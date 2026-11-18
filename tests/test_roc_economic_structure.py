"""Execute the ordinary economic structure controller and preserve unrelated state."""
import unittest
from test_roc_allied_parties import economic_decisions, ROOT, one, read_script
from test_roc_central_economy import CentralState


IDEAS = {'ROC_ce_structure_mixed'} | {f'ROC_ce_structure_{side}_{level}' for side in ('market','public') for level in (1,2,3)}


class PolicyState(CentralState):
    def __init__(self, **variables):
        super().__init__(**variables)
        path=ROOT/'common/scripted_effects/ROC_scripted_effects.txt'
        if path.exists():self.effects.update(dict(read_script(str(path))))
        self.effects.update(dict(read_script('common/scripted_effects/ROC_scripted_effects.txt')))
        self.exists=True
        self.emulate_native_callback=False

    def run(self,block):
        rewritten=[]
        for key,value in block:
            rewritten.append((key,value))
            if key=='remove_power_balance' and self.emulate_native_callback:
                rewritten.extend([('set_variable',[('VAR_ROC_jianshe_pp_factor','1')]),('set_variable',[('VAR_ROC_jianshe_days_factor','1')])])
        super().run(rewritten)

    def effect(self,name):
        assert name in self.effects, 'missing production economic structure effect '+name
        super().effect(name)


class EconomicStructure(unittest.TestCase):
    def state(self, **variables):
        s=PolicyState(**variables);s.bop=False
        return s

    def test_all_seven_tiers_have_exact_boundaries_and_only_one_country_modifier(self):
        for axis,tier in [(-100,-3),(-75.001,-3),(-75,-2),(-50.001,-2),(-50,-1),(-25.001,-1),(-25,0),(0,0),(25,0),(25.001,1),(50,1),(50.001,2),(75,2),(75.001,3),(100,3)]:
            s=self.state(ROC_ce_policy_axis=axis)
            s.flags.add('ROC_ce_policy_migrated');s.ideas.update(IDEAS)
            s.effect('ROC_ce_policy_refresh')
            self.assertEqual(s.vars['ROC_ce_policy_tier'],tier,axis)
            self.assertEqual(s.vars['ROC_ce_policy_needle_x'],round(245 + axis * 1.75))
            expected='ROC_ce_structure_mixed' if tier==0 else f"ROC_ce_structure_{'market' if tier<0 else 'public'}_{abs(tier)}"
            self.assertEqual(s.ideas & IDEAS,{expected})

    def test_country_modifiers_equal_all_seven_original_native_range_bonuses(self):
        path=ROOT/'common/ideas/ROC_economic_structure.txt'
        self.assertTrue(path.exists(),'ordinary economic modifiers must be defined')
        ideas=dict(one(one(read_script(str(path)),'ideas'),'country'))
        expected={
            'mixed':{'stability_factor':'0.03','political_power_factor':'0.05'},
            'market_1':{'production_speed_buildings_factor':'0.05','local_resources_factor':'0.03','research_speed_factor':'0.02'},
            'market_2':{'production_speed_buildings_factor':'0.08','local_resources_factor':'0.05','research_speed_factor':'0.04','war_support_factor':'-0.03'},
            'market_3':{'production_speed_buildings_factor':'0.12','local_resources_factor':'0.08','research_speed_factor':'0.06','war_support_factor':'-0.06'},
            'public_1':{'industrial_capacity_factory':'0.05'},
            'public_2':{'industrial_capacity_factory':'0.08','production_factory_max_efficiency_factor':'0.03','production_factory_efficiency_gain_factor':'0.03','stability_factor':'-0.03'},
            'public_3':{'industrial_capacity_factory':'0.12','production_factory_max_efficiency_factor':'0.05','production_factory_efficiency_gain_factor':'0.05','stability_factor':'-0.06'},
        }
        for key,modifier in expected.items():self.assertEqual(dict(one(ideas['ROC_ce_structure_'+key],'modifier')),modifier)

    def test_extreme_legacy_construction_multipliers_reset_on_crossing_tiers(self):
        s=self.state(ROC_VAR_nongcun_pp_base=30,ROC_VAR_nongcun_days_base=90)
        for axis,days,pp in [(-80,1.5,1),(80,1,1.5),(0,1,1),(-75,1,1),(75,1,1)]:
            s.vars['ROC_ce_policy_axis']=axis;s.effect('ROC_ce_policy_refresh')
            self.assertEqual(s.vars['VAR_ROC_jianshe_days_factor'],days)
            self.assertEqual(s.vars['VAR_ROC_jianshe_pp_factor'],pp)
            self.assertEqual(s.vars['ROC_VAR_nongcun_pp'],30*pp)
            self.assertEqual(s.vars['ROC_VAR_nongcun_days'],90*days)

    def test_migration_copies_native_value_and_old_backlog_before_retirement_once(self):
        s=self.state(ROC_econ_pending_shift=.12,ROC_ce_actual=17,ROC_ce_expected=22,ROC_ce_pressure=18,ROC_ce_project_id=2,ROC_ce_project_progress=43,ROC_ce_datong_attitude=20,ROC_ce_labor_attitude=3,ROC_ce_socialist_attitude=-8,ROC_ce_democratic_attitude=50)
        s.flags.add('ROC_ce_initialized');s.bop=True;s.axis=-.8
        s.missions.update(ROC_decision_zuopai=17,ROC_decision_zhongpai=28,ROC_decision_youpai=39)
        before=dict(s.missions)
        s.effect('ROC_ce_retire_bop')
        self.assertFalse(s.bop)
        self.assertEqual(s.vars['ROC_ce_policy_axis'],-80)
        self.assertEqual(s.vars['ROC_ce_policy_pending'],12)
        s.effect('ROC_ce_retire_bop')
        self.assertEqual(s.vars['ROC_ce_policy_pending'],12)
        self.assertEqual(s.missions,before)
        for key,value in {'actual':17,'expected':22,'pressure':18,'project_id':2,'project_progress':43,'datong_attitude':20,'labor_attitude':3,'socialist_attitude':-8,'democratic_attitude':50}.items():self.assertEqual(s.vars['ROC_ce_'+key],value)

    def test_already_centralized_save_without_native_value_starts_mixed_and_keeps_pending(self):
        s=self.state(ROC_econ_pending_shift=-.05,ROC_ce_policy_pending=4)
        s.flags.add('ROC_ce_initialized');s.effect('ROC_ce_policy_initialize')
        self.assertEqual(s.vars['ROC_ce_policy_axis'],0)
        self.assertEqual(s.vars['ROC_ce_policy_pending'],-1)
        s.effect('ROC_econ_queue_shift');s.effect('ROC_econ_refresh')
        self.assertEqual(s.vars['ROC_ce_policy_pending'],-1)

    def test_every_legacy_amplitude_queues_exact_points_without_double_attitude_or_delivery(self):
        for side,sign,amounts in [('public',1,[2,3,4,5,6,8]),('market',-1,[2,3,5,6,8])]:
            for amount in amounts:
                s=self.state();s.effect('ROC_ce_initialize');before=dict(s.vars)
                s.effect(f'ROC_econ_shift_{side}_{amount*10:03d}')
                self.assertEqual(s.vars['ROC_ce_policy_pending'],sign*amount)
                self.assertEqual(s.vars['ROC_ce_policy_axis'],0)
                self.assertEqual(s.vars['ROC_ce_actual'],0)
                variable='ROC_ma_left_favor' if side=='public' else 'ROC_ma_right_favor'
                self.assertEqual(s.vars[variable],before[variable]+(12 if side=='public' else 8))

    def test_monthly_rate_clamp_endpoints_and_queue_cap(self):
        for axis,pending,expected_axis,expected_pending in [(0,8,1,7),(0,-8,-1,-7),(99.5,8,100,0),(-99.5,-8,-100,0),(100,-8,99,-7),(-100,8,-99,7)]:
            s=self.state(ROC_ce_policy_axis=axis,ROC_ce_policy_pending=pending);s.flags.add('ROC_ce_policy_migrated')
            before=dict(s.missions);s.effect('ROC_ce_policy_apply_monthly')
            self.assertEqual(s.vars['ROC_ce_policy_axis'],expected_axis)
            self.assertEqual(s.vars['ROC_ce_policy_pending'],expected_pending)
            self.assertEqual(s.missions,before)
        s=self.state();s.effect('ROC_ce_policy_initialize')
        for _ in range(8):s.effect('ROC_econ_shift_public_080')
        self.assertEqual(s.vars['ROC_ce_policy_pending'],30)

    def test_no_modifier_or_monthly_progress_before_administration_or_without_country(self):
        for inactive in ('country','administration'):
            s=self.state(ROC_ce_policy_pending=10)
            if inactive=='country':s.exists=False
            else:s.focuses.clear()
            s.effect('ROC_ce_policy_initialize');s.effect('ROC_ce_policy_apply_monthly')
            self.assertFalse(s.ideas & IDEAS)
            self.assertEqual(s.vars.get('ROC_ce_policy_axis',0),0)
            self.assertEqual(s.vars['ROC_ce_policy_pending'],10)

    def test_yan_settlements_move_projected_structure_toward_mixed_with_original_caps(self):
        for stage,cap in [('pilot',2),('expansion',3)]:
            for axis,pending in [(40,8),(-40,-8),(1,0),(-1,0),(0,0)]:
                s=self.state(ROC_ce_policy_axis=axis,ROC_ce_policy_pending=pending)
                s.flags.add('ROC_ce_policy_migrated')
                s.effect(f'ROC_econ_yan_{stage}_settlement')
                adjustment=max(-cap,min(cap,-axis-pending))
                self.assertEqual(s.vars['ROC_ce_policy_pending'],pending+adjustment)
                self.assertEqual(s.vars.get('ROC_ce_actual',0),0)

    def test_business_entries_capture_native_structure_then_retire_without_waiting_for_daily(self):
        for entry in ('industry','agriculture','transport','budget','personnel','policy'):
            s=PolicyState();s.bop=True;s.axis=.67
            s.flags.update({'ROC_ce_program_done','ROC_ce_industry_unlocked','ROC_ce_agriculture_unlocked','ROC_ce_transport_unlocked'})
            if entry in ('industry','agriculture','transport'):s.effect('ROC_ce_start_'+entry)
            else:
                decisions=dict(economic_decisions())
                s.run(one(decisions['ROC_ce_'+entry+'_negotiation'],'complete_effect'))
            self.assertFalse(s.bop,entry)
            self.assertEqual(s.vars['ROC_ce_policy_axis'],67,entry)
            self.assertEqual(s.vars['ROC_ce_actual'],0,entry)

    def test_single_wrong_country_idea_self_heals_even_with_matching_applied_tier(self):
        s=self.state(ROC_ce_policy_axis=80,ROC_ce_policy_applied_tier=3)
        s.flags.update({'ROC_ce_policy_migrated','ROC_ce_policy_effects_active'})
        s.ideas.add('ROC_ce_structure_market_3')
        s.effect('ROC_ce_policy_refresh')
        self.assertEqual(s.ideas & IDEAS,{'ROC_ce_structure_public_3'})

    def test_retirement_reasserts_construction_multiplier_after_legacy_native_callback(self):
        s=self.state();s.bop=True;s.axis=-.8;s.emulate_native_callback=True
        s.effect('ROC_ce_retire_bop')
        self.assertEqual(s.vars['VAR_ROC_jianshe_days_factor'],1.5)
        self.assertEqual(s.vars['VAR_ROC_jianshe_pp_factor'],1)


if __name__=='__main__':unittest.main()
