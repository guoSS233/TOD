"""Execute shipped minister agendas; native engine integration is not simulated QA."""
import unittest

from test_roc_central_economy import CentralState
from test_roc_allied_parties import economic_decisions, read_script, one, named_event, read_event


class MinisterAgendaRuntime(unittest.TestCase):
    def state(self, minister='YuShude'):
        s = CentralState()
        s.ideas.add('ROC_idea_' + minister)
        s.initialize()
        return s

    def credit(self, s, days):
        s.vars['ROC_ma_day_credit'] = days
        s.effect('ROC_ma_advance_days')

    def native_days(self, s, days, remove_before_callback=False):
        definitions = {}
        from test_roc_allied_parties import ROOT
        for path in (ROOT/'common/decisions').glob('ROC*.txt'):
            for _, category in read_script(str(path)):
                if isinstance(category,list):
                    definitions.update((k,v) for k,v in category if isinstance(v,list))
        for _ in range(days):
            # Timed flags that existed before today's callbacks expire first.
            for flag in list(s.flag_days):
                s.flag_days[flag]-=1
                if s.flag_days[flag]<=0:
                    s.flag_days.pop(flag);s.flags.discard(flag)
            # Clock expiration is simultaneous; callbacks can then run in either order.
            for mission in list(s.missions):s.missions[mission]-=1
            due=[mission for mission,remaining in s.missions.items() if remaining<=0]
            for mission in due:
                if remove_before_callback:s.missions.pop(mission,None)
                s.run(one(definitions[mission],'timeout_effect'))
                s.missions.pop(mission,None)
            s.effect('ROC_ce_daily')

    def choose_roc_event(self, s, event_id, suffix):
        event = read_event(f'ROC_pingheng.{event_id}')
        s.run(one(event, 'immediate'))
        option = next(
            value for key, value in event
            if key == 'option' and one(value, 'name').endswith('.' + suffix)
        )
        triggers = [value for key, value in option if key == 'trigger']
        if triggers:
            self.assertTrue(s.passes(triggers[0]), f'{event_id}.{suffix} should be available')
        s.run([(key, value) for key, value in option if key not in ('name', 'trigger')])
        return event, option

    def test_temporary_starting_idea_waits_for_formal_minister_selection(self):
        s = CentralState()
        s.ideas.add('ROC_idea_YuShude')
        s.missions.pop('ROC_decision_bop_jingjidahui')
        s.effect('ROC_ce_refresh')
        self.assertEqual(s.vars['ROC_ce_minister_profile_id'], 1)
        self.assertNotIn('ROC_ma_minister_selection', s.focuses)
        self.assertNotIn('ROC_ma_yu_appointed', s.focuses)

        self.choose_roc_event(s, 9997, 'a')
        self.assertIn('ROC_ma_minister_selection', s.focuses)
        self.assertIn('ROC_ma_yu_appointed', s.focuses)
        self.assertFalse(any(focus in s.focuses for focus in (
            'ROC_ma_yu_1', 'ROC_ma_yu_2', 'ROC_ma_yu_3',
            'ROC_ma_yan_appointed', 'ROC_ma_ruan_appointed',
            'ROC_ma_chen_appointed', 'ROC_ma_xiao_appointed',
        )))

    def test_formal_appointments_complete_only_the_selected_entry(self):
        for minister, slug, option in (
            ('YuShude', 'yu', 'a'), ('YanYangchu', 'yan', 'b'),
            ('RuanXiaoxian', 'ruan', 'e'), ('ChenZanxian', 'chen', 'c'),
            ('XiaoZheng', 'xiao', 'f'),
        ):
            with self.subTest(minister=minister):
                s = CentralState()
                s.ideas.add('ROC_idea_YuShude')
                s.missions.pop('ROC_decision_bop_jingjidahui')
                s.effect('ROC_ce_refresh')
                self.assertNotIn('ROC_ma_minister_selection', s.focuses)
                self.choose_roc_event(s, 9997, option)
                self.assertIn('ROC_idea_' + minister, s.ideas)
                self.assertIn('ROC_ma_minister_selection', s.focuses)
                self.assertIn(f'ROC_ma_{slug}_appointed', s.focuses)
                self.assertFalse(any(
                    f'ROC_ma_{other}_appointed' in s.focuses
                    for other in ('yu', 'yan', 'ruan', 'chen', 'xiao') if other != slug
                ))
                self.assertNotIn(f'ROC_ma_{slug}_1', s.focuses)

    def test_reappointment_refresh_and_tree_switch_restore_only_historic_entries(self):
        s = CentralState()
        s.ideas.add('ROC_idea_YuShude')
        s.missions.pop('ROC_decision_bop_jingjidahui')
        s.effect('ROC_ce_refresh')
        self.choose_roc_event(s, 9997, 'a')
        s.missions.pop('ROC_decision_bop_jingjidahui')
        self.choose_roc_event(s, 9999, 'b')
        self.assertIn('ROC_idea_YanYangchu', s.ideas)
        self.assertIn('ROC_ma_yu_appointed', s.focuses)
        self.assertIn('ROC_ma_yan_appointed', s.focuses)
        self.assertFalse(any(
            f'ROC_ma_{slug}_appointed' in s.focuses for slug in ('ruan', 'chen', 'xiao')
        ))

        state_before = (
            s.vars['ROC_ce_actual'], s.vars['ROC_ma_yan_stage'], s.vars['ROC_ma_yan_days'],
            s.missions['ROC_ma_current_action'], s.missions['ROC_decision_bop_jingjidahui'],
            tuple(s.vars[f'ROC_ma_{side}_favor'] for side in ('left', 'center', 'right')),
        )
        for _ in range(3):
            s.effect('ROC_econ_refresh_minister')
        self.assertEqual(state_before, (
            s.vars['ROC_ce_actual'], s.vars['ROC_ma_yan_stage'], s.vars['ROC_ma_yan_days'],
            s.missions['ROC_ma_current_action'], s.missions['ROC_decision_bop_jingjidahui'],
            tuple(s.vars[f'ROC_ma_{side}_favor'] for side in ('left', 'center', 'right')),
        ))

        s.focuses.difference_update({
            'ROC_ma_minister_selection', 'ROC_ma_yu_appointed', 'ROC_ma_yan_appointed',
        })
        s.flags.update({'ROC_postwar_active', 'ROC_ce_survey_done'})
        s.run([('load_focus_tree', [('tree', 'ROC_datong_postwar'), ('keep_completed', 'yes')])])
        s.effect('ROC_ce_refresh')
        self.assertIn('ROC_ma_minister_selection', s.focuses)
        self.assertIn('ROC_ma_yu_appointed', s.focuses)
        self.assertIn('ROC_ma_yan_appointed', s.focuses)
        self.assertFalse(any(
            f'ROC_ma_{slug}_appointed' in s.focuses for slug in ('ruan', 'chen', 'xiao')
        ))
        self.assertNotIn('ROC_ma_yan_1', s.focuses)

    def test_same_day_term_and_agenda_expiration_settles_old_term_in_both_orders(self):
        for order in [('ROC_econ_term_expired','ROC_ma_timeout'),
                      ('ROC_ma_timeout','ROC_econ_term_expired')]:
            s=self.state();s.missions.update(ROC_decision_bop_jingjidahui=0,ROC_ma_current_action=0)
            for effect in order:s.effect(effect)
            self.assertEqual(s.vars['ROC_ce_actual'],20,order)
            self.assertEqual(s.vars['ROC_ma_yu_stage'],2,order)
            s.missions.pop('ROC_ma_current_action',None);s.missions.pop('ROC_decision_bop_jingjidahui',None)
            s.effect('ROC_ma_daily');s.effect('ROC_ma_timeout')
            self.assertEqual(s.vars['ROC_ce_actual'],20,order)
            s.effect('ROC_econ_start_term')
            self.assertEqual(s.vars['ROC_ce_actual'],0,order)
            self.assertNotIn('ROC_ma_current_action',s.missions,order)
            s.effect('ROC_ma_timeout');s.effect('ROC_ma_daily')
            self.assertEqual(s.vars['ROC_ce_actual'],0,order)
            self.assertEqual(s.vars['ROC_ma_yu_stage'],2,order)
            s.tick()
            self.assertEqual(s.missions['ROC_ma_current_action'],180,order)

    def test_same_day_replacement_and_stale_timeout_never_complete_successor(self):
        for callback_first in (False,True):
            s=self.state();s.missions['ROC_ma_current_action']=0
            if callback_first:s.effect('ROC_ma_timeout')
            s.effect('ROC_econ_remove_ministers');s.ideas.add('ROC_idea_XiaoZheng')
            s.effect('ROC_econ_refresh_minister');s.effect('ROC_ma_timeout')
            self.assertEqual(s.vars['ROC_ce_actual'],20)
            self.assertEqual(s.vars['ROC_ma_yu_stage'],2)
            self.assertEqual(s.vars['ROC_ma_xiao_stage'],1)
            self.assertNotIn('ROC_ma_current_action',s.missions)
            s.tick();self.assertEqual(s.missions['ROC_ma_current_action'],180)
            s.effect('ROC_ma_timeout');s.effect('ROC_ma_daily')
            self.assertEqual(s.missions['ROC_ma_current_action'],180)
            self.assertEqual(s.vars['ROC_ce_actual'],20)
            self.assertNotIn('ROC_ma_xiao_1',s.focuses)

    def test_engine_removal_before_timeout_callback_still_settles_last_saved_day(self):
        s=self.state();s.missions['ROC_ma_current_action']=1;s.effect('ROC_ce_refresh')
        self.native_days(s,1,remove_before_callback=True)
        self.assertEqual(s.vars['ROC_ma_yu_stage'],2)
        self.assertEqual(s.vars['ROC_ce_actual'],20)
        self.assertNotIn('ROC_ma_current_action',s.missions)
        self.native_days(s,1)
        self.assertEqual(s.missions['ROC_ma_current_action'],180)

    def test_both_engine_removal_orders_and_callback_orders_settle_same_old_term(self):
        for remove_first in (False,True):
            for agenda_first in (False,True):
                s=self.state();s.missions['ROC_ma_current_action']=1
                s.effect('ROC_ce_refresh')
                s.missions['ROC_decision_bop_jingjidahui']=1
                if agenda_first:
                    s.missions=dict(reversed(list(s.missions.items())))
                self.native_days(s,1,remove_before_callback=remove_first)
                self.assertEqual(s.vars['ROC_ce_actual'],20,(remove_first,agenda_first))
                self.assertEqual(s.vars['ROC_ma_yu_stage'],2,(remove_first,agenda_first))
                s.effect('ROC_econ_start_term');s.effect('ROC_ma_timeout')
                self.assertEqual(s.vars['ROC_ce_actual'],0)
                self.assertNotIn('ROC_ma_current_action',s.missions)
                s.tick();self.assertEqual(s.missions['ROC_ma_current_action'],180)

    def test_one_day_credit_remainder_is_rearmed_instead_of_falsely_expired(self):
        s=self.state();s.missions['ROC_ma_current_action']=0;self.credit(s,179)
        self.assertEqual(s.vars['ROC_ma_yu_days'],1)
        s.tick();self.assertEqual(s.missions['ROC_ma_current_action'],1)
        self.assertEqual(s.vars['ROC_ma_yu_stage'],2)
        self.native_days(s,1)
        self.assertEqual(s.vars['ROC_ma_yu_stage'],3)
        self.assertEqual(s.vars['ROC_ce_actual'],25)

    def test_no_click_route_advances_by_actual_native_mission_durations(self):
        s=self.state();s.missions['ROC_decision_bop_jingjidahui']=1095
        action=one(economic_decisions(),'ROC_ma_current_action')
        self.assertEqual(one(action,'cancel_if_not_visible'),'no')
        for index,(days,key) in enumerate([(180,'1'),(180,'step2'),(180,'2'),(180,'step4'),(180,'3'),(180,'step6')]):
            self.native_days(s,days-1)
            self.assertNotIn('ROC_ma_yu_'+key,s.focuses)
            self.native_days(s,1)
            self.assertIn('ROC_ma_yu_'+key,s.focuses)
            self.assertNotIn('ROC_ma_current_action',s.missions)
            if key=='2':
                event=named_event(read_script('events/ROC_minister_agenda.txt'),'ROC_minister_agenda.12')
                self.assertTrue(s.passes(one(event,'trigger')))
            if index<5:self.native_days(s,1)
        self.assertEqual(s.vars['ROC_ma_stage'],7)
        self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'],10)
        s.missions['ROC_decision_bop_jingjidahui']=100
        self.native_days(s,1)
        self.assertIn('ROC_ma_current_action',s.missions)
        self.assertFalse(s.passes(one(action,'visible')))
        before=s.vars['ROC_ce_actual'];self.native_days(s,90)
        self.assertEqual(s.vars['ROC_ce_actual'],before+10)

    def test_timeout_effect_tooltips_hide_internals_without_changing_callbacks(self):
        agenda = dict(economic_decisions())
        term_decisions = dict(economic_decisions())
        cases = (
            (agenda['ROC_ma_current_action'], 'ROC_ma_current_action_complete_tt', 'ROC_ma_timeout'),
            (term_decisions['ROC_decision_bop_jingjidahui'], 'ROC_ma_term_complete_tt', 'ROC_econ_term_expired'),
        )
        for decision, tooltip, callback in cases:
            timeout = one(decision, 'timeout_effect')
            self.assertEqual([key for key, _ in timeout], ['custom_effect_tooltip', 'hidden_effect'])
            self.assertEqual(one(timeout, 'custom_effect_tooltip'), tooltip)
            self.assertEqual(one(one(timeout, 'hidden_effect'), callback), 'yes')

        def snapshot(state):
            return (
                dict(state.vars), set(state.flags), dict(state.flag_days),
                set(state.ideas), set(state.focuses), dict(state.missions),
                set(state.decisions), list(state.events), state.pp,
                state.stability, state.axis,
            )

        direct = self.state()
        wrapped = self.state()
        direct.missions['ROC_ma_current_action'] = 0
        wrapped.missions['ROC_ma_current_action'] = 0
        direct.effect('ROC_ma_timeout')
        wrapped.run(one(agenda['ROC_ma_current_action'], 'timeout_effect'))
        self.assertEqual(snapshot(wrapped), snapshot(direct))

        direct = self.state()
        wrapped = self.state()
        direct.flags.add('ROC_econ_term_active')
        wrapped.flags.add('ROC_econ_term_active')
        direct.missions['ROC_decision_bop_jingjidahui'] = 0
        wrapped.missions['ROC_decision_bop_jingjidahui'] = 0
        direct.effect('ROC_econ_term_expired')
        wrapped.run(one(term_decisions['ROC_decision_bop_jingjidahui'], 'timeout_effect'))
        self.assertEqual(snapshot(wrapped), snapshot(direct))

    def test_crossing_stage_decision_opens_valid_event_after_advancement(self):
        s=self.state();s.missions['ROC_ma_current_action']=5
        s.focuses.add('ROC_ma_yu_1')
        decisions=economic_decisions()
        s.run(one(one(decisions,'ROC_ma_yu_1_decision'),'complete_effect'))
        event=named_event(read_script('events/ROC_minister_agenda.txt'),'ROC_minister_agenda.11')
        self.assertEqual(s.vars['ROC_ma_stage'],2)
        self.assertTrue(s.passes(one(event,'trigger')))

    def test_project_delivery_credit_requires_real_output_and_is_once_only(self):
        s=self.state();s.flags.update({'ROC_ce_industry_unlocked','ROC_ce_program_done'})
        s.effect('ROC_ce_start_industry');s.vars['ROC_ce_project_progress']=100
        s.effect('ROC_ce_deliver')
        self.assertEqual(s.vars['ROC_ma_days_remaining'],150)
        s.effect('ROC_ce_deliver')
        self.assertEqual(s.vars['ROC_ma_days_remaining'],150)

    def test_delay_spends_favor_and_never_political_power_or_overdraws(self):
        for side,mission in [('left','zuopai'),('right','youpai')]:
            for favor,want_days,want_favor in [(14,50,14),(15,71,0)]:
                s=self.state();s.focuses.add('gemingweiyuanhui')
                s.missions['ROC_decision_'+mission]=50
                s.vars['ROC_ma_'+side+'_favor']=favor;s.effect('ROC_ce_refresh');s.pp=0
                s.effect('ROC_ma_delay_committee_'+side)
                self.assertEqual(s.missions['ROC_decision_'+mission],want_days)
                self.assertEqual(s.vars['ROC_ma_'+side+'_favor'],want_favor)
                s.effect('ROC_ma_delay_committee_'+side)
                self.assertEqual(s.missions['ROC_decision_'+mission],want_days)
                self.assertEqual(s.pp,0)

    def test_old_completed_shared_focus_receives_missing_bookkeeping_once(self):
        s=self.state();s.focuses.add('ROC_ma_yu_1');self.credit(s,180)
        self.assertEqual(s.vars['ROC_ce_actual'],20)
        s.effect('ROC_ma_reward_yu_1');self.assertEqual(s.vars['ROC_ce_actual'],20)

    def test_committee_callback_after_race_ending_cannot_reuse_completion(self):
        s=self.state();s.focuses.add('gemingweiyuanhui')
        s.vars['ROC_committee_left_agenda']=1
        s.effect('ROC_committee_complete_left')
        self.assertEqual(s.vars['ROC_ma_days_remaining'],187)
        s.focuses.add('jingchenghezuo')
        s.effect('ROC_committee_complete_left');s.effect('ROC_committee_complete_center')
        self.assertEqual(s.vars['ROC_ma_days_remaining'],187)

    def test_postwar_tree_switch_preserves_shared_completion_clock_and_rewards(self):
        s=self.state();self.credit(s,190)
        s.run([('load_focus_tree',[('tree','ROC_datong_postwar'),('keep_completed','yes')])])
        s.flags.add('ROC_postwar_active');s.flags.add('ROC_ce_survey_done')
        s.effect('ROC_ce_refresh')
        self.assertIn('ROC_ma_yu_1',s.focuses)
        self.assertEqual(s.vars['ROC_ma_days_remaining'],170)
        self.assertEqual(s.vars['ROC_ce_actual'],20)

    def test_native_auto_activation_rejects_uninitialized_zero_day_clock(self):
        definitions=economic_decisions()
        activation=one(one(definitions,'ROC_ma_current_action'),'activation')
        s=CentralState();s.ideas.add('ROC_idea_YuShude')
        s.vars['ROC_ce_minister_profile_id']=1
        self.assertFalse(s.passes(activation))
        s.initialize();self.assertTrue(s.passes(activation))

    def test_preexisting_approved_legacy_work_can_finish_but_new_entry_is_hidden(self):
        decisions=economic_decisions()
        block=one(decisions,'ROC_econ_yu_pilot')
        s=self.state();s.focuses.update({'gemingweiyuanhui','qianghuazhengzhituanjie','tuidongnongyehezuoshefazhan'});s.effect('ROC_econ_refresh')
        self.assertFalse(s.passes(one(block,'visible')))
        # Use the actual old bill submission/vote path, whose validity also saves minister identity.
        s.effect('ROC_bill_refresh_candidate');s.effect('ROC_bill_submit_effect')
        s.effect('ROC_bill_prepare_materials');s.focuses.add('qianghuazhengzhituanjie')
        s.effect('ROC_bill_vote')
        self.assertFalse(s.passes(one(block,'visible')))
        self.assertFalse(s.passes(one(block,'available')))

        # A saved paid timer remains visible to its current minister and still settles after a switch.
        s.decisions.add('ROC_econ_yu_pilot')
        self.assertTrue(s.passes(one(block,'visible')))
        self.assertFalse(s.passes(one(block,'available')))
        s.vars['ROC_ce_minister_profile_id']=2
        self.assertFalse(s.passes(one(block,'visible')))
        s.run(one(block,'remove_effect'))
        self.assertIn('ROC_econ_yu_pilot_done',s.flags)

    def test_every_minister_first_reward_has_theme_output_without_changing_favor(self):
        for minister,slug,project,want_progress,want_pp,want_stability,want_direction in [
                ('YuShude','yu',1,22,200,.5,2),
                ('YanYangchu','yan',2,25,200,.5,0),
                ('RuanXiaoxian','ruan',1,10,200,.5,3),
                ('ChenZanxian','chen',1,25,200,.51,3),
                ('XiaoZheng','xiao',2,10,215,.5,-3)]:
            s=self.state(minister);s.vars.update(ROC_ce_project_id=project,ROC_ce_project_progress=10)
            before=tuple(s.vars['ROC_ma_'+side+'_favor'] for side in ('left','center','right'))
            self.credit(s,180)
            self.assertEqual(s.vars['ROC_ce_project_progress'],want_progress)
            self.assertEqual(s.pp,want_pp);self.assertAlmostEqual(s.stability,want_stability)
            self.assertEqual(s.vars['ROC_ma_policy_pending'],want_direction)
            self.assertEqual(tuple(s.vars['ROC_ma_'+side+'_favor'] for side in ('left','center','right')),before)

    def test_native_stage_clock_starts_independently_and_overflow_crosses_stages(self):
        s = self.state()
        self.assertEqual(s.vars.get('ROC_ma_days_remaining'), 180)
        self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'], 700)
        self.credit(s, 370)
        self.assertEqual(s.vars['ROC_ma_stage'], 3)
        self.assertEqual(s.vars['ROC_ma_days_remaining'], 170)
        self.assertEqual(s.vars['ROC_ce_actual'], 25)
        self.assertTrue({'ROC_ma_yu_1', 'ROC_ma_yu_step2'} <= s.focuses)

    def test_progress_renders_the_saved_stage_clock_independently_of_axis_and_term(self):
        s = self.state()
        registration = one(one(read_script('common/scripted_guis/ROC_central_economy.txt'),
                              'scripted_gui'), 'ROC_central_economy_window')
        visible = one(one(registration, 'triggers'), 'ROC_ce_gui_current_action_bar_visible')
        # A save from the previous UI can have a frame but no numerical readout.
        s.vars.pop('ROC_ma_gui_progress_percent')
        s.vars.pop('ROC_ce_policy_needle_x')
        s.missions.update(ROC_ma_current_action=83, ROC_decision_bop_jingjidahui=1012)

        self.assertFalse(s.passes(visible))
        s.effect('ROC_ce_daily')
        self.assertTrue(s.passes(visible))
        self.assertEqual(s.vars['ROC_ma_gui_progress_frame'], 55)  # 97/180 days, 54%.
        self.assertEqual(s.vars['ROC_ma_gui_progress_percent'], 54)
        self.assertEqual(s.vars['ROC_ce_policy_needle_x'], 245)
        self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'], 1012)

        self.native_days(s, 2)
        self.assertEqual(s.vars['ROC_ma_gui_progress_frame'], 56)
        s.vars['ROC_ma_day_delay'] = 18
        s.effect('ROC_ma_delay_days')
        self.assertEqual(s.vars['ROC_ma_gui_progress_frame'], 46)
        self.assertEqual(s.vars['ROC_ma_gui_progress_percent'], 45)
        self.credit(s, 9)
        self.assertEqual(s.vars['ROC_ma_gui_progress_frame'], 51)
        self.assertEqual(s.vars['ROC_ma_gui_progress_percent'], 50)
        s.flags.add('ROC_econ_conference_pending')
        self.assertFalse(s.passes(visible))

    def test_execution_progress_uses_its_own_ninety_day_cycle(self):
        s = self.state()
        self.credit(s, 1080)
        self.assertEqual(s.vars['ROC_ma_gui_progress_frame'], 1)
        self.credit(s, 45)
        self.assertEqual(s.vars['ROC_ma_gui_progress_frame'], 51)
        self.assertEqual(s.vars['ROC_ma_gui_progress_percent'], 50)
        s.vars['ROC_ma_day_delay'] = 100
        s.effect('ROC_ma_delay_days')
        self.assertEqual(s.vars['ROC_ma_gui_progress_frame'], 1)
        self.assertEqual(s.vars['ROC_ma_gui_progress_percent'], 0)

    def test_stage_percentage_and_sprite_match_for_every_remaining_day(self):
        s = self.state()
        for stage, duration in ((1, 180), (7, 90)):
            s.vars['ROC_ma_stage'] = stage
            for remaining in range(duration + 2):
                s.vars['ROC_ma_days_remaining'] = remaining
                s.effect('ROC_ma_refresh_gui_progress')
                percent = round(100 * max(0, duration - remaining) / duration)
                self.assertEqual(s.vars['ROC_ma_gui_progress_percent'], percent)
                self.assertEqual(s.vars['ROC_ma_gui_progress_frame'], percent + 1)

    def test_completed_route_repeats_execution_without_repeating_focus_rewards(self):
        s = self.state()
        self.credit(s, 1080)
        self.assertEqual(s.vars['ROC_ma_stage'], 7)
        self.assertEqual(s.vars['ROC_ma_days_remaining'], 90)
        self.assertEqual(s.vars['ROC_ce_actual'], 115)
        self.credit(s, 180)
        self.assertEqual(s.vars['ROC_ce_actual'], 135)
        s.effect('ROC_ma_reward_yu_1')
        self.assertEqual(s.vars['ROC_ce_actual'], 135)

    def test_switch_and_conference_pause_preserve_personal_clock_and_term(self):
        s = self.state()
        s.missions['ROC_ma_current_action'] = 123
        s.effect('ROC_econ_remove_ministers')
        s.ideas.add('ROC_idea_XiaoZheng')
        s.effect('ROC_econ_refresh_minister')
        self.assertEqual(s.vars['ROC_ma_days_remaining'], 180)
        self.credit(s, 20)
        s.effect('ROC_econ_remove_ministers')
        s.ideas.add('ROC_idea_YuShude')
        s.effect('ROC_econ_refresh_minister')
        self.assertEqual(s.vars['ROC_ma_days_remaining'], 123)
        s.flags.add('ROC_econ_conference_pending')
        s.effect('ROC_ce_refresh')
        self.assertNotIn('ROC_ma_current_action', s.missions)
        s.flags.discard('ROC_econ_conference_pending')
        s.effect('ROC_ce_refresh')
        self.assertEqual(s.missions['ROC_ma_current_action'], 123)
        self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'], 700)

    def test_native_timeout_defers_rearm_until_engine_removes_old_mission(self):
        s = self.state()
        s.missions['ROC_ma_current_action'] = 1
        s.effect('ROC_ce_refresh')
        self.assertEqual(s.vars['ROC_ma_stage'], 1)
        s.effect('ROC_ma_timeout')
        self.assertEqual(s.vars['ROC_ma_stage'], 1)
        s.missions['ROC_ma_current_action']=0
        s.effect('ROC_ma_timeout')
        self.assertEqual(s.vars['ROC_ma_stage'], 2)
        self.assertNotIn('ROC_ma_current_action',s.missions)
        s.effect('ROC_ma_daily')
        self.assertNotIn('ROC_ma_current_action',s.missions)
        s.tick()
        self.assertEqual(s.vars['ROC_ma_stage'], 2)
        self.assertEqual(s.missions['ROC_ma_current_action'], 180)

    def test_delay_during_rearm_barrier_preserves_next_stage_clock(self):
        s=self.state();s.missions['ROC_ma_current_action']=0;s.effect('ROC_ma_timeout')
        s.vars['ROC_ma_day_delay']=21;s.effect('ROC_ma_delay_days')
        self.assertEqual(s.vars['ROC_ma_yu_days'],201)
        s.effect('ROC_ma_timeout');self.assertEqual(s.vars['ROC_ce_actual'],20)
        s.tick();self.assertEqual(s.missions['ROC_ma_current_action'],201)

    def test_credit_on_expiry_consumes_due_reward_then_applies_excess_once(self):
        s=self.state();s.missions['ROC_ma_current_action']=0;self.credit(s,660)
        self.assertEqual(s.vars['ROC_ma_yu_stage'],5)
        self.assertEqual(s.vars['ROC_ma_yu_days'],60)
        self.assertEqual(s.vars['ROC_ce_actual'],65)
        s.effect('ROC_ma_timeout');s.effect('ROC_ma_daily')
        self.assertEqual(s.vars['ROC_ce_actual'],65)
        s.tick();self.assertEqual(s.missions['ROC_ma_current_action'],60)

    def test_committee_alignment_and_no_duplicate_completion(self):
        for minister, effect, days in [('RuanXiaoxian','left',173),
                                       ('XiaoZheng','left',201),
                                       ('YuShude','left',187),
                                       ('YuShude','center',166)]:
            s = self.state(minister)
            s.effect('ROC_ma_committee_' + effect)
            self.assertEqual(s.vars['ROC_ma_days_remaining'], days)

    def test_minister_event_stale_after_switch_or_stage_change(self):
        s = self.state()
        s.effect('ROC_ma_open_yu_1')
        event = named_event(read_script('events/ROC_minister_agenda.txt'), 'ROC_minister_agenda.11')
        option = next(v for k,v in event if k == 'option' and one(v,'name').endswith('.a'))
        s.effect('ROC_econ_remove_ministers')
        s.ideas.add('ROC_idea_XiaoZheng');s.effect('ROC_econ_refresh_minister')
        before = (dict(s.vars), dict(s.missions), s.pp)
        s.run(one(option,'hidden_effect'))
        self.assertEqual((s.vars,s.missions,s.pp), before)

    def test_minister_intervention_stops_when_either_native_clock_reaches_zero(self):
        event = named_event(read_script('events/ROC_minister_agenda.txt'), 'ROC_minister_agenda.11')
        option = next(value for key, value in event if key == 'option'
                      and one(value, 'name').endswith('.a'))
        for mission in ('ROC_ma_current_action', 'ROC_decision_bop_jingjidahui'):
            with self.subTest(mission=mission):
                s = self.state()
                s.effect('ROC_ma_open_yu_1')
                self.assertTrue(s.passes(one(event, 'trigger')))
                s.missions[mission] = 0
                self.assertFalse(s.passes(one(event, 'trigger')))
                before = (dict(s.vars), dict(s.missions), set(s.flags), s.pp)
                s.run(one(option, 'hidden_effect'))
                self.assertEqual(before, (s.vars, s.missions, s.flags, s.pp))

    def test_refined_five_milestones_and_routine_preserve_original_rewards(self):
        s=self.state()
        self.assertEqual(s.vars['ROC_ma_days_remaining'],180)
        for stage,days,actual,focus in [(1,180,20,'1'),(2,180,25,'step2'),
                                      (3,180,60,'2'),(4,180,65,'step4'),
                                      (5,180,110,'3'),(6,180,115,'step6')]:
            self.credit(s,days)
            self.assertEqual(s.vars['ROC_ma_stage'],stage+1)
            self.assertEqual(s.vars['ROC_ce_actual'],actual)
            self.assertIn('ROC_ma_yu_'+focus,s.focuses)
        self.credit(s,90)
        self.assertEqual(s.vars['ROC_ce_actual'],125)

    def test_refined_legacy_saved_progress_migrates_all_ministers_once(self):
        s=self.state();s.flags.discard('ROC_ma_five_stage_migrated');s.flags.discard('ROC_ma_six_stage_migrated')
        s.vars.update(ROC_ma_clock_owner=1,ROC_ma_stage=2,ROC_ma_yu_stage=2,
                      ROC_ma_yu_days=140,ROC_ma_yan_stage=3,ROC_ma_yan_days=175,
                      ROC_ma_ruan_stage=4,ROC_ma_ruan_days=41)
        s.missions['ROC_ma_current_action']=140
        s.effect('ROC_ma_sync')
        self.assertEqual((s.vars['ROC_ma_yu_stage'],s.vars['ROC_ma_yu_days']),(3,90))
        self.assertEqual((s.vars['ROC_ma_yan_stage'],s.vars['ROC_ma_yan_days']),(5,90))
        self.assertEqual((s.vars['ROC_ma_ruan_stage'],s.vars['ROC_ma_ruan_days']),(6,180))
        self.assertIn('ROC_ma_rewarded_yu_step2',s.flags)
        self.assertIn('ROC_ma_rewarded_yan_step4',s.flags)
        self.assertEqual(s.vars['ROC_ce_actual'],0)
        s.effect('ROC_ma_sync')
        self.assertEqual(s.vars['ROC_ma_yu_days'],90)
        self.assertEqual(s.vars['ROC_ce_actual'],0)

    def test_refined_last_minister_queue_replaces_and_prioritizes_one_monthly_step(self):
        s=self.state();s.vars['ROC_ce_policy_pending']=8
        s.effect('ROC_ma_yu_direction');s.effect('ROC_ma_yu_direction')
        self.assertEqual(s.vars['ROC_ma_policy_pending'],2)
        s.effect('ROC_ma_xiao_direction')
        self.assertEqual((s.vars['ROC_ma_policy_owner'],s.vars['ROC_ma_policy_pending']),(5,-3))
        self.assertEqual(s.vars['ROC_ce_policy_pending'],8)
        s.effect('ROC_ce_policy_apply_monthly')
        self.assertEqual((s.vars['ROC_ce_policy_axis'],s.vars['ROC_ma_policy_pending']),(-1,-2))
        self.assertEqual(s.vars['ROC_ce_policy_pending'],8)
        s.effect('ROC_ma_reward_yu_1')
        self.assertEqual((s.vars['ROC_ma_policy_owner'],s.vars['ROC_ma_policy_pending']),(5,-2))

    def test_new_incumbent_native_reward_adopts_own_policy_without_stale_takeover(self):
        for old,old_slug,new,new_slug,new_owner,direction in [
            ('YuShude','yu','XiaoZheng','xiao',5,-3),
            ('XiaoZheng','xiao','YuShude','yu',1,2),
            ('YuShude','yu','YanYangchu','yan',2,0),
            ('XiaoZheng','xiao','RuanXiaoxian','ruan',3,3),
            ('XiaoZheng','xiao','ChenZanxian','chen',4,3),
        ]:
            with self.subTest(old=old,new=new):
                s=self.state(old);s.vars['ROC_ce_policy_pending']=8
                s.effect('ROC_ma_'+old_slug+'_direction')
                s.effect('ROC_econ_remove_ministers');s.ideas.add('ROC_idea_'+new);s.effect('ROC_econ_refresh_minister')
                self.native_days(s,180)
                self.assertEqual((s.vars['ROC_ma_policy_owner'],s.vars['ROC_ma_policy_pending']),(new_owner,direction))
                self.assertEqual(s.vars['ROC_ce_policy_pending'],8)
                s.effect('ROC_ma_reward_'+old_slug+'_1')
                self.assertEqual((s.vars['ROC_ma_policy_owner'],s.vars['ROC_ma_policy_pending']),(new_owner,direction))

    def test_refined_old_due_mission_migrates_before_both_callback_orders(self):
        for callback_first in (False,True):
            s=self.state();s.flags.discard('ROC_ma_five_stage_migrated');s.flags.discard('ROC_ma_six_stage_migrated')
            s.vars.update(ROC_ma_yu_stage=2,ROC_ma_stage=2,ROC_ma_yu_days=0)
            s.missions['ROC_ma_current_action']=0
            if callback_first:s.effect('ROC_ma_timeout')
            s.effect('ROC_ma_sync');s.effect('ROC_ma_timeout')
            self.assertEqual((s.vars['ROC_ma_yu_stage'],s.vars['ROC_ma_yu_days']),(4,180))
            self.assertEqual(s.vars['ROC_ce_actual'],35)
            s.tick();self.assertEqual(s.missions['ROC_ma_current_action'],180)

    def test_refined_all_ten_decisions_select_before_native_credit(self):
        decisions=economic_decisions()
        for owner,minister,slug in [(1,'YuShude','yu'),(2,'YanYangchu','yan'),
                                   (3,'RuanXiaoxian','ruan'),(4,'ChenZanxian','chen'),(5,'XiaoZheng','xiao')]:
            for number in (1,2):
                with self.subTest(minister=minister,number=number):
                    s=self.state(minister)
                    s.focuses.add(f'ROC_ma_{slug}_1')
                    if number==2:
                        s.focuses.add(f'ROC_ma_{slug}_step2')
                    s.vars.update(ROC_ma_policy_owner=5 if owner!=5 else 1,
                                  ROC_ma_policy_pending=-9,ROC_ce_policy_pending=7)
                    if number==2:
                        s.vars.update(ROC_ma_stage=3)
                        s.vars[f'ROC_ma_{slug}_stage']=3
                    s.missions['ROC_ma_current_action']=5
                    s.run(one(one(decisions,f'ROC_ma_{slug}_{number}_decision'),'complete_effect'))
                    self.assertEqual(s.vars['ROC_ma_policy_owner'],owner)
                    self.assertEqual(s.vars['ROC_ce_policy_pending'],7)
                    self.assertEqual(s.vars['ROC_ma_policy_pending'],{'yu':2,'yan':0,'ruan':3,'chen':3,'xiao':-3}[slug])
                    self.assertEqual(s.vars['ROC_ce_actual'],20 if number==1 else 35)

    def test_refined_yan_uses_actual_axis_and_legacy_common_queue_survives(self):
        s=self.state();s.vars.update(ROC_ce_policy_axis=1,ROC_ce_policy_pending=-20)
        s.effect('ROC_ma_yan_direction')
        self.assertEqual(s.vars['ROC_ma_policy_pending'],-1)
        self.assertEqual(s.vars['ROC_ce_policy_pending'],-20)
        s.effect('ROC_ce_policy_apply_monthly')
        self.assertEqual(s.vars['ROC_ce_policy_axis'],0)
        self.assertEqual(s.vars['ROC_ma_policy_pending'],0)
        s.effect('ROC_ce_policy_apply_monthly')
        self.assertEqual(s.vars['ROC_ce_policy_axis'],-1)
        self.assertEqual(s.vars['ROC_ce_policy_pending'],-19)

    def test_refined_policy_endpoints_cap_both_queues_and_never_double_step(self):
        for axis,minister,common,want_axis,want_minister,want_common in [
                (100,8,-7,100,0,-7),(-100,-8,7,-100,0,7),
                (99.5,8,7,100,0,0),(-99.5,-8,-7,-100,0,0),
                (0,100,-100,1,29,-30),(0,-100,100,-1,-29,30)]:
            s=self.state();s.vars.update(ROC_ce_policy_axis=axis,ROC_ma_policy_pending=minister,
                                         ROC_ce_policy_pending=common)
            s.effect('ROC_ce_policy_apply_monthly')
            self.assertEqual((s.vars['ROC_ce_policy_axis'],s.vars['ROC_ma_policy_pending'],
                              s.vars['ROC_ce_policy_pending']),(want_axis,want_minister,want_common))

    def test_refined_inserted_rewards_are_small_once_only_and_do_not_choose_policy(self):
        for minister,slug,project,want_progress,want_pressure,want_stability,want_pp in [
                ('YuShude','yu',1,22,50,.5,200),('YanYangchu','yan',3,22,50,.5,200),
                ('RuanXiaoxian','ruan',1,10,42,.5,200),('ChenZanxian','chen',1,10,50,.51,200),
                ('XiaoZheng','xiao',2,10,50,.5,210)]:
            s=self.state(minister);s.vars.update(ROC_ce_project_id=project,ROC_ce_project_progress=10,
                                               ROC_ce_pressure=50,ROC_ma_policy_owner=5,ROC_ma_policy_pending=-3)
            for step in ('step2','step4'):
                s.effect(f'ROC_ma_reward_{slug}_{step}');s.effect(f'ROC_ma_reward_{slug}_{step}')
            self.assertEqual(s.vars['ROC_ce_actual'],10)
            self.assertEqual(s.vars['ROC_ce_project_progress'],want_progress)
            self.assertEqual(s.vars['ROC_ce_pressure'],want_pressure)
            self.assertAlmostEqual(s.stability,want_stability);self.assertEqual(s.pp,want_pp)
            self.assertEqual((s.vars['ROC_ma_policy_owner'],s.vars['ROC_ma_policy_pending']),(5,-3))
            self.assertEqual(s.states[0]['industrial_complex'],0)

    def test_refined_old_routine_restores_graph_without_repaying_historical_rewards(self):
        s=self.state();s.flags.discard('ROC_ma_five_stage_migrated');s.flags.discard('ROC_ma_six_stage_migrated')
        s.vars.update(ROC_ma_yu_stage=4,ROC_ma_stage=4,ROC_ma_yu_days=41,ROC_ce_actual=100)
        s.missions['ROC_ma_current_action']=41
        s.focuses.difference_update({'ROC_ma_yu_'+key for key in ('1','step2','2','step4','3')})
        s.effect('ROC_ma_sync')
        self.assertEqual(s.vars['ROC_ma_stage'],6)
        self.assertEqual(s.vars['ROC_ma_days_remaining'],180)
        self.assertEqual(s.vars['ROC_ce_actual'],100)
        self.assertTrue({'ROC_ma_yu_'+key for key in ('1','step2','2','step4','3')} <= s.focuses)
        s.tick();self.credit(s,180)
        self.assertEqual(s.vars['ROC_ce_actual'],105)

    def test_refined_migration_invalidates_old_events_and_ledger_keeps_mixed_pending(self):
        s=self.state();s.effect('ROC_ma_open_yu_1')
        s.flags.discard('ROC_ma_five_stage_migrated');s.flags.discard('ROC_ma_six_stage_migrated')
        s.flags.discard('ROC_ma_policy_ledger_initialized')
        s.vars['ROC_ce_policy_pending']=12
        s.effect('ROC_ma_sync');s.effect('ROC_ce_policy_initialize')
        self.assertNotIn('ROC_ma_yu_1_pending',s.flags)
        self.assertEqual((s.vars['ROC_ma_policy_owner'],s.vars['ROC_ma_policy_pending']),(0,0))
        self.assertEqual(s.vars['ROC_ce_policy_pending'],12)

    def test_refined_migration_expired_callbacks_and_barrier_settle_exactly_once(self):
        for remaining,remove_before,blocked in [(0,False,False),(-2,False,False),
                                               (1,True,False),(0,False,True)]:
            with self.subTest(remaining=remaining,remove_before=remove_before,blocked=blocked):
                s=self.state();s.flags.discard('ROC_ma_five_stage_migrated');s.flags.discard('ROC_ma_six_stage_migrated')
                s.vars.update(ROC_ma_stage=3,ROC_ma_yu_stage=3,
                              ROC_ma_days_remaining=remaining,ROC_ma_yu_days=remaining)
                s.missions['ROC_ma_current_action']=remaining
                if remove_before:s.missions.pop('ROC_ma_current_action')
                if blocked:s.run([('set_country_flag',[('flag','ROC_ma_rearm_blocked'),('days','1')])])
                s.effect('ROC_ma_timeout');s.effect('ROC_ma_sync');s.effect('ROC_ma_timeout')
                if blocked:
                    self.assertEqual(s.vars['ROC_ma_yu_stage'],5)
                    self.assertEqual(s.vars['ROC_ce_actual'],0)
                    s.tick()
                self.assertEqual(s.vars['ROC_ma_yu_stage'],6)
                self.assertEqual(s.vars['ROC_ma_yu_days'],180)
                self.assertEqual(s.vars['ROC_ce_actual'],45)
                s.effect('ROC_ma_timeout');s.effect('ROC_ma_sync')
                self.assertEqual(s.vars['ROC_ce_actual'],45)

    def test_refined_migration_keeps_vacant_conference_personal_clock_and_term(self):
        s=self.state();s.flags.discard('ROC_ma_five_stage_migrated');s.flags.discard('ROC_ma_six_stage_migrated')
        s.vars.update(ROC_ma_stage=2,ROC_ma_yu_stage=2,ROC_ma_yu_days=140)
        s.missions['ROC_ma_current_action']=140
        s.flags.add('ROC_econ_conference_pending')
        s.effect('ROC_ma_sync')
        self.assertEqual((s.vars['ROC_ma_yu_stage'],s.vars['ROC_ma_yu_days']),(3,90))
        self.assertNotIn('ROC_ma_current_action',s.missions)
        self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'],700)
        s.ideas.discard('ROC_idea_YuShude');s.effect('ROC_econ_refresh_minister')
        s.tick();self.assertNotIn('ROC_ma_current_action',s.missions)
        s.flags.discard('ROC_econ_conference_pending');s.ideas.add('ROC_idea_YuShude')
        s.effect('ROC_econ_refresh_minister')
        self.assertEqual(s.missions['ROC_ma_current_action'],90)
        self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'],700)
        self.assertEqual(s.vars['ROC_ce_actual'],0)

    def test_refined_new_minister_selection_invalidates_old_event_choices(self):
        s=self.state();s.effect('ROC_ma_open_yu_1')
        event=named_event(read_script('events/ROC_minister_agenda.txt'),'ROC_minister_agenda.11')
        option=next(v for k,v in event if k=='option' and one(v,'name').endswith('.b'))
        s.effect('ROC_ma_select_xiao_policy')
        before=(dict(s.vars),dict(s.missions),s.pp)
        s.run(one(option,'hidden_effect'))
        self.assertEqual((s.vars,s.missions,s.pp),before)
        self.assertEqual(s.vars['ROC_ma_policy_owner'],5)

    def test_refined_event_direction_replaces_pending_without_touching_common_queue(self):
        s=self.state();s.vars.update(ROC_ma_policy_owner=1,ROC_ma_policy_pending=17,ROC_ce_policy_pending=-9)
        s.effect('ROC_ma_open_yu_1')
        event=named_event(read_script('events/ROC_minister_agenda.txt'),'ROC_minister_agenda.11')
        option=next(v for k,v in event if k=='option' and one(v,'name').endswith('.b'))
        s.run(one(option,'hidden_effect'))
        self.assertEqual((s.vars['ROC_ma_policy_owner'],s.vars['ROC_ma_policy_pending']),(1,2))
        self.assertEqual(s.vars['ROC_ce_policy_pending'],-9)

    def test_six_fresh_route_completes_each_half_year_then_runs_routine(self):
        for minister, slug in (('YuShude', 'yu'), ('YanYangchu', 'yan'),
                               ('RuanXiaoxian', 'ruan'), ('ChenZanxian', 'chen'),
                               ('XiaoZheng', 'xiao')):
            with self.subTest(minister=minister):
                s = self.state(minister)
                self.assertEqual(s.missions['ROC_ma_current_action'], 180)
                for stage, key in enumerate(('1', 'step2', '2', 'step4', '3', 'step6'), 1):
                    self.credit(s, 179)
                    self.assertNotIn(f'ROC_ma_{slug}_{key}', s.focuses)
                    self.credit(s, 1)
                    self.assertIn(f'ROC_ma_{slug}_{key}', s.focuses)
                    self.assertEqual(s.vars['ROC_ma_stage'], stage + 1)
                self.assertEqual(s.vars['ROC_ce_actual'], 115)
                self.assertEqual(s.vars['ROC_ma_days_remaining'], 90)
                self.credit(s, 90)
                self.assertEqual(s.vars['ROC_ce_actual'], 125)
                s.effect(f'ROC_ma_reward_{slug}_step6')
                self.assertEqual(s.vars['ROC_ce_actual'], 125)

    def test_six_migration_scales_active_and_saved_progress_only_once(self):
        s = self.state()
        s.flags.discard('ROC_ma_six_stage_migrated')
        s.vars.update(ROC_ma_clock_owner=1, ROC_ma_stage=1,
                      ROC_ma_yu_stage=1, ROC_ma_yu_days=35,
                      ROC_ma_yan_stage=2, ROC_ma_yan_days=42,
                      ROC_ma_ruan_stage=3, ROC_ma_ruan_days=49,
                      ROC_ma_chen_stage=4, ROC_ma_chen_days=56,
                      ROC_ma_xiao_stage=5, ROC_ma_xiao_days=63)
        s.missions['ROC_ma_current_action'] = 35
        s.effect('ROC_ma_sync')
        for slug, stage in (('yu', 1), ('yan', 2), ('ruan', 3), ('chen', 4), ('xiao', 5)):
            self.assertEqual((s.vars[f'ROC_ma_{slug}_stage'], s.vars[f'ROC_ma_{slug}_days']),
                             (stage, 90))
        self.assertEqual(s.vars['ROC_ce_actual'], 0)
        self.assertNotIn('ROC_ma_current_action', s.missions)
        s.tick()
        self.assertEqual(s.missions['ROC_ma_current_action'], 90)
        s.effect('ROC_ma_sync')
        self.assertEqual(s.vars['ROC_ma_yu_days'], 90)

    def test_six_migration_settles_old_due_fifth_without_finishing_sixth(self):
        for remaining, remove_before in ((0, False), (-2, False), (1, True)):
            with self.subTest(remaining=remaining, remove_before=remove_before):
                s = self.state()
                s.flags.discard('ROC_ma_six_stage_migrated')
                s.vars.update(ROC_ma_stage=5, ROC_ma_yu_stage=5,
                              ROC_ma_days_remaining=remaining, ROC_ma_yu_days=remaining)
                s.missions['ROC_ma_current_action'] = remaining
                if remove_before:
                    s.missions.pop('ROC_ma_current_action')
                s.effect('ROC_ma_timeout')
                s.effect('ROC_ma_sync')
                self.assertEqual((s.vars['ROC_ma_yu_stage'], s.vars['ROC_ma_yu_days']), (6, 180))
                self.assertEqual(s.vars['ROC_ce_actual'], 45)
                self.assertIn('ROC_ma_yu_3', s.focuses)
                self.assertNotIn('ROC_ma_yu_step6', s.focuses)
                s.effect('ROC_ma_timeout')
                self.assertEqual(s.vars['ROC_ce_actual'], 45)

    def test_six_migration_settles_due_old_routine_without_finishing_new_focus(self):
        cases = (
            (41, True, True, False, 100),   # Still running.
            (1, True, True, False, 100),    # One day left on a live mission.
            (0, True, False, False, 110),   # Live mission reached zero.
            (-2, True, True, False, 110),   # A late callback still settles only once.
            (1, False, True, False, 110),   # Engine removed the armed last day first.
            (0, False, False, True, 110),   # Saved pending timeout is independently valid.
            (0, False, False, False, 100),  # No active, armed, or pending clock.
            (41, False, False, True, 100),  # A stray pending flag is not an expired clock.
        )
        for legacy_three_stage in (False, True):
            for remaining, active, armed, pending, expected in cases:
                for callback_first in (False, True):
                    with self.subTest(legacy=legacy_three_stage, remaining=remaining,
                                      active=active, armed=armed, pending=pending,
                                      callback_first=callback_first):
                        s = self.state()
                        s.flags.discard('ROC_ma_six_stage_migrated')
                        stage = 4 if legacy_three_stage else 6
                        if legacy_three_stage:
                            s.flags.discard('ROC_ma_five_stage_migrated')
                        s.vars.update(ROC_ma_stage=stage, ROC_ma_yu_stage=stage,
                                      ROC_ma_days_remaining=remaining, ROC_ma_yu_days=remaining,
                                      ROC_ce_actual=100)
                        s.flags.update(f'ROC_ma_rewarded_yu_{key}' for key in ('1', 'step2', '2', 'step4', '3'))
                        if active:
                            s.missions['ROC_ma_current_action'] = remaining
                        else:
                            s.missions.pop('ROC_ma_current_action', None)
                        if not armed:
                            s.flags.discard('ROC_ma_clock_armed')
                        if pending:
                            s.flags.add('ROC_ma_timeout_pending')
                        if callback_first:
                            s.effect('ROC_ma_timeout')
                        s.effect('ROC_ma_sync')
                        s.effect('ROC_ma_timeout')
                        self.assertEqual((s.vars['ROC_ma_yu_stage'], s.vars['ROC_ma_yu_days']), (6, 180))
                        self.assertEqual(s.vars['ROC_ce_actual'], expected)
                        self.assertNotIn('ROC_ma_rewarded_yu_step6', s.flags)
                        self.assertNotIn('ROC_ma_yu_step6', s.focuses)
                        s.tick()
                        for effect in ('ROC_ma_timeout', 'ROC_ma_sync', 'ROC_ma_timeout'):
                            s.effect(effect)
                        self.assertEqual(s.vars['ROC_ce_actual'], expected)
                        self.assertEqual(s.missions['ROC_ma_current_action'], 180)

    def test_six_migration_does_not_credit_an_unowned_routine_clock(self):
        for legacy_three_stage in (False, True):
            s = self.state()
            s.flags.discard('ROC_ma_six_stage_migrated')
            if legacy_three_stage:
                s.flags.discard('ROC_ma_five_stage_migrated')
            s.vars.update(ROC_ma_clock_owner=0, ROC_ma_stage=4 if legacy_three_stage else 6,
                          ROC_ma_yu_stage=4 if legacy_three_stage else 6,
                          ROC_ma_days_remaining=0, ROC_ma_yu_days=0, ROC_ce_actual=100)
            s.missions.pop('ROC_ma_current_action')
            s.flags.add('ROC_ma_timeout_pending')
            s.effect('ROC_ma_sync')
            self.assertEqual(s.vars['ROC_ce_actual'], 100)
            self.assertNotIn('ROC_ma_timeout_pending', s.flags)
            self.assertEqual((s.vars['ROC_ma_stage'], s.vars['ROC_ma_days_remaining']), (6, 180))
            self.assertEqual(s.missions['ROC_ma_current_action'], 180)
            self.assertNotIn('ROC_ma_rewarded_yu_step6', s.flags)

    def test_six_migration_does_not_pay_for_an_unarmed_stale_mission_during_rearm(self):
        for legacy_three_stage in (False, True):
            s = self.state()
            s.flags.discard('ROC_ma_six_stage_migrated')
            if legacy_three_stage:
                s.flags.discard('ROC_ma_five_stage_migrated')
            stage = 4 if legacy_three_stage else 6
            s.vars.update(ROC_ma_stage=stage, ROC_ma_yu_stage=stage,
                          ROC_ma_days_remaining=0, ROC_ma_yu_days=0, ROC_ce_actual=100)
            s.flags.discard('ROC_ma_clock_armed')
            s.run([('set_country_flag', [('flag', 'ROC_ma_rearm_blocked'), ('days', '1')])])
            s.missions['ROC_ma_current_action'] = 0
            s.effect('ROC_ma_timeout')
            self.assertEqual(s.vars['ROC_ce_actual'], 100)
            self.assertEqual((s.vars['ROC_ma_yu_stage'], s.vars['ROC_ma_yu_days']), (6, 180))
            s.tick()
            s.effect('ROC_ma_timeout')
            self.assertEqual(s.vars['ROC_ce_actual'], 100)
            self.assertEqual(s.missions['ROC_ma_current_action'], 180)

    def test_six_migrates_three_stage_legacy_through_both_conversions(self):
        s = self.state()
        s.flags.discard('ROC_ma_five_stage_migrated')
        s.flags.discard('ROC_ma_six_stage_migrated')
        s.vars.update(ROC_ma_stage=2, ROC_ma_yu_stage=2, ROC_ma_yu_days=140,
                      ROC_ma_yan_stage=4, ROC_ma_yan_days=41)
        s.missions['ROC_ma_current_action'] = 140
        s.effect('ROC_ma_sync')
        self.assertEqual((s.vars['ROC_ma_yu_stage'], s.vars['ROC_ma_yu_days']), (3, 90))
        self.assertEqual((s.vars['ROC_ma_yan_stage'], s.vars['ROC_ma_yan_days']), (6, 180))
        self.assertEqual(s.vars['ROC_ce_actual'], 0)
        self.assertIn('ROC_ma_rewarded_yu_step2', s.flags)
        self.assertNotIn('ROC_ma_rewarded_yan_step6', s.flags)

    def test_six_same_day_term_expiry_awards_sixth_to_old_term_once(self):
        for order in (('ROC_econ_term_expired', 'ROC_ma_timeout'),
                      ('ROC_ma_timeout', 'ROC_econ_term_expired')):
            s = self.state()
            s.flags.add('ROC_ma_six_stage_migrated')
            s.vars.update(ROC_ma_stage=6, ROC_ma_yu_stage=6, ROC_ce_actual=100)
            s.missions.update(ROC_decision_bop_jingjidahui=0, ROC_ma_current_action=0)
            for effect in order:
                s.effect(effect)
            self.assertEqual(s.vars['ROC_ce_actual'], 105, order)
            self.assertEqual(s.vars['ROC_ma_yu_stage'], 7, order)
            self.assertIn('ROC_ma_yu_step6', s.focuses)
            s.effect('ROC_ma_timeout')
            self.assertEqual(s.vars['ROC_ce_actual'], 105, order)

    def test_six_rewards_are_once_only_and_leave_selected_policy_unchanged(self):
        cases = (
            ('YuShude', 'yu', 1, 16, 50, .5, 200),
            ('YanYangchu', 'yan', 3, 16, 50, .5, 200),
            ('RuanXiaoxian', 'ruan', 1, 10, 46, .5, 200),
            ('ChenZanxian', 'chen', 1, 10, 50, .505, 200),
            ('XiaoZheng', 'xiao', 2, 10, 50, .5, 205),
        )
        for minister, slug, project, progress, pressure, stability, pp in cases:
            with self.subTest(minister=minister):
                s = self.state(minister)
                s.vars.update(ROC_ce_project_id=project, ROC_ce_project_progress=10,
                              ROC_ce_pressure=50, ROC_ma_policy_owner=5,
                              ROC_ma_policy_pending=-3, ROC_ce_policy_pending=7)
                s.effect(f'ROC_ma_reward_{slug}_step6')
                s.effect(f'ROC_ma_reward_{slug}_step6')
                self.assertEqual(s.vars['ROC_ce_actual'], 5)
                self.assertEqual(s.vars['ROC_ce_project_progress'], progress)
                self.assertEqual(s.vars['ROC_ce_pressure'], pressure)
                self.assertAlmostEqual(s.stability, stability)
                self.assertEqual(s.pp, pp)
                self.assertEqual((s.vars['ROC_ma_policy_owner'], s.vars['ROC_ma_policy_pending'],
                                  s.vars['ROC_ce_policy_pending']), (5, -3, 7))

    def test_six_saved_routine_starts_new_focus_when_former_minister_returns(self):
        s = self.state()
        s.flags.discard('ROC_ma_six_stage_migrated')
        s.vars.update(ROC_ma_stage=1, ROC_ma_yu_stage=1, ROC_ma_yu_days=35,
                      ROC_ma_xiao_stage=6, ROC_ma_xiao_days=41)
        s.missions['ROC_ma_current_action'] = 35
        s.effect('ROC_ma_sync')
        self.assertEqual((s.vars['ROC_ma_yu_days'], s.vars['ROC_ma_xiao_days']), (90, 180))
        s.tick()
        s.effect('ROC_econ_remove_ministers')
        s.ideas.add('ROC_idea_XiaoZheng')
        s.effect('ROC_econ_refresh_minister')
        self.assertEqual((s.vars['ROC_ma_stage'], s.vars['ROC_ma_days_remaining']), (6, 180))
        self.assertNotIn('ROC_ma_xiao_step6', s.focuses)
        self.credit(s, 180)
        self.assertIn('ROC_ma_xiao_step6', s.focuses)
        self.assertEqual(s.vars['ROC_ma_yu_days'], 90)

    def test_six_focus_rebuild_after_tree_switch_does_not_repeat_its_reward(self):
        s = self.state()
        self.credit(s, 1080)
        self.assertIn('ROC_ma_rewarded_yu_step6', s.flags)
        self.assertEqual(s.vars['ROC_ce_actual'], 115)
        s.focuses.discard('ROC_ma_yu_step6')
        s.effect('ROC_ce_refresh')
        self.assertIn('ROC_ma_yu_step6', s.focuses)
        self.assertEqual(s.vars['ROC_ce_actual'], 115)
        self.assertEqual(s.vars['ROC_ma_stage'], 7)

    def test_six_term_and_focus_native_expiry_both_removal_and_callback_orders(self):
        for remove_first in (False, True):
            for focus_first in (False, True):
                with self.subTest(remove_first=remove_first, focus_first=focus_first):
                    s = self.state()
                    s.vars.update(ROC_ma_stage=6, ROC_ma_yu_stage=6, ROC_ce_actual=100)
                    s.missions.update(ROC_decision_bop_jingjidahui=1, ROC_ma_current_action=1)
                    s.effect('ROC_ce_refresh')
                    if focus_first:
                        s.missions = dict(reversed(list(s.missions.items())))
                    self.native_days(s, 1, remove_before_callback=remove_first)
                    self.assertEqual(s.vars['ROC_ce_actual'], 105)
                    self.assertEqual(s.vars['ROC_ma_yu_stage'], 7)
                    self.assertIn('ROC_ma_yu_step6', s.focuses)
                    s.effect('ROC_ma_timeout')
                    self.assertEqual(s.vars['ROC_ce_actual'], 105)

    def test_six_current_action_text_selects_each_focus_then_routine(self):
        texts = read_script('common/scripted_localisation/ROC_scripted_localisation.txt')
        def selected(s, name):
            defined = next(block for kind, block in texts
                           if kind == 'defined_text' and one(block, 'name') == name)
            return next(one(block, 'localization_key') for kind, block in defined
                        if kind == 'text' and s.passes(one(block, 'trigger')))
        for minister, slug in (('YuShude', 'yu'), ('YanYangchu', 'yan'),
                               ('RuanXiaoxian', 'ruan'), ('ChenZanxian', 'chen'),
                               ('XiaoZheng', 'xiao')):
            with self.subTest(minister=minister):
                s = self.state(minister)
                s.vars['ROC_ma_stage'] = 6
                self.assertEqual(selected(s, 'ROC_ma_current_action'), f'ROC_ma_{slug}_step6')
                self.assertEqual(selected(s, 'ROC_ma_current_action_desc'), 'ROC_ma_gui_action_active_desc')
                s.vars['ROC_ma_stage'] = 7
                self.assertEqual(selected(s, 'ROC_ma_current_action'), 'ROC_ma_gui_action_execution')
                self.assertEqual(selected(s, 'ROC_ma_current_action_desc'), 'ROC_ma_gui_action_execution_desc')

    def test_six_migration_keeps_an_open_same_minister_event_usable(self):
        s = self.state()
        s.effect('ROC_ma_open_yu_1')
        s.flags.discard('ROC_ma_six_stage_migrated')
        s.missions['ROC_ma_current_action'] = 35
        s.effect('ROC_ma_sync')
        event = named_event(read_script('events/ROC_minister_agenda.txt'), 'ROC_minister_agenda.11')
        option = next(v for k, v in event if k == 'option' and one(v, 'name').endswith('.c'))
        self.assertTrue(s.passes(one(event, 'trigger')))
        s.run(one(option, 'hidden_effect'))
        self.assertEqual(s.vars['ROC_ma_yu_days'], 111)
        s.tick()
        self.assertEqual(s.missions['ROC_ma_current_action'], 111)
        self.assertEqual(s.vars['ROC_ce_actual'], 0)

    def test_six_three_stage_migration_rounds_old_last_day_only_once(self):
        for old_stage, new_stage, half in ((1, 1, 105), (2, 3, 140), (3, 5, 175)):
            for remaining, expected in ((1, 1), (half, 90)):
                with self.subTest(old_stage=old_stage, remaining=remaining):
                    s = self.state()
                    s.flags.discard('ROC_ma_five_stage_migrated')
                    s.flags.discard('ROC_ma_six_stage_migrated')
                    s.vars.update(ROC_ma_stage=old_stage, ROC_ma_yu_stage=old_stage,
                                  ROC_ma_yu_days=remaining)
                    s.missions['ROC_ma_current_action'] = remaining
                    s.effect('ROC_ma_sync')
                    self.assertEqual((s.vars['ROC_ma_yu_stage'], s.vars['ROC_ma_yu_days']), (new_stage, expected))
                    s.tick()
                    self.assertEqual(s.missions['ROC_ma_current_action'], expected)

    def test_six_three_stage_migration_settles_every_expired_original_focus_once(self):
        for old_stage, new_stage, reward in ((1, 2, 20), (2, 4, 35), (3, 6, 45)):
            for remove_before in (False, True):
                with self.subTest(old_stage=old_stage, remove_before=remove_before):
                    s = self.state()
                    s.flags.discard('ROC_ma_five_stage_migrated')
                    s.flags.discard('ROC_ma_six_stage_migrated')
                    remaining = 1 if remove_before else 0
                    s.vars.update(ROC_ma_stage=old_stage, ROC_ma_yu_stage=old_stage,
                                  ROC_ma_days_remaining=remaining, ROC_ma_yu_days=remaining)
                    s.missions['ROC_ma_current_action'] = remaining
                    if remove_before:
                        s.missions.pop('ROC_ma_current_action')
                    s.effect('ROC_ma_timeout')
                    s.effect('ROC_ma_sync')
                    self.assertEqual((s.vars['ROC_ma_yu_stage'], s.vars['ROC_ma_yu_days']), (new_stage, 180))
                    self.assertEqual(s.vars['ROC_ce_actual'], reward)
                    s.effect('ROC_ma_timeout')
                    self.assertEqual(s.vars['ROC_ce_actual'], reward)

    def test_six_three_stage_conversion_uses_each_saved_ministers_original_duration(self):
        s = self.state()
        s.flags.discard('ROC_ma_five_stage_migrated')
        s.flags.discard('ROC_ma_six_stage_migrated')
        s.vars.update(ROC_ma_stage=1, ROC_ma_yu_stage=1, ROC_ma_yu_days=1,
                      ROC_ma_yan_stage=2, ROC_ma_yan_days=1,
                      ROC_ma_ruan_stage=3, ROC_ma_ruan_days=1,
                      ROC_ma_chen_stage=1, ROC_ma_chen_days=105,
                      ROC_ma_xiao_stage=2, ROC_ma_xiao_days=140)
        s.missions['ROC_ma_current_action'] = 1
        s.effect('ROC_ma_sync')
        for slug, stage, remaining in (('yu', 1, 1), ('yan', 3, 1), ('ruan', 5, 1),
                                       ('chen', 1, 90), ('xiao', 3, 90)):
            self.assertEqual((s.vars[f'ROC_ma_{slug}_stage'], s.vars[f'ROC_ma_{slug}_days']),
                             (stage, remaining))
        self.assertIn('ROC_ma_five_stage_migrated', s.flags)
        self.assertIn('ROC_ma_six_stage_migrated', s.flags)
        self.assertNotIn('ROC_ma_three_stage_conversion_pending', s.flags)
        self.assertEqual(s.vars['ROC_ce_actual'], 0)

    def test_six_migration_settles_armed_due_routine_during_rearm_barrier(self):
        for legacy_three_stage in (False, True):
            for active in (False, True):
                s = self.state()
                s.flags.discard('ROC_ma_six_stage_migrated')
                if legacy_three_stage:
                    s.flags.discard('ROC_ma_five_stage_migrated')
                stage = 4 if legacy_three_stage else 6
                remaining = 0 if active else 1
                s.vars.update(ROC_ma_stage=stage, ROC_ma_yu_stage=stage,
                              ROC_ma_days_remaining=remaining, ROC_ma_yu_days=remaining,
                              ROC_ce_actual=100)
                s.run([('set_country_flag', [('flag', 'ROC_ma_rearm_blocked'), ('days', '1')])])
                if active:
                    s.missions['ROC_ma_current_action'] = 0
                else:
                    s.missions.pop('ROC_ma_current_action')
                s.effect('ROC_ma_timeout')
                self.assertEqual(s.vars['ROC_ce_actual'], 110)
                self.assertEqual((s.vars['ROC_ma_yu_stage'], s.vars['ROC_ma_yu_days']), (6, 180))
                s.tick()
                s.effect('ROC_ma_timeout')
                self.assertEqual(s.vars['ROC_ce_actual'], 110)
                self.assertEqual(s.missions['ROC_ma_current_action'], 180)

    def test_six_migration_settles_old_routine_before_simultaneous_term_expiry(self):
        for legacy_three_stage in (False, True):
            for remove_first in (False, True):
                for routine_first in (False, True):
                    with self.subTest(legacy=legacy_three_stage, remove=remove_first, routine_first=routine_first):
                        s = self.state()
                        s.flags.discard('ROC_ma_six_stage_migrated')
                        if legacy_three_stage:
                            s.flags.discard('ROC_ma_five_stage_migrated')
                        stage = 4 if legacy_three_stage else 6
                        s.vars.update(ROC_ma_stage=stage, ROC_ma_yu_stage=stage,
                                      ROC_ma_days_remaining=1, ROC_ma_yu_days=1, ROC_ce_actual=100)
                        s.missions.update(ROC_decision_bop_jingjidahui=1, ROC_ma_current_action=1)
                        if routine_first:
                            s.missions = dict(reversed(list(s.missions.items())))
                        self.native_days(s, 1, remove_before_callback=remove_first)
                        self.assertEqual(s.vars['ROC_ce_actual'], 110)
                        self.assertEqual((s.vars['ROC_ma_yu_stage'], s.vars['ROC_ma_yu_days']), (6, 180))
                        self.assertNotIn('ROC_ma_yu_step6', s.focuses)
                        s.effect('ROC_ma_timeout')
                        self.assertEqual(s.vars['ROC_ce_actual'], 110)


if __name__ == '__main__':
    unittest.main()
