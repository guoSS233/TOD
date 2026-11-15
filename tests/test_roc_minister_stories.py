"""Runtime coverage for ministerial focus stories and their choice windows."""
import unittest

import test_roc_minister_agenda_runtime as agenda_runtime
from test_roc_allied_parties import ROOT, named_event, one, read_script


class MinisterStoriesRuntime(unittest.TestCase):
    def setUp(self):
        self.agenda = agenda_runtime.MinisterAgendaRuntime()

    def story_options(self, event_id):
        path = ROOT / 'events/ROC_ma_story.txt'
        self.assertTrue(path.exists(), 'story events are not defined')
        if not hasattr(type(self), '_story_events'):
            type(self)._story_events = {
                one(event, 'id'): event for key, event in read_script(str(path))
                if key == 'country_event'
            }
        event = type(self)._story_events[f'ROC_ma_story.{event_id}']
        return {one(option, 'name'): option for key, option in event if key == 'option'}

    def story_state(self, event_id):
        ministers = ('YuShude', 'YanYangchu', 'RuanXiaoxian', 'ChenZanxian', 'XiaoZheng')
        minister, stage = divmod(event_id, 100)
        state = self.agenda.state(ministers[minister - 1])
        self.agenda.credit(state, stage * 180)
        return state

    @staticmethod
    def snapshot(state):
        return (dict(state.vars), set(state.flags), dict(state.flag_days),
                set(state.ideas), set(state.focuses), dict(state.missions),
                list(state.events), state.pp, state.stability, state.axis)

    def test_first_new_milestone_queues_its_own_story_once(self):
        state = self.agenda.state()
        self.agenda.credit(state, 179)
        self.assertNotIn('ROC_ma_story.101', state.events)
        self.agenda.credit(state, 1)
        self.assertEqual(state.events.count('ROC_ma_story.101'), 1)
        self.assertEqual(state.vars['ROC_ma_yu_stage'], 2)
        state.effect('ROC_ma_timeout')
        state.effect('ROC_ma_daily')
        self.assertEqual(state.events.count('ROC_ma_story.101'), 1)

    def test_story_events_are_delayed_until_after_the_new_stage_is_saved(self):
        def walk(entries):
            for key, value in entries:
                yield key, value
                if isinstance(value, list):
                    yield from walk(value)

        script = read_script('common/scripted_effects/ROC_scripted_effects.txt')
        calls = [value for key, value in walk(script)
                 if key == 'country_event' and one(value, 'id').startswith('ROC_ma_story.')]
        self.assertEqual(len(calls), 30)
        self.assertEqual(len({one(call, 'id') for call in calls}), 30)
        self.assertTrue(all(one(call, 'hours') == '1' for call in calls))

    def test_all_ministers_queue_six_stories_at_their_own_milestones(self):
        ministers = (('YuShude', 'yu'), ('YanYangchu', 'yan'),
                     ('RuanXiaoxian', 'ruan'), ('ChenZanxian', 'chen'),
                     ('XiaoZheng', 'xiao'))
        suffixes = ('1', 'step2', '2', 'step4', '3', 'step6')
        for minister_id, (minister, slug) in enumerate(ministers, 1):
            with self.subTest(minister=minister):
                state = self.agenda.state(minister)
                expected = []
                for stage, suffix in enumerate(suffixes, 1):
                    self.agenda.credit(state, 179)
                    self.assertNotIn(f'ROC_ma_{slug}_{suffix}', state.focuses)
                    self.agenda.credit(state, 1)
                    expected.append(f'ROC_ma_story.{minister_id * 100 + stage}')
                    stories = [event for event in state.events if event.startswith('ROC_ma_story.')]
                    self.assertEqual(stories, expected)
                    self.assertIn(f'ROC_ma_{slug}_{suffix}', state.focuses)
                self.assertEqual(state.vars['ROC_ce_actual'], 115)
                self.agenda.credit(state, 90)
                self.assertEqual([event for event in state.events
                                  if event.startswith('ROC_ma_story.')], expected)

    def test_completed_focus_missing_reward_flag_never_replays_a_story(self):
        state = self.agenda.state()
        state.focuses.add('ROC_ma_yu_1')
        self.agenda.credit(state, 180)
        self.assertEqual(state.vars['ROC_ce_actual'], 20)
        self.assertNotIn('ROC_ma_story.101', state.events)

    def test_focus_tree_rebuild_with_reward_flag_never_replays_a_story(self):
        state = self.agenda.state()
        self.agenda.credit(state, 180)
        state.events.clear()
        state.focuses.discard('ROC_ma_yu_1')
        state.effect('ROC_ce_refresh')
        self.assertIn('ROC_ma_yu_1', state.focuses)
        self.assertEqual(state.vars['ROC_ce_actual'], 20)
        self.assertNotIn('ROC_ma_story.101', state.events)

    def test_old_three_and_five_stage_routes_only_show_the_new_sixth_story(self):
        for old_version in (3, 5):
            with self.subTest(old_version=old_version):
                state = self.agenda.state()
                state.flags.discard('ROC_ma_six_stage_migrated')
                if old_version == 3:
                    state.flags.discard('ROC_ma_five_stage_migrated')
                old_routine = 4 if old_version == 3 else 6
                state.vars.update(ROC_ma_stage=old_routine, ROC_ma_yu_stage=old_routine,
                                  ROC_ma_yu_days=41)
                state.missions['ROC_ma_current_action'] = 41
                state.effect('ROC_ma_sync')
                self.assertFalse(any(event.startswith('ROC_ma_story.') for event in state.events))
                state.tick()
                self.agenda.credit(state, 180)
                self.assertEqual([event for event in state.events
                                  if event.startswith('ROC_ma_story.')], ['ROC_ma_story.106'])

    def test_third_story_keeps_the_existing_intervention_window(self):
        state = self.agenda.state()
        self.agenda.credit(state, 540)
        self.assertIn('ROC_ma_story.103', state.events)
        self.assertIn('ROC_minister_agenda.12', state.events)
        self.assertIn('ROC_ma_story_pending', state.flags)
        self.assertIn('ROC_ma_yu_2_pending', state.flags)
        existing = named_event(read_script('events/ROC_minister_agenda.txt'),
                               'ROC_minister_agenda.12')
        self.assertTrue(state.passes(one(existing, 'trigger')))

    def test_simultaneous_term_expiry_queues_old_ministers_story_once(self):
        for first in ('ROC_ma_timeout', 'ROC_econ_term_expired'):
            for remove_first in (False, True):
                with self.subTest(first=first, remove_first=remove_first):
                    state = self.agenda.state()
                    state.vars.update(ROC_ma_stage=6, ROC_ma_yu_stage=6,
                                      ROC_ma_days_remaining=1, ROC_ma_yu_days=1)
                    state.missions.update(ROC_ma_current_action=0,
                                          ROC_decision_bop_jingjidahui=0)
                    if remove_first:
                        state.missions.pop('ROC_ma_current_action')
                    second = ('ROC_econ_term_expired' if first == 'ROC_ma_timeout'
                              else 'ROC_ma_timeout')
                    state.effect(first)
                    state.effect(second)
                    state.effect('ROC_ma_timeout')
                    self.assertEqual(state.events.count('ROC_ma_story.106'), 1)
                    self.assertNotIn('ROC_ma_story_pending', state.flags)

    def test_crossing_multiple_stages_leaves_only_the_latest_window(self):
        state = self.agenda.state()
        self.agenda.credit(state, 370)
        self.assertEqual([event for event in state.events
                          if event.startswith('ROC_ma_story.')],
                         ['ROC_ma_story.101', 'ROC_ma_story.102'])
        self.assertEqual(state.vars['ROC_ma_story_active_id'], 102)
        self.assertEqual(state.vars['ROC_ma_story_next_stage'], 3)
        self.assertIn('ROC_ma_story_pending', state.flags)

    def test_story_window_is_cleared_by_resignation_or_term_expiry(self):
        for end in ('ROC_econ_remove_ministers', 'ROC_econ_term_expired'):
            with self.subTest(end=end):
                state = self.agenda.state()
                self.agenda.credit(state, 180)
                self.assertIn('ROC_ma_story_pending', state.flags)
                state.effect(end)
                self.assertNotIn('ROC_ma_story_pending', state.flags)

    def test_direct_new_term_and_profile_change_invalidate_old_window(self):
        for change in ('start_term', 'profile'):
            with self.subTest(change=change):
                state = self.agenda.state()
                self.agenda.credit(state, 180)
                if change == 'start_term':
                    state.missions.pop('ROC_decision_bop_jingjidahui')
                    state.effect('ROC_econ_start_term')
                else:
                    state.ideas.discard('ROC_idea_YuShude')
                    state.ideas.add('ROC_idea_XiaoZheng')
                    state.effect('ROC_ce_refresh')
                self.assertNotIn('ROC_ma_story_pending', state.flags)

    def test_policy_selection_does_not_close_an_unrelated_story(self):
        state = self.agenda.state()
        self.agenda.credit(state, 180)
        state.vars['ROC_ma_policy_owner'] = 0
        state.effect('ROC_ma_select_yu_policy')
        self.assertIn('ROC_ma_story_pending', state.flags)
        self.assertTrue(state.passes(state.effects['ROC_ma_story_is_valid']))

    def test_routine_execution_invalidates_the_last_focus_window(self):
        state = self.agenda.state()
        self.agenda.credit(state, 1080)
        self.assertEqual(state.vars['ROC_ma_story_active_id'], 106)
        self.assertIn('ROC_ma_story_pending', state.flags)
        self.agenda.credit(state, 90)
        self.assertNotIn('ROC_ma_story_pending', state.flags)

    def test_window_rejects_clocks_due_before_their_native_callback(self):
        for mission in ('ROC_ma_current_action', 'ROC_decision_bop_jingjidahui'):
            with self.subTest(mission=mission):
                state = self.agenda.state()
                self.agenda.credit(state, 180)
                self.assertTrue('ROC_ma_story_is_valid' in state.effects,
                                'story validity trigger is not loaded')
                trigger = state.effects['ROC_ma_story_is_valid']
                self.assertTrue(state.passes(trigger))
                state.missions[mission] = 0
                self.assertFalse(state.passes(trigger))

    def test_window_allows_the_new_stage_during_the_rearm_barrier(self):
        state = self.agenda.state()
        state.missions['ROC_ma_current_action'] = 0
        state.effect('ROC_ma_timeout')
        self.assertTrue('ROC_ma_story_is_valid' in state.effects,
                        'story validity trigger is not loaded')
        trigger = state.effects['ROC_ma_story_is_valid']
        self.assertTrue(state.passes(trigger))
        state.flags.add('ROC_ma_clock_armed')
        self.assertFalse(state.passes(trigger))

    def test_free_default_is_available_and_spends_no_political_power(self):
        state = self.agenda.state()
        self.agenda.credit(state, 180)
        options = self.story_options(101)
        option = options['ROC_ma_story.101.a']
        state.pp = 0
        state.vars.update(ROC_ma_left_favor=0, ROC_ma_center_favor=0, ROC_ma_right_favor=0)
        self.assertTrue(state.passes(one(option, 'trigger')))
        state.run(one(option, 'hidden_effect'))
        self.assertEqual(state.pp, 0)
        self.assertNotIn('ROC_ma_story_pending', state.flags)

    def test_ai_may_choose_any_affordable_story_option(self):
        for minister in range(1, 6):
            for stage in range(1, 7):
                event_id = minister * 100 + stage
                options = self.story_options(event_id)
                for name in ('a', 'b', 'c'):
                    option = options[f'ROC_ma_story.{event_id}.{name}']
                    self.assertEqual(one(one(option, 'ai_chance'), 'factor'), '1',
                                     (event_id, name))

    def test_every_story_has_a_free_default_and_a_resource_costing_alternative(self):
        for minister in range(1, 6):
            for stage in range(1, 7):
                event_id = minister * 100 + stage
                with self.subTest(event=event_id):
                    state = self.story_state(event_id)
                    options = self.story_options(event_id)
                    self.assertEqual(set(options), {
                        f'ROC_ma_story.{event_id}.a', f'ROC_ma_story.{event_id}.b',
                        f'ROC_ma_story.{event_id}.c', 'ROC_ma_story_archive'})
                    state.pp = 0
                    state.vars.update(ROC_ma_left_favor=0, ROC_ma_center_favor=0,
                                      ROC_ma_right_favor=0)
                    default = options[f'ROC_ma_story.{event_id}.a']
                    self.assertTrue(state.passes(one(default, 'trigger')))
                    self.assertFalse(state.passes(one(options['ROC_ma_story_archive'], 'trigger')))
                    alternatives = [options[f'ROC_ma_story.{event_id}.{name}'] for name in ('b', 'c')]
                    self.assertTrue(any(not state.passes(one(option, 'trigger'))
                                        for option in alternatives))
                    state.run(one(default, 'hidden_effect'))
                    self.assertEqual(state.pp, 0)
                    self.assertNotIn('ROC_ma_story_pending', state.flags)
                    before = self.snapshot(state)
                    state.run(one(default, 'hidden_effect'))
                    self.assertEqual(self.snapshot(state), before)

    def test_all_priced_choices_recheck_each_resource_before_spending(self):
        for minister in range(1, 6):
            for stage in range(1, 7):
                event_id = minister * 100 + stage
                options = self.story_options(event_id)
                for name in ('b', 'c'):
                    with self.subTest(event=event_id, choice=name):
                        state = self.story_state(event_id)
                        option = options[f'ROC_ma_story.{event_id}.{name}']
                        trigger = one(option, 'trigger')
                        requirements = []
                        for key, value in trigger:
                            if key == 'NOT' and any(k == 'has_political_power' for k, _ in value):
                                requirements.append(('pp', float(one(value, 'has_political_power').value)))
                            elif key == 'check_variable':
                                fields = dict(value)
                                var = fields.get('var', '')
                                if var.startswith('ROC_ma_') and var.endswith('_favor'):
                                    requirements.append((var, float(fields['value'])))
                        if not requirements:
                            state.pp = 0
                            for side in ('left', 'center', 'right'):
                                state.vars[f'ROC_ma_{side}_favor'] = 0
                            self.assertTrue(state.passes(trigger))
                        for resource, cost in requirements:
                            state.pp = 200
                            for side in ('left', 'center', 'right'):
                                state.vars[f'ROC_ma_{side}_favor'] = 50
                            if resource == 'pp':
                                state.pp = cost - 1
                            else:
                                state.vars[resource] = cost - 1
                            self.assertFalse(state.passes(trigger))
                            before = self.snapshot(state)
                            state.run(one(option, 'hidden_effect'))
                            self.assertEqual(self.snapshot(state), before)
                            if resource == 'pp':
                                state.pp = cost
                            else:
                                state.vars[resource] = cost
                            self.assertTrue(state.passes(trigger))
                        state.run(one(option, 'hidden_effect'))
                        before = self.snapshot(state)
                        state.run(one(option, 'hidden_effect'))
                        self.assertEqual(self.snapshot(state), before)

    def test_every_story_archives_inertly_after_expiry_or_replacement(self):
        ministers = ('YuShude', 'YanYangchu', 'RuanXiaoxian', 'ChenZanxian', 'XiaoZheng')
        for minister in range(1, 6):
            for stage in range(1, 7):
                event_id = minister * 100 + stage
                options = self.story_options(event_id)
                negated = one(one(options['ROC_ma_story_archive'], 'trigger'), 'NOT')
                self.assertEqual([key for key, _ in negated], ['AND'], event_id)
                conjunction = one(negated, 'AND')
                self.assertIn(('ROC_ma_story_is_valid', 'yes'), conjunction)
                self.assertEqual(dict(one(conjunction, 'check_variable')), {
                    'var': 'ROC_ma_story_active_id', 'value': str(event_id), 'compare': 'equals'})
                for reason in ('expiry', 'replacement'):
                    with self.subTest(event=event_id, reason=reason):
                        state = self.story_state(event_id)
                        if reason == 'expiry':
                            state.flags.discard('ROC_ma_story_pending')
                            state.flag_days.pop('ROC_ma_story_pending', None)
                        else:
                            state.effect('ROC_econ_remove_ministers')
                            state.ideas.add('ROC_idea_' + ministers[minister % 5])
                            state.effect('ROC_econ_refresh_minister')
                        self.assertTrue(state.passes(one(options['ROC_ma_story_archive'], 'trigger')))
                        for name in ('a', 'b', 'c'):
                            option = options[f'ROC_ma_story.{event_id}.{name}']
                            self.assertFalse(state.passes(one(option, 'trigger')))
                            before = self.snapshot(state)
                            state.run(one(option, 'hidden_effect'))
                            self.assertEqual(self.snapshot(state), before)

    def test_sample_choices_apply_the_frozen_costs_and_consequences(self):
        expected = {
            'a': (0, 0, 4, 0, 0, 3, 14),
            'b': (-10, 6, 0, -4, 0, 0, -14),
            'c': (0, -4, -5, -3, 3, 0, 0),
        }
        for name, changes in expected.items():
            with self.subTest(choice=name):
                state = self.story_state(101)
                state.vars['ROC_ce_pressure'] = 50
                before = (state.pp, state.vars['ROC_ma_left_favor'],
                          state.vars['ROC_ma_center_favor'], state.vars['ROC_ma_right_favor'],
                          state.vars['ROC_ce_actual'], state.vars['ROC_ce_pressure'],
                          state.vars['ROC_ma_days_remaining'])
                option = self.story_options(101)[f'ROC_ma_story.101.{name}']
                self.assertTrue(state.passes(one(option, 'trigger')))
                state.run(one(option, 'hidden_effect'))
                after = (state.pp, state.vars['ROC_ma_left_favor'],
                         state.vars['ROC_ma_center_favor'], state.vars['ROC_ma_right_favor'],
                         state.vars['ROC_ce_actual'], state.vars['ROC_ce_pressure'],
                         state.vars['ROC_ma_days_remaining'])
                self.assertEqual(tuple(y - x for x, y in zip(before, after)), changes)

    def test_stale_story_options_are_inert_and_archive_is_available(self):
        options = self.story_options(101)
        for stale in ('next_stage', 'expiry', 'same_minister', 'term', 'agenda_due', 'term_due'):
            with self.subTest(stale=stale):
                state = self.agenda.state()
                self.agenda.credit(state, 180)
                if stale == 'next_stage':
                    self.agenda.credit(state, 180)
                elif stale == 'expiry':
                    self.agenda.native_days(state, 15)
                elif stale == 'same_minister':
                    state.effect('ROC_econ_remove_ministers')
                    state.ideas.add('ROC_idea_YuShude')
                    state.effect('ROC_econ_refresh_minister')
                elif stale == 'term':
                    state.effect('ROC_econ_term_expired')
                    state.missions.pop('ROC_decision_bop_jingjidahui', None)
                    state.effect('ROC_econ_start_term')
                elif stale == 'agenda_due':
                    state.missions['ROC_ma_current_action'] = 0
                elif stale == 'term_due':
                    state.missions['ROC_decision_bop_jingjidahui'] = 0
                self.assertTrue(state.passes(one(options['ROC_ma_story_archive'], 'trigger')))
                for suffix in ('a', 'b', 'c'):
                    option = options[f'ROC_ma_story.101.{suffix}']
                    self.assertFalse(state.passes(one(option, 'trigger')))
                    before = self.snapshot(state)
                    state.run(one(option, 'hidden_effect'))
                    self.assertEqual(self.snapshot(state), before, (stale, suffix))


if __name__ == '__main__':
    unittest.main()
