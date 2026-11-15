"""Execute the council's actual Clausewitz state transitions, not the game engine."""
import unittest

from test_roc_allied_parties import economic_decisions, ROOT, one, read_script, read_event
from test_sichuan_red_opportunity import Comparison


class ScriptState:
    def __init__(self, effects, **variables):
        self.effects, self.vars = dict(effects), variables
        structure_path = ROOT / 'common/scripted_effects/ROC_scripted_effects.txt'
        if structure_path.exists():
            self.effects.update(dict(read_script(str(structure_path))))
        memory_path = ROOT / 'common/scripted_triggers/ROC_prewar_focus_memory.txt'
        if memory_path.exists():
            self.effects.update(dict(read_script(str(memory_path))))
        for directory in ('scripted_effects', 'scripted_triggers'):
            agenda_path = ROOT / 'common' / directory / 'ROC_minister_agenda.txt'
            if agenda_path.exists():
                self.effects.update(dict(read_script(str(agenda_path))))
            story_path = ROOT / 'common' / directory / 'ROC_ma_story.txt'
            if story_path.exists():
                self.effects.update(dict(read_script(str(story_path))))
            central_path = ROOT / 'common' / directory / 'ROC_central_economy.txt'
            if central_path.exists():
                self.effects.update(dict(read_script(str(central_path))))
            committee_path = ROOT / 'common' / directory / 'ROC_committee.txt'
            if committee_path.exists():
                self.effects.update(dict(read_script(str(committee_path))))
        self.flags, self.ideas, self.focuses = set(), set(), set()
        self.missions, self.decisions, self.events = {}, set(), []
        self.axis, self.bop = 0.0, True
        self.bop_add_calls = 0
        self.pp, self.stability = 200.0, .5
        self.flag_days = {}
        self.tag, self.cosmetic_tag = 'ROC', None
        self.at_war = False
        self.exists = True
        self.loaded_trees = []

    def number(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            if value.startswith('var:'):
                return self.vars.get(value.removeprefix('var:'), 0)
            if value == 'power_balance_value':
                return self.axis
            if value.startswith('days_mission_timeout@'):
                return self.missions.get(value.split('@')[1], 0)
            return self.vars.get(value, 0)

    def compare(self, left, right):
        if isinstance(right, Comparison):
            n = self.number(right.value)
            return {'>': left > n, '<': left < n, '>=': left >= n,
                    '<=': left <= n, '=': left == n}[right.operator]
        return left == self.number(right)

    def passes(self, block):
        result = []
        for key, value in block:
            if key in self.effects:
                ok = self.passes(self.effects[key])
                if value == 'no':
                    ok = not ok
            elif key == 'NOT':
                ok = not self.passes(value)
            elif key == 'OR':
                ok = any(self.passes([item]) for item in value)
            elif key in ('AND', 'hidden_trigger', 'custom_trigger_tooltip'):
                ok = self.passes(value)
            elif key == 'tooltip':
                continue
            elif key == 'has_power_balance':
                assert value == [('id', 'ROC_power_balance')]
                ok = self.bop
            elif key == 'check_variable':
                d = dict(value)
                if 'var' in d:
                    var, limit = d['var'], d['value']
                    operators = {
                        'equals': '=', 'not_equals': '!=', 'less_than': '<',
                        'less_than_or_equals': '<=', 'greater_than': '>',
                        'greater_than_or_equals': '>=',
                    }
                    compare = d.get('compare', 'equals')
                    assert compare in operators, f'unsupported check_variable compare {compare}'
                    left, right = self.number(var), self.number(limit)
                    if compare == 'not_equals':
                        ok = left != right
                    else:
                        ok = self.compare(left, Comparison(operators[compare], limit))
                    result.append(ok)
                    continue
                assert len(value) == 1, 'unsupported check_variable shorthand'
                var, limit = value[0]
                if isinstance(limit, Comparison):
                    assert limit.operator in {'=', '<', '>'}, 'unsupported check_variable shorthand'
                ok = self.compare(self.number(var), limit)
            elif key == 'power_balance_value':
                ok = self.bop and self.compare(self.axis, one(value, 'value'))
            elif key == 'has_country_flag':
                ok = value in self.flags
            elif key == 'has_political_power':
                ok = self.compare(self.pp, value)
            elif key == 'has_idea':
                ok = value in self.ideas
            elif key == 'has_completed_focus':
                ok = value in self.focuses
            elif key == 'has_active_mission':
                ok = value in self.missions
            elif key == 'has_decision':
                ok = value in self.decisions
            elif key == 'country_exists':
                ok = self.exists and value == self.tag
            elif key in ('tag', 'original_tag'):
                ok = value == self.tag
            elif key == 'has_cosmetic_tag':
                ok = value == self.cosmetic_tag
            elif key == 'has_war':
                ok = self.at_war == (value == 'yes')
            elif key == 'ROC':
                ok = self.passes(value)
            elif key == 'always':
                ok = value == 'yes'
            else:
                raise AssertionError(f'unsupported condition {key}')
            result.append(ok)
        return all(result)

    def run(self, block):
        chain = False
        for key, value in block:
            if key == 'if':
                chain = self.passes(one(value, 'limit'))
                if chain:
                    self.run([(k, v) for k, v in value if k != 'limit'])
            elif key == 'else_if':
                if not chain and self.passes(one(value, 'limit')):
                    chain = True
                    self.run([(k, v) for k, v in value if k != 'limit'])
            elif key == 'else':
                if not chain:
                    self.run(value)
                chain = True
            elif key in self.effects:
                self.run(self.effects[key])
            elif key in ('hidden_effect', 'ROC'):
                self.run(value)
            elif key == 'round_variable':
                self.vars[value] = round(self.number(value))
            elif key in ('set_variable', 'add_to_variable', 'subtract_from_variable',
                         'multiply_variable', 'divide_variable', 'clamp_variable'):
                d = dict(value)
                var = d.get('var', next(iter(d)))
                n = self.number(d.get('value', d.get(var, '0')))
                old = self.vars.get(var, 0)
                if key == 'set_variable': self.vars[var] = n
                elif key == 'add_to_variable': self.vars[var] = old + n
                elif key == 'subtract_from_variable': self.vars[var] = old - n
                elif key == 'multiply_variable': self.vars[var] = old * n
                elif key == 'divide_variable': self.vars[var] = old / n
                else:
                    self.vars[var] = max(self.number(d.get('min', '-100000')),
                                         min(old, self.number(d.get('max', '100000'))))
            elif key == 'set_country_flag':
                self.flags.add(one(value, 'flag') if isinstance(value, list) else value)
                if isinstance(value, list):
                    self.flag_days[one(value, 'flag')] = self.number(one(value, 'days'))
            elif key == 'clr_country_flag':
                self.flags.discard(value)
                self.flag_days.pop(value, None)
            elif key == 'activate_mission':
                definitions = {}
                for path in (ROOT / 'common/decisions').glob('ROC*.txt'):
                    for _, category in read_script(str(path)):
                        if isinstance(category, list):
                            definitions.update((k,v) for k,v in category if isinstance(v,list))
                self.missions[value] = self.number(one(definitions[value], 'days_mission_timeout'))
            elif key == 'remove_mission': self.missions.pop(value, None)
            elif key == 'remove_decision': self.decisions.discard(value)
            elif key == 'add_days_mission_timeout':
                mission = one(value, 'mission')
                if mission in self.missions:
                    self.missions[mission] += self.number(one(value, 'days'))
            elif key == 'add_power_balance_value':
                try:
                    amount = float(one(value, 'value'))
                except (ValueError, TypeError):
                    raise AssertionError('unsupported add_power_balance_value value')
                self.axis += amount
                self.bop_add_calls += 1
            elif key == 'country_event': self.events.append(one(value, 'id'))
            elif key == 'complete_national_focus':
                if value not in self.focuses:
                    self.focuses.add(value)
                    # These shared focus rewards are part of the actual engine callback.
                    if value.startswith('ROC_ma_'):
                        path = ROOT/'common/national_focus/ROC_minister_agenda.txt'
                        if path.exists():
                            focus = next(block for key,block in read_script(str(path))
                                         if key == 'shared_focus' and one(block,'id') == value)
                            self.run(one(focus,'completion_reward'))
                        else:
                            # During parallel authoring the guarded runtime fallback still works.
                            self.run(self.effects[value.replace('ROC_ma_', 'ROC_ma_reward_', 1)])
            elif key == 'while_loop_effect':
                count = 0
                while self.passes(one(value, 'limit')):
                    self.run([(k,v) for k,v in value if k != 'limit'])
                    count += 1
                    assert count < 10000, 'unbounded production loop'
            elif key == 'random_list':
                # Deterministically choose a branch; tests inspect native weights separately.
                self.random_calls = getattr(self, 'random_calls', 0) + 1
                self.run(value[getattr(self, 'random_choice', 0) % len(value)][1])
            elif key == 'remove_power_balance': self.bop = False
            elif key == 'ROOT': self.run(value)
            elif key == 'remove_ideas': self.ideas.discard(value)
            elif key == 'add_ideas': self.ideas.add(value)
            elif key == 'load_focus_tree':
                assert dict(value) == {'tree': 'ROC_datong_postwar', 'keep_completed': 'yes'}
                self.loaded_trees.append(one(value, 'tree'))
                # New tree IDs all use ROC_pw_; keep_completed cannot retain old IDs.
                self.focuses = {focus for focus in self.focuses if focus.startswith(('ROC_pw_', 'ROC_ma_'))}
            elif key == 'add_political_power': self.pp += self.number(value)
            elif key == 'add_stability': self.stability = max(0, min(1, self.stability + self.number(value)))
            elif key == 'custom_effect_tooltip':
                pass
            elif key.startswith('ROC_scripted_effects_'):
                pass  # Existing dynamic modifier recomputation is covered separately.
            else:
                raise AssertionError(f'unsupported effect {key}')


class EconomicCouncil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'common/scripted_effects/ROC_scripted_effects.txt'
        cls.effects = dict(read_script(str(path))) if path.exists() else {}
        trigger_path = ROOT / 'common/scripted_triggers/ROC_economic_council.txt'
        if trigger_path.exists(): cls.effects.update(dict(read_script(str(trigger_path))))
        cls.effects.update(dict(read_script('common/scripted_triggers/ROC_legislation.txt')))

    def execute(self, name, state):
        self.assertIn(name, self.effects, f'missing production effect {name}')
        state.run(self.effects[name])

    def test_retired_queue_is_inert_at_every_old_axis_endpoint(self):
        for axis in (-1,-.5,0,.5,1):
            state=ScriptState(self.effects,ROC_econ_pending_shift=.3)
            state.axis=axis
            self.execute('ROC_econ_queue_shift',state)
            self.execute('ROC_econ_apply_monthly',state)
            self.assertEqual(state.axis,axis)
            self.assertEqual(state.vars['ROC_econ_pending_shift'],0)
            self.assertEqual(state.bop_add_calls,0)

    def test_monthly_refresh_does_not_change_political_mission_time(self):
        state=ScriptState(self.effects)
        state.missions.update(ROC_decision_zuopai=12,ROC_decision_zhongpai=23,ROC_decision_youpai=34)
        before=dict(state.missions)
        self.execute('ROC_econ_apply_monthly',state)
        self.assertEqual(state.missions,before)

    def test_old_active_mission_migrates_without_resetting_and_stage_boundaries(self):
        state = ScriptState(self.effects)
        for remaining, stage in [(1080, 1), (731, 1), (730, 2), (366, 2), (365, 3), (1, 3)]:
            state.missions['ROC_decision_bop_jingjidahui'] = remaining
            self.execute('ROC_econ_refresh', state)
            self.assertEqual(state.vars['ROC_econ_term_remaining'], remaining)
            self.assertEqual(state.vars['ROC_econ_stage'], stage)
            self.assertEqual(state.missions['ROC_decision_bop_jingjidahui'], remaining)
        self.assertEqual(state.events, [])

    def test_delayed_conference_and_duplicate_choice_do_not_restart_term(self):
        state = ScriptState(self.effects)
        self.execute('ROC_econ_term_expired', state)
        self.execute('ROC_econ_term_expired', state)
        self.assertEqual(len(state.events), 1)
        self.assertNotIn('ROC_decision_bop_jingjidahui', state.missions)
        self.execute('ROC_econ_start_term', state)
        state.missions['ROC_decision_bop_jingjidahui'] = 920
        self.execute('ROC_econ_start_term', state)
        self.assertEqual(state.missions['ROC_decision_bop_jingjidahui'], 920)

    def test_timeout_with_engine_mission_still_present_keeps_pending_stage_zero(self):
        state = ScriptState(self.effects)
        state.missions['ROC_decision_bop_jingjidahui'] = 0
        state.flags.add('ROC_econ_term_active')
        self.execute('ROC_econ_term_expired', state)
        self.assertIn('ROC_econ_conference_pending', state.flags)
        self.assertNotIn('ROC_econ_term_active', state.flags)
        self.assertEqual(state.vars['ROC_econ_stage'], 0)
        self.assertEqual(state.events, ['ROC_pingheng.9998'])
        state.missions.clear()
        self.execute('ROC_econ_term_expired', state)
        self.assertEqual(len(state.events), 1)

    def test_yan_settlement_supports_central_parties_without_axis_or_free_delivery(self):
        state=ScriptState(self.effects)
        self.execute('ROC_econ_yan_pilot_settlement',state)
        self.assertEqual(state.vars['ROC_ma_left_favor'],5)
        self.assertEqual(state.vars['ROC_ma_right_favor'],5)
        self.assertEqual(state.vars.get('ROC_ce_actual',0),0)
        self.assertEqual(state.bop_add_calls,0)

    def test_no_axis_is_needed_but_administration_authorisation_is_required(self):
        state=ScriptState(self.effects)
        state.bop=False
        self.execute('ROC_econ_start_term',state)
        self.assertEqual(state.missions,{})
        state.focuses.add('gaizaojingjidezhunbei')
        self.execute('ROC_econ_start_term',state)
        self.assertEqual(state.missions,{'ROC_decision_bop_jingjidahui':1095})

    def test_missing_clock_bootstrap_is_idempotent_and_pending_blocks_recovery(self):
        state = ScriptState(self.effects, ROC_econ_pending_shift=.12)
        state.focuses.add('gaizaojingjidezhunbei')
        state.ideas.add('ROC_idea_YuShude')
        self.execute('ROC_econ_bootstrap', state)
        state.missions['ROC_decision_bop_jingjidahui'] = 1001
        self.execute('ROC_econ_bootstrap', state)
        self.assertEqual(state.missions['ROC_decision_bop_jingjidahui'], 1001)
        self.assertEqual(state.ideas, {'ROC_idea_YuShude','ROC_ce_structure_mixed'})
        self.assertEqual(state.vars['ROC_econ_pending_shift'], 0)
        self.assertFalse(state.events)
        state.missions.clear()
        state.flags.add('ROC_econ_conference_pending')
        self.execute('ROC_econ_bootstrap', state)
        self.assertFalse(state.missions)

    def test_expired_resignation_choice_cannot_overwrite_next_cabinet(self):
        from test_roc_central_economy import CentralState
        state=CentralState();state.initialize()
        state.ideas.add('ROC_idea_XiaoZheng')
        before=set(state.ideas)
        state.choose(7,'a')
        self.assertEqual(state.ideas,before)
        self.assertEqual(state.missions['ROC_decision_bop_jingjidahui'],700)

    def test_direct_party_appointment_invalidates_earlier_resignation(self):
        state = ScriptState(self.effects, ROC_econ_pending_shift=.1)
        state.flags.add('ROC_econ_resignation_pending')
        state.ideas = {'ROC_idea_RuanXiaoxian'}
        state.missions['ROC_decision_bop_jingjidahui'] = 45
        self.execute('ROC_econ_direct_appointment_refresh', state)
        self.assertNotIn('ROC_econ_resignation_pending', state.flags)
        self.assertEqual(state.ideas, {'ROC_idea_RuanXiaoxian'})
        self.assertEqual(state.missions['ROC_decision_bop_jingjidahui'], 45)
        self.assertEqual(state.vars['ROC_econ_pending_shift'], 0)

    def test_finished_race_cancels_compromise_costs(self):
        state = ScriptState(self.effects)
        state.decisions.update({'ROC_decision_zuoxiantuoxie', 'ROC_decision_youxiantuoxie'})
        self.execute('ROC_econ_finish_race', state)
        self.assertFalse(state.decisions)

    def test_personal_projects_have_distinct_stages_native_duration_and_term_flags(self):
        decisions = dict(economic_decisions())
        ids = [key for key in decisions if key.startswith('ROC_econ_') and key.endswith(('_pilot', '_expansion'))]
        self.assertEqual(len(ids), 10)
        for ident in ids:
            block = decisions[ident]
            self.assertEqual(one(block, 'days_remove'), '90' if ident.endswith('pilot') else '180')
            self.assertEqual(one(block, 'cancel_effect'), [])
            self.assertIn(ident + '_done', str(one(block, 'remove_effect')))
            self.assertIn('hidden_trigger', str(one(block, 'available')))

    def test_no_debug_or_native_balance_gameplay_path_remains(self):
        source=(ROOT/'common/decisions/ROC.txt').read_text(encoding='utf-8')
        self.assertNotIn('set_power_balance',source)
        self.assertNotIn('add_power_balance_value',source)
        bop=(ROOT/'common/bop/ROC_bop.txt').read_text(encoding='utf-8')
        self.assertNotIn('on_activate',bop)
        self.assertNotIn('on_deactivate',bop)
        self.assertNotIn('modifier',bop)

    def test_daily_and_monthly_controllers_only_run_from_roc_country_hooks(self):
        for path in ('common/on_actions/ROC.txt', 'common/on_actions/ROC_economic_council.txt'):
            hooks = one(read_script(path), 'on_actions')
            self.assertTrue(hooks)
            for name, block in hooks:
                self.assertIn(name, {'on_daily_ROC', 'on_monthly_ROC'}, path)
                self.assertNotIn(name, {'on_daily', 'on_monthly'}, path)
        hooks = dict(one(read_script('common/on_actions/ROC_economic_council.txt'), 'on_actions'))
        self.assertIn('ROC_ce_daily', str(hooks['on_daily_ROC']))
        self.assertIn('ROC_econ_head_daily', str(hooks['on_daily_ROC']))
        self.assertIn('ROC_econ_apply_monthly', str(hooks['on_monthly_ROC']))

    def test_replacement_preserves_paid_projects_without_early_rewards_and_preserves_term(self):
        state=ScriptState(self.effects)
        state.focuses.add('gaizaojingjidezhunbei')
        state.missions['ROC_decision_bop_jingjidahui']=40
        state.decisions.update({'ROC_econ_yu_pilot','ROC_decision_bop_left_fcsyqy'})
        state.ideas={'ROC_idea_XiaoZheng'}
        self.execute('ROC_econ_refresh_minister',state)
        self.assertIn('ROC_econ_yu_pilot',state.decisions)
        self.assertEqual(state.vars.get('ROC_ce_actual',0),0)
        self.assertEqual(state.missions['ROC_decision_bop_jingjidahui'],40)

    def test_administrative_support_never_shortens_independent_committee_agenda(self):
        state=ScriptState(self.effects)
        state.focuses.add('gemingweiyuanhui')
        state.missions.update(ROC_decision_bop_jingjidahui=100,ROC_decision_zhongpai=2,ROC_decision_zuopai=30,ROC_decision_youpai=40)
        self.execute('ROC_econ_help_center',state)
        self.assertEqual(state.missions['ROC_decision_zhongpai'],2)
        state.focuses.add('jingchenghezuo')
        self.execute('ROC_econ_finish_race',state)
        self.assertEqual(state.missions,{'ROC_decision_bop_jingjidahui':100})

    def test_axis_head_impeachment_fires_after_ninety_continuous_days(self):
        state=ScriptState(self.effects,ROC_ce_policy_axis=80)
        state.bop=False;state.flags.add('ROC_ce_policy_migrated')
        state.focuses.add('guangzhouqiyi');state.ideas.add('ROC_idea_Xuqian')
        for _ in range(89):self.execute('ROC_econ_head_daily',state)
        self.assertEqual(state.events,[])
        self.assertEqual(state.vars['ROC_econ_head_mismatch_days'],89)
        self.execute('ROC_econ_head_daily',state)
        self.assertEqual(state.events,['ROC_pingheng.1002'])
        for _ in range(100):self.execute('ROC_econ_head_daily',state)
        self.assertEqual(state.events,['ROC_pingheng.1002'])

    def test_conference_choices_and_direct_appointments_use_controller(self):
        for ident in ('9997', '9998', '9999'):
            event = read_event('ROC_pingheng.' + ident)
            for key, option in event:
                if key == 'option':
                    self.assertIn('ROC_econ_start_term', str(option))
                    self.assertNotIn('add_power_balance_value', str(option))

    def test_initialization_and_conference_options_hide_recursive_internal_state(self):
        effects=dict(self.effects)
        for directory in ('scripted_effects','scripted_triggers'):
            for path in (ROOT/'common'/directory).glob('ROC*.txt'):
                effects.update(dict(read_script(str(path))))

        def visible(entries,stack=()):
            result=[]
            for key,value in entries:
                if key in ('hidden_effect','hidden_trigger'):continue
                if key in effects:
                    self.assertNotIn(key,stack,'visible scripted-effect recursion')
                    result.extend(visible(effects[key],stack+(key,)))
                else:
                    result.append((key,value))
                    if isinstance(value,list):result.extend(visible(value,stack))
            return result

        private={'set_variable','add_to_variable','subtract_from_variable','multiply_variable',
                 'divide_variable','clamp_variable','check_variable','has_country_flag',
                 'set_country_flag','clr_country_flag','has_active_mission','activate_mission',
                 'remove_mission','remove_decision','remove_ideas','remove_power_balance'}
        for event_id in ('ROC_focus.23','ROC_pingheng.9997','ROC_pingheng.9998','ROC_pingheng.9999'):
            for key,option in read_event(event_id):
                if key!='option':continue
                expanded=visible(option)
                exposed=private & {key for key,value in expanded}
                self.assertFalse(exposed,(event_id,one(option,'name'),exposed))
                expected='ROC_ce_administration_started_tt' if event_id=='ROC_focus.23' else 'ROC_ce_conference_start_tt'
                self.assertEqual([v for k,v in expanded if k=='custom_effect_tooltip'],[expected])
                if event_id!='ROC_focus.23':
                    self.assertEqual(len([v for k,v in expanded if k=='add_ideas']),1)


if __name__ == '__main__':
    unittest.main()
