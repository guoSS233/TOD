"""Execute actual three-faction bookkeeping across appointments."""
import unittest
from test_roc_central_economy import CentralState
from test_roc_allied_parties import named_event, one, read_script
PARTIES=('left','center','right')
MINISTERS=('YuShude','YanYangchu','RuanXiaoxian','ChenZanxian','XiaoZheng')
BASES=((55,70,40),(45,70,55),(70,50,25),(80,40,15),(20,50,80))
class MinisterProfiles(unittest.TestCase):
    def state(self,minister,**variables):
        s=CentralState(**variables);s.ideas.add('ROC_idea_'+minister);s.initialize();return s
    def favors(self,s):return tuple(s.vars.get('ROC_ma_'+p+'_favor',0) for p in PARTIES)
    def replace(self,s,minister):
        s.effect('ROC_econ_remove_ministers');s.ideas.add('ROC_idea_'+minister);s.effect('ROC_econ_refresh_minister')
    def choose_agenda(self,s,slug,event_id,option):
        s.effect(f'ROC_ma_open_{slug}_1')
        event=named_event(read_script('events/ROC_minister_agenda.txt'),f'ROC_minister_agenda.{event_id}')
        choice=next(v for k,v in event if k=='option' and one(v,'name').endswith('.'+option))
        self.assertTrue(s.passes(one(choice,'trigger')))
        s.run(one(choice,'hidden_effect'))
    def test_five_appointments_have_distinct_intrinsic_favors(self):
        for minister,expected in zip(MINISTERS,BASES):self.assertEqual(self.favors(self.state(minister)),expected)
    def test_negotiations_survive_replacements_and_clamp_without_farming(self):
        s=self.state('YuShude');s.vars['ROC_ma_left_favor']+=100;s.effect('ROC_ce_refresh');s.effect('ROC_ce_policy_market')
        for _ in range(3):
            self.replace(s,'XiaoZheng');self.assertEqual(self.favors(s),(57,50,88))
            self.replace(s,'YuShude');self.assertEqual(self.favors(s),(92,70,48))
        self.assertEqual(s.vars['ROC_ma_left_delta'],37)
    def test_initialized_legacy_profile_migrates_negotiation_once(self):
        s=CentralState(ROC_ce_labor_relation_delta=20,ROC_ce_socialist_relation_delta=12,ROC_ce_datong_relation_delta=-10,ROC_ce_democratic_relation_delta=8)
        s.flags.update({'ROC_ce_initialized','ROC_ce_minister_profiles_initialized'});s.ideas.add('ROC_idea_RuanXiaoxian');s.initialize()
        self.assertEqual(self.favors(s),(78,45,29))
        before=dict(s.vars);s.initialize();self.assertEqual(s.vars,before)
    def test_switch_preserves_term_project_economic_structure_and_committee(self):
        s=self.state('YuShude');s.vars.update(ROC_ce_actual=34,ROC_ce_expected=55,ROC_ce_project_id=1,ROC_ce_project_progress=67,ROC_ce_policy_axis=60,ROC_ce_policy_pending=-9,ROC_committee_session_days=12)
        before={k:v for k,v in s.vars.items() if k.startswith(('ROC_ce_project','ROC_ce_actual','ROC_ce_expected','ROC_ce_policy_','ROC_committee'))}
        self.replace(s,'YanYangchu');self.assertEqual({k:s.vars[k] for k in before},before);self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'],700)
    def test_vacancy_does_not_discard_negotiations_within_successors_range(self):
        s=self.state('RuanXiaoxian')
        s.vars['ROC_ma_left_favor']=0;s.effect('ROC_ce_refresh')
        self.replace(s,'ChenZanxian')
        self.assertEqual(s.vars['ROC_ma_left_favor'],10)
        for _ in range(3):s.effect('ROC_ce_refresh')
        self.assertEqual(s.vars['ROC_ma_left_favor'],10)
    def test_pre_profile_legacy_save_reads_four_old_attitudes_once(self):
        s=CentralState(ROC_ce_labor_attitude=20,ROC_ce_socialist_attitude=22,
                       ROC_ce_datong_attitude=10,ROC_ce_democratic_attitude=8)
        s.flags.add('ROC_ce_initialized');s.ideas.add('ROC_idea_RuanXiaoxian');s.initialize()
        self.assertEqual(self.favors(s),(78,45,29))
        s.vars.update(ROC_ce_labor_attitude=100,ROC_ce_socialist_attitude=100,
                      ROC_ce_datong_attitude=100,ROC_ce_democratic_attitude=100)
        s.initialize();self.assertEqual(self.favors(s),(78,45,29))
    def test_cap_does_not_bank_invisible_goodwill_or_negative_debt(self):
        s=self.state('YuShude')
        s.vars['ROC_ma_right_favor']=200;s.effect('ROC_ce_refresh')
        self.assertEqual(s.vars['ROC_ma_right_favor'],100)
        before=s.vars['ROC_ma_right_delta']
        s.vars['ROC_ma_right_favor']+=5;s.effect('ROC_ce_refresh')
        self.assertEqual(s.vars['ROC_ma_right_delta'],before)
        s.vars['ROC_ma_right_favor']=-100;s.effect('ROC_ce_refresh')
        self.assertEqual(s.vars['ROC_ma_right_favor'],0)
        before=s.vars['ROC_ma_right_delta']
        s.vars['ROC_ma_right_favor']-=5;s.effect('ROC_ce_refresh')
        self.assertEqual(s.vars['ROC_ma_right_delta'],before)
        s.vars['ROC_ma_right_favor']+=5;s.effect('ROC_ce_refresh')
        self.assertEqual(s.vars['ROC_ma_right_favor'],5)
    def test_cost_after_switch_to_higher_base_leaves_visible_cap(self):
        for side,initial,successor in (
                ('left','RuanXiaoxian','ChenZanxian'),
                ('center','XiaoZheng','YuShude'),
                ('right','ChenZanxian','XiaoZheng')):
            with self.subTest(side=side):
                s=self.state(initial)
                s.vars[f'ROC_ma_{side}_favor']=100;s.effect('ROC_ce_refresh')
                self.replace(s,successor)
                self.assertEqual(s.vars[f'ROC_ma_{side}_favor'],100)
                if side=='left':
                    self.choose_agenda(s,'chen',41,'a')
                else:
                    s.vars['ROC_ce_project_id']=1;s.flags.add('ROC_ce_event_4_pending')
                    s.choose(4,'c')
                self.assertEqual(s.vars[f'ROC_ma_{side}_favor'],90)
                after=self.favors(s)
                for _ in range(3):s.effect('ROC_ce_refresh')
                self.assertEqual(self.favors(s),after)
    def test_gain_after_switch_to_lower_base_leaves_visible_floor(self):
        for side,initial,successor,slug,event in (
                ('left','RuanXiaoxian','XiaoZheng',None,None),
                ('center','YuShude','XiaoZheng','xiao',51),
                ('right','XiaoZheng','YuShude','yu',11)):
            with self.subTest(side=side):
                s=self.state(initial)
                s.vars[f'ROC_ma_{side}_favor']=0;s.effect('ROC_ce_refresh')
                self.replace(s,successor)
                self.assertEqual(s.vars[f'ROC_ma_{side}_favor'],0)
                if side=='left':s.effect('ROC_econ_yan_pilot_settlement')
                else:self.choose_agenda(s,slug,event,'b')
                self.assertEqual(s.vars[f'ROC_ma_{side}_favor'],5)
                after=self.favors(s)
                for _ in range(3):s.effect('ROC_ce_refresh')
                self.assertEqual(self.favors(s),after)
    def test_changes_during_vacancy_leave_visible_caps(self):
        for side,minister,start,effect,visible,next_minister,next_visible in (
                ('left','ChenZanxian',0,'ROC_econ_yan_pilot_settlement',5,'RuanXiaoxian',25),
                ('center','YuShude',0,'ROC_econ_help_center',1,'YuShude',21),
                ('right','ChenZanxian',100,'ROC_ma_delay_committee_right',85,'YuShude',75)):
            with self.subTest(side=side):
                s=self.state(minister)
                s.vars[f'ROC_ma_{side}_favor']=start;s.effect('ROC_ce_refresh')
                s.effect('ROC_econ_remove_ministers')
                s.flags.add('ROC_econ_resignation_pending');s.focuses.add('gemingweiyuanhui')
                s.missions['ROC_decision_youpai']=50
                self.assertEqual(s.vars[f'ROC_ma_{side}_favor'],start)
                s.effect(effect)
                self.assertEqual(s.vars[f'ROC_ma_{side}_favor'],visible)
                if side=='right':self.assertEqual(s.missions['ROC_decision_youpai'],71)
                for _ in range(3):s.effect('ROC_ce_refresh')
                self.assertEqual(s.vars[f'ROC_ma_{side}_favor'],visible)
                s.ideas.add('ROC_idea_'+next_minister);s.effect('ROC_econ_refresh_minister')
                self.assertEqual(s.vars[f'ROC_ma_{side}_favor'],next_visible)
if __name__=='__main__':unittest.main()
