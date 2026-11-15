"""Central construction executes the shipped script, without claiming engine QA."""
import unittest
from pathlib import Path

from test_roc_allied_parties import economic_decisions, ROOT, read_script, one, named_event
from test_roc_economic_council import ScriptState


class CentralState(ScriptState):
    def __init__(self, **variables):
        effects = {}
        effects.update(dict(read_script('common/scripted_effects/ROC_scripted_effects.txt')))
        for name in ('ROC_central_economy', 'ROC_economic_council', 'ROC_legislation'):
            effects.update(dict(read_script(f'common/scripted_triggers/{name}.txt')))
        super().__init__(effects, **variables)
        self.states = [dict(owned=True, controlled=True, core=True, slots=2, infrastructure=2, industrial_complex=0)]
        self.current_state = None
        self.focuses.add('gaizaojingjidezhunbei')
        self.missions['ROC_decision_bop_jingjidahui'] = 700

    def passes(self, block):
        for key, value in block:
            if key == 'any_owned_state':
                if not any(self.state_passes(state, value) for state in self.states if state['owned']):
                    return False
            elif key in ('is_controlled_by', 'is_core_of', 'is_owned_by'):
                field = {'is_controlled_by':'controlled', 'is_core_of':'core', 'is_owned_by':'owned'}[key]
                if not self.current_state[field]: return False
            elif key == 'free_building_slots':
                if self.current_state['slots'] < 1: return False
            elif key == 'infrastructure':
                if not self.compare(self.current_state['infrastructure'], value): return False
            elif not super().passes([(key, value)]): return False
        return True

    def state_passes(self, state, block):
        previous = self.current_state
        self.current_state = state
        try: return self.passes(block)
        finally: self.current_state = previous

    def run(self, block):
        # Preserve native if/else chains by replacing only scope commands before dispatch.
        transformed = []
        for key, value in block:
            if key == 'random_owned_controlled_state':
                targets = [s for s in self.states if s['owned'] and s['controlled'] and self.state_passes(s, one(value, 'limit'))]
                if targets:
                    previous = self.current_state
                    self.current_state = targets[0]
                    self.run([(k,v) for k,v in value if k != 'limit'])
                    self.current_state = previous
            elif key == 'add_building_construction':
                kind = one(value, 'type')
                self.current_state[kind] += int(one(value, 'level'))
                if kind == 'industrial_complex': self.current_state['slots'] -= 1
            else:
                # Flush chunks to retain complete consecutive if/else_if chains.
                transformed.append((key,value))
        if transformed: super().run(transformed)

    def effect(self, name): self.run(self.effects[name])

    def initialize(self): self.effect('ROC_ce_initialize')

    def tick(self, days=1):
        for _ in range(days):
            for flag in list(self.flag_days):
                self.flag_days[flag] -= 1
                if self.flag_days[flag] <= 0:
                    self.flag_days.pop(flag)
                    self.flags.discard(flag)
            self.effect('ROC_ce_daily')

    def choose(self, event_id, option):
        event = named_event(read_script('events/ROC_central_economy.txt'), f'ROC_central_economy.{event_id}')
        block = next(v for k,v in event if k=='option' and one(v,'name').endswith('.'+option))
        self.run(one(block,'hidden_effect'))


class CentralEconomy(unittest.TestCase):
    def test_controller_exists_and_is_independent_of_native_economic_axis(self):
        path = ROOT / 'common/scripted_effects/ROC_scripted_effects.txt'
        self.assertTrue(path.exists(), 'central delivery controller must exist')
        text = path.read_text(encoding='utf-8-sig')
        self.assertIn('ROC_ce_initialize', text)
        self.assertIn('ROC_ce_daily', text)
        self.assertNotIn('add_power_balance_value', text)

    def state(self):
        state = CentralState()
        state.initialize()
        state.flags.update({'ROC_ce_program_done','ROC_ce_industry_unlocked','ROC_ce_agriculture_unlocked','ROC_ce_transport_unlocked'})
        return state

    def test_legacy_adoption_is_idempotent_and_preserves_real_project_and_clocks(self):
        s = CentralState(ROC_ce_project_id=2, ROC_ce_project_progress=42)
        s.missions.update(ROC_decision_zuopai=37, ROC_decision_youpai=51)
        before = dict(s.missions)
        s.initialize()
        self.assertFalse(s.bop)
        self.assertEqual(s.missions, before)
        self.assertEqual(s.vars['ROC_ce_actual'],0)
        self.assertEqual(s.vars['ROC_ce_expected'],0)
        self.assertEqual(s.vars['ROC_ce_project_progress'],42)
        s.vars['ROC_ce_actual']=12
        s.vars['ROC_ma_left_favor']=23
        s.initialize()
        self.assertEqual(s.vars['ROC_ce_actual'],12)
        self.assertEqual(s.vars['ROC_ma_left_favor'],23)

    def test_first_quarter_is_preparation_and_inactivity_eventually_faces_accountability(self):
        s=self.state()
        s.tick(90)
        self.assertEqual(s.vars['ROC_ce_expected'],0)
        self.assertEqual(s.vars['ROC_ce_reviews_behind'],0)
        s.tick(270)
        self.assertIn('ROC_central_economy.5',s.events)
        self.assertGreaterEqual(s.vars['ROC_ce_reviews_behind'],2)
        self.assertGreaterEqual(s.vars['ROC_ce_opposition_count'],2)

    def test_support_minister_and_temporary_funding_change_real_delivery_date(self):
        durations=[]
        for attitude, minister, funded in [(50,None,False),(80,'YuShude',True),(10,None,False)]:
            s=self.state()
            for party in ('left','center','right'): s.vars[f'ROC_ma_{party}_favor']=attitude
            if minister: s.ideas.add('ROC_idea_'+minister)
            if funded: s.flags.add('ROC_ce_funded')
            s.effect('ROC_ce_start_industry')
            days=0
            while s.vars['ROC_ce_project_id'] and days<600:
                s.effect('ROC_ce_refresh');s.effect('ROC_ce_project_daily');days+=1
            self.assertEqual(s.states[0]['industrial_complex'],1)
            self.assertEqual(s.vars['ROC_ce_actual'],20)
            durations.append(days)
        self.assertLess(durations[1],durations[0])
        self.assertGreater(durations[2],durations[0])
        self.assertGreaterEqual(min(durations),91,'same event ID cannot recur within its 14-day window')

    def test_parallel_start_is_rejected_and_authorisation_is_rechecked(self):
        s=self.state();s.flags.discard('ROC_ce_industry_unlocked')
        s.effect('ROC_ce_start_industry');self.assertEqual(s.vars.get('ROC_ce_project_id',0),0)
        s.effect('ROC_ce_start_agriculture');s.vars['ROC_ce_project_progress']=33
        s.effect('ROC_ce_start_transport')
        self.assertEqual(s.vars['ROC_ce_project_id'],2)
        self.assertEqual(s.vars['ROC_ce_project_progress'],33)

    def test_lost_capacity_or_territory_cannot_deliver_empty_score(self):
        for invalid in ('owned','controlled','core','slots'):
            s=self.state();s.effect('ROC_ce_start_industry')
            s.vars['ROC_ce_project_progress']=100
            s.states[0][invalid]=0
            s.effect('ROC_ce_deliver')
            self.assertEqual(s.vars['ROC_ce_actual'],0)
            self.assertEqual(s.vars['ROC_ce_project_id'],1)
            self.assertEqual(s.vars['ROC_ce_project_progress'],99)
            self.assertIn('ROC_ce_no_delivery_target',s.flags)
            s.states[0][invalid]=2 if invalid=='slots' else True
            s.vars['ROC_ce_project_progress']=100
            s.effect('ROC_ce_deliver')
            self.assertEqual(s.vars['ROC_ce_actual'],20)
            self.assertEqual(s.states[0]['industrial_complex'],1)

    def test_infrastructure_programs_have_distinct_pace_and_real_output(self):
        speeds=[]
        for project in ('agriculture','transport'):
            s=self.state();s.effect('ROC_ce_start_'+project)
            speeds.append(s.vars['ROC_ce_speed'])
            s.vars['ROC_ce_project_progress']=100
            s.effect('ROC_ce_deliver')
            self.assertEqual(s.states[0]['infrastructure'],3)
            self.assertEqual(s.vars['ROC_ce_actual'],20)
            self.assertAlmostEqual(s.stability,.51 if project=='agriculture' else .5)
        self.assertGreater(speeds[1],speeds[0])

    def test_negotiation_stops_real_work_but_expected_progress_keeps_advancing(self):
        s=self.state();s.effect('ROC_ce_start_industry')
        s.vars['ROC_ce_project_progress']=25
        s.flags.add('ROC_ce_event_1_pending')
        s.choose(1,'b')
        s.tick(14)
        self.assertEqual(s.vars['ROC_ce_project_progress'],25)
        self.assertGreater(s.vars['ROC_ce_project_expected'],0)
        s.tick()
        self.assertGreater(s.vars['ROC_ce_project_progress'],25)

    def test_every_event_has_native_default_and_expired_choices_are_inert(self):
        entries=read_script('events/ROC_central_economy.txt')
        for n in range(1,7):
            event=named_event(entries,f'ROC_central_economy.{n}')
            self.assertEqual(one(event,'timeout_days'),'14')
            options=[v for k,v in event if k=='option']
            self.assertEqual(len(options),3)
            self.assertTrue(one(options[0],'name').endswith('.c'))
            for key in 'abc':
                s=self.state();s.vars['ROC_ce_project_id']=1
                before=(dict(s.vars),s.pp,s.stability,set(s.ideas))
                s.choose(n,key)
                self.assertEqual((s.vars,s.pp,s.stability,s.ideas),before)

    def test_native_timeout_day_still_executes_once_and_cannot_spend_free_money(self):
        s=self.state();s.effect('ROC_ce_start_industry');s.flags.add('ROC_ce_event_1_seen')
        s.flags.add('ROC_ce_event_1_pending');s.flag_days['ROC_ce_event_1_pending']=15
        s.tick(14)
        pressure=s.vars['ROC_ce_pressure'];s.choose(1,'c')
        self.assertEqual(s.vars['ROC_ce_pressure'],pressure+8)
        before=dict(s.vars);s.choose(1,'c');self.assertEqual(s.vars,before)
        s.flags.add('ROC_ce_event_1_pending');s.pp=29
        before=dict(s.vars);s.choose(1,'a')
        self.assertEqual(s.pp,29);self.assertEqual(s.vars,before)

    def test_resignation_and_next_term_keep_unfinished_project(self):
        s=self.state();s.effect('ROC_ce_start_industry');s.vars['ROC_ce_project_progress']=61
        s.effect('ROC_ce_resign');self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'],700)
        s.choose(7,'b')
        self.assertIn('ROC_idea_YanYangchu',s.ideas)
        self.assertEqual(s.vars['ROC_ce_project_progress'],61)
        self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'],700)
        s.missions.clear();s.effect('ROC_econ_term_expired');s.effect('ROC_econ_start_term')
        self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'],1095)
        self.assertEqual(s.vars['ROC_ce_project_progress'],61)

    def test_grace_skips_one_review_without_erasing_debt_and_false_reports_are_checked(self):
        s=self.state();s.vars.update(ROC_ce_expected=40,ROC_ce_reviews_behind=2)
        s.vars['ROC_ma_left_favor']=-80;s.vars['ROC_ma_right_favor']=-80
        s.flags.add('ROC_ce_accountability_pending');s.choose(5,'b')
        self.assertEqual(s.vars['ROC_ce_expected'],40)
        s.effect('ROC_ce_quarterly_review');self.assertNotIn('ROC_ce_accountability_pending',s.flags)
        s.effect('ROC_ce_quarterly_review');self.assertIn('ROC_ce_accountability_pending',s.flags)
        paid=s.pp;s.choose(5,'b');self.assertEqual(s.pp,paid)
        s.flags.discard('ROC_ce_accountability_pending');s.vars['ROC_ce_project_id']=1
        s.flags.add('ROC_ce_event_3_pending');s.choose(3,'b')
        self.assertEqual(s.vars['ROC_ce_actual'],0)
        s.effect('ROC_ce_quarterly_review');self.assertNotIn('ROC_ce_accountability_pending',s.flags)
        s.tick(30);self.assertIn('ROC_central_economy.6',s.events)

    def test_policy_compatibility_never_manufactures_delivery_or_changes_political_clocks(self):
        s=self.state();s.missions.update(ROC_decision_zuopai=17,ROC_decision_zhongpai=28,ROC_decision_youpai=39)
        before=dict(s.missions)
        for effect in ('ROC_ce_policy_public','ROC_ce_policy_market','ROC_ce_focus_contribution','ROC_econ_help_center'):
            s.effect(effect)
        self.assertEqual(s.vars['ROC_ce_actual'],0)
        self.assertEqual(s.missions,before)

    def test_paid_legacy_projects_survive_replacement_and_new_term_then_settle(self):
        decisions=dict(economic_decisions())
        for person in ('yu','yan','ruan','chen','xiao'):
            for kind in ('pilot','expansion'):
                ident=f'ROC_econ_{person}_{kind}'
                s=self.state();s.decisions.add(ident)
                s.effect('ROC_ce_resign');s.choose(7,'e')
                self.assertIn(ident,s.decisions)
                self.assertFalse(s.passes(one(decisions[ident],'cancel_trigger')))
                s.missions.clear();s.effect('ROC_econ_term_expired');s.effect('ROC_econ_start_term')
                self.assertIn(ident,s.decisions)
                s.run(one(decisions[ident],'remove_effect'))
                self.assertEqual(s.vars['ROC_ce_actual'],2,ident)
                self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'],1095)

    def test_only_completed_project_can_deliver_and_duplicate_delivery_is_inert(self):
        s=self.state();s.effect('ROC_ce_start_industry')
        s.effect('ROC_ce_deliver')
        self.assertEqual(s.vars['ROC_ce_actual'],0)
        s.vars['ROC_ce_project_progress']=100;s.effect('ROC_ce_deliver')
        self.assertEqual(s.vars['ROC_ce_actual'],20)
        s.effect('ROC_ce_deliver')
        self.assertEqual(s.vars['ROC_ce_actual'],20)

    def test_missing_cabinet_recovers_with_one_initial_conference(self):
        s=self.state();s.missions.clear();s.ideas.clear()
        s.effect('ROC_econ_bootstrap')
        s.effect('ROC_econ_bootstrap')
        self.assertEqual(s.events.count('ROC_pingheng.9997'),1)
        self.assertIn('ROC_econ_conference_pending',s.flags)

    def test_route_conflict_opens_one_replacement_window(self):
        s=self.state();s.ideas.add('ROC_idea_XiaoZheng')
        s.effect('ROC_econ_public_route');s.tick()
        self.assertEqual(s.events.count('ROC_central_economy.7'),1)
        self.assertNotIn('ROC_economic_council.1',s.events)
        self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'],700)

    def test_completed_legacy_delivery_during_conference_is_accounted_next_term(self):
        s=self.state();s.missions.clear();s.flags.add('ROC_econ_conference_pending')
        s.effect('ROC_econ_reconcile')
        self.assertEqual(s.vars['ROC_ce_actual'],0)
        self.assertEqual(s.vars['ROC_ce_unassigned_delivery'],2)
        s.effect('ROC_econ_start_term')
        self.assertEqual(s.vars['ROC_ce_actual'],2)
        self.assertEqual(s.vars['ROC_ce_unassigned_delivery'],0)

    def test_postwar_survey_opens_all_economic_paths_without_prewar_preparation_memory(self):
        from test_roc_allied_parties import read_event
        s=CentralState();s.focuses.clear();s.missions.clear();s.flags.add('ROC_postwar_active')
        # Focus rewards initialize before setting their flag. The next country daily adopts it.
        s.effect('ROC_ce_initialize')
        self.assertNotIn('ROC_ce_initialized',s.flags)
        s.flags.add('ROC_ce_survey_done')
        s.effect('ROC_ce_initialize');s.effect('ROC_econ_bootstrap')
        self.assertIn('ROC_ce_initialized',s.flags)
        self.assertEqual(s.events.count('ROC_pingheng.9997'),1)
        category=one(read_script('common/decisions/categories/ROC.txt'),'ROC_economic_administration')
        self.assertTrue(s.passes(one(category,'visible')))
        meeting=read_event('ROC_pingheng.9997')
        option=next(v for k,v in meeting if k=='option')
        s.run([(k,v) for k,v in option if k!='name'])
        self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'],1095)
        mission=one(economic_decisions(),'ROC_decision_bop_jingjidahui')
        self.assertTrue(s.passes(one(mission,'activation')))
        self.assertTrue(s.passes([('ROC_bill_session_ready','yes')]))
        old_projects=dict(economic_decisions())
        self.assertFalse(s.passes(one(old_projects['ROC_econ_yu_pilot'],'visible')))
        proposal=one(economic_decisions(),'ROC_bill_submit')
        self.assertFalse(s.passes(one(proposal,'visible')))
        s.flags.update({'ROC_ce_program_done','ROC_ce_industry_unlocked'})
        s.effect('ROC_ce_start_industry')
        self.assertEqual(s.vars['ROC_ce_project_id'],1)
        self.assertEqual(s.vars['ROC_ce_expected'],0)
        self.assertNotIn('ROC_prewar_completed_gaizaojingjidezhunbei',s.flags)

    def test_public_policy_helpers_display_only_their_localized_effect_summary(self):
        effects=dict(read_script('common/scripted_effects/ROC_scripted_effects.txt'))
        expected={
            'ROC_ce_policy_public':{'ROC_ma_left_favor':12,'ROC_ma_right_favor':-4},
            'ROC_ce_policy_market':{'ROC_ma_right_favor':8,'ROC_ma_left_favor':-8},
            'ROC_ce_focus_contribution':{'ROC_ce_pressure':-3},
        }
        for name,changes in expected.items():
            self.assertEqual({k for k,v in effects[name]},{'custom_effect_tooltip','hidden_effect'})
            self.assertEqual(one(effects[name],'custom_effect_tooltip'),name+'_tt')
            s=self.state();s.vars['ROC_ce_pressure']=40
            before=dict(s.vars);s.effect(name)
            for variable,delta in changes.items():self.assertEqual(s.vars[variable],before.get(variable,0)+delta)
            self.assertEqual(s.vars['ROC_ce_actual'],before['ROC_ce_actual'])

    def test_in_term_negotiations_reject_pending_meeting_and_successor(self):
        decisions=dict(economic_decisions())
        for kind in ('budget','personnel','policy'):
            block=one(decisions['ROC_ce_'+kind+'_negotiation'],'available')
            for condition in ('active','meeting','successor','expired'):
                s=self.state()
                if condition=='meeting':s.flags.add('ROC_econ_conference_pending')
                if condition=='successor':s.flags.add('ROC_econ_resignation_pending')
                if condition=='expired':s.missions.clear()
                self.assertEqual(s.passes(block),condition=='active',(kind,condition))


if __name__ == '__main__':
    unittest.main()
