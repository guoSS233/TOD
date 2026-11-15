"""Real production AST execution for sector/political separation and focus switch."""
import unittest
from test_roc_allied_parties import ROOT, one, read_script
from test_roc_economic_council import ScriptState
from test_roc_legislation import PEOPLE
from test_roc_economic_council_runtime_syntax import walk
from test_sichuan_red_opportunity import parse_localization

class SectorsAndTransition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.effects = dict(read_script("common/scripted_effects/ROC_scripted_effects.txt"))
        for directory in ('scripted_effects','scripted_triggers'):
            for name in ('ROC_economic_council','ROC_legislation','ROC_prewar_focus_memory','ROC_postwar_transition'):
                p=ROOT/'common'/directory/(name+'.txt')
                if p.exists():cls.effects.update(dict(read_script(str(p))))

    def state(self, person=0):
        s=ScriptState(self.effects)
        s.focuses.update({'gemingweiyuanhui','gaizaojingjidezhunbei'})
        s.ideas.add('ROC_idea_'+PEOPLE[person][1])
        s.missions['ROC_decision_bop_jingjidahui']=1000
        s.run(self.effects['ROC_econ_refresh'])
        return s

    def effect(self,s,name):
        self.assertTrue(name in self.effects,'missing production '+name)
        s.run(self.effects[name])

    def submit(self,s):
        self.effect(s,'ROC_bill_refresh_candidate')
        s.pp-=15
        self.effect(s,'ROC_bill_submit_effect')

    def test_political_sources_do_not_provide_sector_support(self):
        s=self.state()
        s.focuses.update({'jingchenghezuo','qianghuazhengzhituanjie'})
        s.flags.add('ROC_bill_rural_record')
        self.submit(s)
        self.effect(s,'ROC_bill_prepare_party')
        self.assertEqual(s.vars.get('ROC_bill_economic_support',-1),0)
        self.assertEqual(s.vars['ROC_bill_stage'],0)
        self.assertEqual(s.vars['ROC_bill_outcome'],3)
        self.assertEqual(s.pp,185)
        self.assertEqual(s.vars.get('ROC_econ_pending_shift',0),0)
        self.assertNotIn('ROC_legislation.12',s.events)

    def test_sector_policy_and_preparation_supply_independent_administration(self):
        for effect,cost,economic,administrative,outcome in (('materials',10,2,3,1),('signatures',20,3,2,1),('party',0,1,1,3)):
            s=self.state(1)
            s.focuses.add(PEOPLE[1][2])
            self.submit(s)
            self.effect(s,'ROC_bill_prepare_'+effect)
            self.assertEqual(s.pp,185-cost)
            self.assertEqual(s.vars.get('ROC_bill_economic_support',-1),economic)
            self.assertEqual(s.vars.get('ROC_bill_political_support',-1),administrative)
            self.assertEqual(s.vars['ROC_bill_support'],administrative)
            self.assertEqual(s.vars['ROC_bill_stage'],2)
            self.effect(s,'ROC_bill_vote')
            self.assertEqual(s.vars['ROC_bill_outcome'],outcome)

    def test_industry_agreement_and_administration_ignore_party_exit(self):
        s=self.state(1)
        s.flags.add('ROC_bill_rural_record')
        self.submit(s)
        self.effect(s,'ROC_bill_prepare_materials')
        self.assertEqual(s.vars.get('ROC_bill_economic_support',-1),1)
        self.assertEqual(s.vars.get('ROC_bill_political_support',-1),2)
        s.focuses.add('jixugeming')
        self.effect(s,'ROC_bill_refresh_support')
        self.assertEqual(s.vars['ROC_bill_economic_support'],1)
        self.assertEqual(s.vars['ROC_bill_political_support'],2)

    def test_old_open_hearing_migrates_without_new_cost_or_block(self):
        s=self.state()
        s.vars.update(ROC_bill_id=1,ROC_bill_stage=2,ROC_bill_days_left=20,ROC_bill_tactic=1,ROC_bill_support=1)
        s.focuses.add('qianghuazhengzhituanjie')
        self.effect(s,'ROC_bill_daily')
        self.assertGreaterEqual(s.vars.get('ROC_bill_economic_support',-1),1)
        self.assertEqual(s.vars['ROC_bill_political_support'],2)
        self.assertEqual(s.pp,200)
        self.effect(s,'ROC_bill_vote')
        self.assertEqual(s.vars['ROC_bill_stage'],3)

    def test_concession_exact_twenty_and_no_free_sector_pass(self):
        s=self.state()
        self.submit(s)
        s.pp=19
        self.effect(s,'ROC_bill_prepare_signatures')
        self.assertEqual(s.vars['ROC_bill_stage'],1)
        self.assertEqual(s.pp,19)
        s.pp=20
        self.effect(s,'ROC_bill_prepare_signatures')
        self.assertEqual(s.pp,0)
        self.assertEqual(s.vars['ROC_bill_economic_support'],2)
        self.assertEqual(s.vars['ROC_bill_stage'],2)

    def test_transition_retains_only_actual_completed_policy_and_all_runtime_state(self):
        s=self.state()
        s.cosmetic_tag='ROC_tongyi'
        s.focuses.update({PEOPLE[0][2],'qianghuazhengzhituanjie','jixugeming'})
        s.vars.update(ROC_econ_pending_shift=.12,ROC_bill_id=1,ROC_bill_stage=3)
        s.decisions.add('ROC_econ_yu_pilot')
        s.missions.update(ROC_decision_zuopai=30,ROC_decision_zhongpai=40,ROC_decision_youpai=50)
        s.decisions.update({'ROC_decision_zuoxiantuoxie','ROC_decision_youxiantuoxie'})
        before=(s.pp,s.stability,dict(s.vars),set(s.ideas))
        self.effect(s,'ROC_enter_postwar_tree')
        self.assertEqual(s.loaded_trees,['ROC_datong_postwar'])
        self.assertEqual((s.pp,s.stability,{k:v for k,v in s.vars.items() if not k.startswith('ROC_committee_')},s.ideas),before)
        self.assertEqual(s.vars['ROC_committee_left_agenda'],0)
        self.assertEqual(s.missions,{'ROC_decision_bop_jingjidahui':1000})
        self.assertEqual(s.decisions,{'ROC_econ_yu_pilot'})
        self.assertIn('ROC_prewar_completed_'+PEOPLE[0][2],s.flags)
        self.assertNotIn('ROC_prewar_completed_jingchenghezuo',s.flags)
        self.assertTrue(s.passes([('ROC_has_gemingweiyuanhui','yes')]))
        self.assertTrue(s.passes([('ROC_econ_left_allies_present','yes')]))
        self.assertTrue(s.passes([('ROC_bill_valid','yes')]))
        self.assertFalse(s.passes([('ROC_econ_race_active','yes')]))
        self.effect(s,'ROC_enter_postwar_tree')
        self.assertEqual(len(s.loaded_trees),1)

    def test_transition_country_and_unification_gates_and_old_save_entry(self):
        for tag,cosmetic,expected in (('ROC',None,0),('SRC','ROC_tongyi',0),('ROC','ROC_tongyi',1)):
            s=self.state();s.tag=tag;s.cosmetic_tag=cosmetic
            self.effect(s,'ROC_enter_postwar_tree')
            self.assertEqual(len(s.loaded_trees),expected)

    def test_unification_entry_and_daily_migration_are_wired(self):
        p=(ROOT/'common/decisions/MNG.txt').read_text(encoding='utf-8-sig')
        branch=p[p.index('limit = { tag = ROC }'):p.index('limit = { tag = SIC',p.index('limit = { tag = ROC }'))]
        self.assertIn('ROC_enter_postwar_tree = yes',branch)
        self.assertIn('mingcivwar.1005',branch)
        daily=one(one(read_script('common/on_actions/ROC_economic_council.txt'),'on_actions'),'on_daily_ROC')
        country=one(one(daily,'effect'),'ROC')
        self.assertIn(('ROC_enter_postwar_tree','yes'),country)
        self.assertFalse(any(key=='ROC_enter_postwar_tree' for key,_ in daily))

    def test_submit_initializes_both_support_layers_before_opening_window(self):
        s=self.state()
        s.focuses.update({PEOPLE[0][2],'qianghuazhengzhituanjie'})
        s.flags.add('ROC_bill_rural_record')
        self.submit(s)
        self.assertEqual(s.vars['ROC_bill_economic_support'],1)
        self.assertEqual(s.vars['ROC_bill_political_support'],1)

    def test_written_execution_guarantee_distinguishes_concession(self):
        for policy,preparation,can in ((False,'materials',False),(False,'signatures',True),(True,'materials',True)):
            s=self.state()
            if policy:s.focuses.add(PEOPLE[0][2])
            self.submit(s);self.effect(s,'ROC_bill_prepare_'+preparation)
            before=s.pp
            self.effect(s,'ROC_bill_conditional')
            self.assertEqual(s.vars['ROC_bill_stage'],3 if can else 0)
            self.assertEqual(s.pp,before-20 if can else before)

    def test_high_industry_materials_cannot_replace_fiscal_readiness(self):
        s=self.state();s.focuses.add(PEOPLE[0][2])
        self.submit(s);self.effect(s,'ROC_bill_prepare_signatures')
        self.assertEqual(s.vars['ROC_bill_economic_support'],3)
        self.assertEqual(s.vars['ROC_bill_support'],2)
        # Administrative supervision raises the real threshold independently of faction pressure.
        s.flags.add('ROC_bill_supervision')
        self.effect(s,'ROC_bill_refresh_support')
        self.assertEqual(s.vars['ROC_bill_requirement'],3)
        before=s.pp;self.effect(s,'ROC_bill_vote')
        self.assertEqual(s.vars['ROC_bill_stage'],0)
        self.assertEqual(s.vars['ROC_bill_outcome'],3)
        self.assertEqual(s.pp,before)

    def test_postwar_war_hooks_and_mission_activation_stay_stopped(self):
        daily=one(one(read_script('common/on_actions/ROC.txt'),'on_actions'),'on_daily_ROC')
        country=next(value for key,value in one(daily,'effect') if key=='ROC')
        first=country[:2]
        self.assertEqual([key for key,_ in first],['ROC_ce_retire_bop','ROC_committee_refresh_timing'])
        for war in (False,True):
            s=self.state();s.at_war=war;s.flags.add('ROC_postwar_active')
            s.vars['ROC_sanpai_time_war_var']=0 if war else 50
            before=dict(s.missions);s.run(first)
            self.assertEqual(s.missions,before)
            self.assertEqual(s.vars["ROC_sanpai_time_war_var"],0)
            self.assertFalse(s.events)
        race=one(read_script('common/decisions/ROC.txt'),'ROC_focus_sanpai')
        for name in ('ROC_decision_zuopai','ROC_decision_zhongpai','ROC_decision_youpai'):
            s=self.state();s.flags.add('ROC_postwar_active')
            self.assertFalse(s.passes(one(one(race,name),'activation')))

    def test_unlocked_advisors_keep_real_history_and_visible_flags_are_localized(self):
        names=['jizhidehuoli','yuanjulihuoliyazhi','qianghuatezhongzuozhan','xiandaihuadesanbingzuozhanlinian','hailujiezaiwomentiankongzhixia']
        characters=(ROOT/'common/characters/ROC.txt').read_text(encoding='utf-8-sig')
        localized,duplicates=parse_localization((ROOT/'localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml').read_bytes())
        self.assertEqual([key for key in duplicates if key.startswith("ROC_prewar_completed_")],[])
        for focus in names:
            self.assertIn('ROC_has_'+focus+' = yes',characters)
            s=self.state();s.cosmetic_tag='ROC_tongyi';s.focuses.add(focus)
            self.effect(s,'ROC_enter_postwar_tree')
            self.assertTrue(s.passes([('ROC_has_'+focus,'yes')]))
            self.assertIn('ROC_prewar_completed_'+focus,localized)
        for name,_ in read_script('common/scripted_triggers/ROC_prewar_focus_memory.txt'):
            self.assertIn('ROC_prewar_completed_'+name.removeprefix('ROC_has_'),localized)
        self.assertIn('ROC_postwar_active',localized)

    def test_stage_one_text_uses_sector_representatives_not_political_partner(self):
        values,_=parse_localization((ROOT/'localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml').read_bytes())
        for group in range(1,6):
            text=values[f'ROC_legislation.{group}1.d']
            self.assertNotIn('_partner]',text)
            self.assertNotIn('友党',text)
            self.assertTrue(any(word in text for word in ('行业','农业','工业','工厂','厂方','农户')))
            self.assertNotIn('大同会内的反对者',text)
        scripted=str(read_script('common/scripted_localisation/ROC_scripted_localisation.txt'))
        self.assertIn('ROC_legislation_readiness_sector',scripted)

if __name__=='__main__':unittest.main()
