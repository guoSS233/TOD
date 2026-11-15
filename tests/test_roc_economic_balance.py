"""The ordinary economic axis retains committee timing without native callbacks."""
import unittest
from test_roc_allied_parties import economic_decisions, ROOT, one, read_script
from test_roc_economic_council import ScriptState
from test_roc_economic_council_runtime_syntax import walk

class RocEconomy(unittest.TestCase):
    def test_political_time_includes_each_applied_axis_offset_once(self):
        effects=dict(read_script('common/scripted_effects/ROC_scripted_effects.txt'))
        for offset in (-15,-10,-5,0,5,10,15):
            s=ScriptState(effects,ROC_sanpai_time_base_var=50,ROC_sanpai_time_war_var=50,ROC_sanpai_time_minister_zuo_var=5,ROC_sanpai_time_minister_you_var=-7,ROC_sanpai_time_minister_zhong_var=11,ROC_sanpai_time_bop_zuo_var=offset,ROC_sanpai_time_bop_you_var=-offset)
            s.run(effects['ROC_scripted_effects_sanpai_time'])
            self.assertEqual(s.vars['ROC_zuopai_time_var'],105+offset)
            self.assertEqual(s.vars['ROC_youpai_time_var'],93-offset)
            self.assertEqual(s.vars['ROC_zhongpai_time_var'],111)

    def test_inert_legacy_definition_has_no_modifiers_callbacks_or_entry_category(self):
        bop=one(read_script('common/bop/ROC_bop.txt'),'ROC_power_balance')
        self.assertFalse(any(k in {'modifier','on_activate','on_deactivate','decision_category'} for k,v in walk(bop)))
        ranges=[v for k,v in walk(bop) if k=='range']
        self.assertEqual(len(ranges),7)

    def test_monthly_political_extremism_has_no_economic_axis_input(self):
        actions=one(read_script('common/on_actions/ROC.txt'),'on_actions')
        monthly=one(actions,'on_monthly_ROC')
        self.assertNotIn('ROC_flag_bop',str(monthly))
        self.assertNotIn('ROC_VAR_youyi_base',str(monthly))
        self.assertNotIn('ROC_VAR_zuoyi_base',str(monthly))

    def test_economy_and_committee_use_separate_ordinary_categories(self):
        categories=dict(read_script('common/decisions/categories/ROC.txt'))
        self.assertNotIn('ROC_balance_of_power_category',categories)
        self.assertEqual(one(categories['ROC_economic_administration'],'scripted_gui'),'ROC_central_economy_window')
        self.assertEqual(one(categories['ROC_economic_administration'],'visible'), [('ROC_ce_administration_active','yes')])
        self.assertEqual(one(categories['ROC_focus_sanpai'],'scripted_gui'),'ROC_economic_council_window')
        self.assertEqual(one(categories['ROC_focus_sanpai'],'visible'), [('ROC_has_gemingweiyuanhui','yes')])
        groups = read_script('common/decisions/ROC.txt')
        expected_economy = {
            'ROC_ce_industry_project', 'ROC_ce_agriculture_project', 'ROC_ce_transport_project',
            'ROC_ce_budget_negotiation', 'ROC_ce_personnel_negotiation', 'ROC_ce_policy_negotiation',
            'ROC_allied_worker_coordination', 'ROC_allied_rural_cooperation',
            'ROC_allied_labor_arbitration', 'ROC_allied_commercial_credit', 'ROC_bill_submit',
        }
        placements = {name: category for category, block in groups for name, value in block
                      if name in expected_economy}
        self.assertEqual(set(placements), expected_economy)
        self.assertEqual(set(placements.values()), {'ROC_economic_administration'})
        council_groups=dict(groups)
        self.assertIn('ROC_focus_sanpai', council_groups)
        self.assertEqual(
            {key for key,value in council_groups['ROC_focus_sanpai']},
            {'ROC_decision_zuopai','ROC_decision_zhongpai','ROC_decision_youpai',
             'ROC_decision_zuoxiantuoxie','ROC_decision_youxiantuoxie'},
        )

    def test_six_existing_policies_keep_busy_and_administration_guards_without_axis(self):
        effects=dict(read_script('common/scripted_triggers/ROC_economic_council.txt'))
        decisions=economic_decisions()
        policies={k:v for k,v in decisions if k.startswith(('ROC_decision_bop_left_','ROC_decision_bop_right_'))}
        self.assertEqual(len(policies),6)
        routes={
            'ROC_decision_bop_left_fcsyqy':(1,'ROC_ma_yu_1'),
            'ROC_decision_bop_left_jqmysc':(2,'ROC_ma_yan_2'),
            'ROC_decision_bop_left_clgq':(5,'ROC_ma_xiao_step4'),
            'ROC_decision_bop_right_qhgh':(4,'ROC_ma_chen_1'),
            'ROC_decision_bop_right_ssjm':(3,'ROC_ma_ruan_1'),
            'ROC_decision_bop_right_sqgyh':(3,'ROC_ma_ruan_2'),
        }
        for ident,block in policies.items():
            profile,route=routes[ident]
            s=ScriptState(effects,ROC_ce_minister_profile_id=profile);s.focuses.update({'gaizaojingjidezhunbei',route})
            s.bop=False
            self.assertTrue(s.passes(one(block,'available')),ident)
            s.decisions={next(iter(policies))}
            self.assertFalse(s.passes(one(block,'available')),ident)
            s.decisions.clear();s.focuses.clear()
            self.assertTrue(s.passes(one(block,'cancel_trigger')),ident)
            self.assertNotIn('power_balance_value',str(block))

    def test_old_building_multiplier_is_normalized_on_adoption_only(self):
        from test_roc_central_economy import CentralState
        s=CentralState(VAR_ROC_jianshe_pp_factor=1.5,VAR_ROC_jianshe_days_factor=1.5)
        s.initialize()
        self.assertEqual(s.vars['VAR_ROC_jianshe_pp_factor'],1)
        self.assertEqual(s.vars['VAR_ROC_jianshe_days_factor'],1)

if __name__ == '__main__':unittest.main()
