"""Regression coverage for the economic axis / head / committee migration boundary."""
import unittest
from test_roc_allied_parties import ROOT, one, read_script, read_event
import test_roc_economic_council as council
from test_roc_economic_council import ScriptState

HEADS = ['ROC_idea_DongBiwu','ROC_idea_TanPingshan','ROC_idea_Xuqian','ROC_idea_HuangYanpei']
OFFSETS = [(25,0,0),(5,-15,0),(0,-15,5),(0,0,25)]
MISSIONS = ['ROC_decision_zuopai','ROC_decision_zhongpai','ROC_decision_youpai']
MODIFIERS = ['ROC_sanpai_time_minister_zuo_var','ROC_sanpai_time_minister_zhong_var','ROC_sanpai_time_minister_you_var']

class Linkage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        council.EconomicCouncil.setUpClass();cls.effects=council.EconomicCouncil.effects

    def state(self,axis=0,head='ROC_idea_Xuqian',race=True):
        s=ScriptState(self.effects,ROC_ce_policy_axis=axis,ROC_sanpai_time_base_var=50)
        s.bop=False;s.flags.add('ROC_ce_policy_migrated')
        s.focuses.update({'guangzhouqiyi','gaizaojingjidezhunbei'})
        if race:s.focuses.add('gemingweiyuanhui')
        if head:s.ideas.add(head)
        return s

    def effect(self,s,name):
        self.assertIn(name,s.effects,'missing production controller '+name)
        s.run(s.effects[name])

    def timing(self,s):
        if 'ROC_committee_refresh_timing' in s.effects:
            self.effect(s,'ROC_committee_refresh_timing')
        else:
            hooks=one(read_script('common/on_actions/ROC.txt'),'on_actions')
            block=next(v for k,v in one(one(hooks,'on_daily_ROC'),'effect') if k=='ROC')
            s.run(block[:next(i for i,(k,v) in enumerate(block) if k=='set_variable')])

    def choose(self,s,event,choice):
        e=read_event('ROC_pingheng.'+str(event))
        option=next(v for k,v in e if k=='option' and one(v,'name').endswith('.'+choice))
        s.run([(k,v) for k,v in option if k not in ('name','ai_chance','trigger')])

    def days(self,s,n):
        for _ in range(n):self.effect(s,'ROC_econ_head_daily')

    def test_sixteen_head_changes_apply_exact_delta_and_repeated_refresh_is_inert(self):
        for old,old_offsets in zip(HEADS,OFFSETS):
            for new,new_offsets in zip(HEADS,OFFSETS):
                with self.subTest(old=old,new=new):
                    s=self.state(head=new);s.vars.update(zip(MODIFIERS,old_offsets));s.missions.update(zip(MISSIONS,[100,100,100]))
                    self.timing(s)
                    expected=dict(zip(MISSIONS,[100+n-o for n,o in zip(new_offsets,old_offsets)]))
                    self.assertEqual(s.missions,expected)
                    self.assertEqual(tuple(s.vars[v] for v in MODIFIERS),new_offsets)
                    for _ in range(5):self.timing(s)
                    self.assertEqual(s.missions,expected)
                    self.assertEqual(tuple(s.vars[v] for v in ('ROC_zuopai_time_var','ROC_zhongpai_time_var','ROC_youpai_time_var')),tuple(50+n for n in new_offsets))

    def test_vacancy_clears_old_head_impact_and_war_changes_all_clocks_once(self):
        s=self.state(head=None);s.vars.update(zip(MODIFIERS,OFFSETS[1]));s.missions.update(zip(MISSIONS,[100]*3))
        self.timing(s);self.assertEqual(list(s.missions.values()),[95,115,100])
        before=dict(s.missions);s.at_war=True;self.timing(s)
        self.assertEqual(s.missions,{k:v+50 for k,v in before.items()})
        self.timing(s);s.at_war=False;self.timing(s);self.assertEqual(s.missions,before)

    def test_axis_tiers_boundaries_change_existing_missions_by_difference(self):
        for axis,tier in [(-100,-3),(-75.01,-3),(-75,-2),(-50.01,-2),(-50,-1),(-25.01,-1),(-25,0),(0,0),(25,0),(25.01,1),(50,1),(50.01,2),(75,2),(75.01,3),(100,3)]:
            with self.subTest(axis=axis):
                s=self.state(axis,head=None);s.missions.update(zip(MISSIONS,[100]*3))
                self.effect(s,'ROC_ce_policy_refresh')
                expected=dict(zip(MISSIONS,[100+tier*5,100,100-tier*5]))
                self.assertEqual(s.missions,expected)
                for _ in range(4):self.effect(s,'ROC_ce_retire_bop')
                self.assertEqual(s.missions,expected)
                self.assertEqual(s.vars.get('ROC_zuopai_time_var',0),50+tier*5)
                self.assertEqual(s.vars.get('ROC_youpai_time_var',0),50-tier*5)
                s.vars['ROC_ce_policy_axis']=-axis;self.effect(s,'ROC_ce_policy_refresh')
                self.assertEqual(s.missions,dict(zip(MISSIONS,[100-tier*5,100,100+tier*5])))

    def test_native_migration_preserves_already_applied_axis_and_missing_native_applies_once(self):
        for native in (True,False):
            s=self.state(-80,head=None);s.missions.update(zip(MISSIONS,[20,30,40]))
            if native:
                s.bop=True;s.axis=-.8;s.flags.remove('ROC_ce_policy_migrated')
                s.vars.update(ROC_sanpai_time_bop_zuo_var=-15,ROC_sanpai_time_bop_you_var=15)
            self.effect(s,'ROC_ce_retire_bop')
            expected=dict(zip(MISSIONS,[20,30,40] if native else [5,30,55]))
            self.assertEqual(s.missions,expected)
            for _ in range(3):self.effect(s,'ROC_ce_retire_bop')
            self.assertEqual(s.missions,expected)

    def test_new_missions_include_head_axis_war_and_finished_race_never_reopens(self):
        s=self.state(80,HEADS[2]);s.at_war=True
        self.effect(s,'ROC_ce_retire_bop');self.effect(s,'ROC_committee_daily')
        self.assertEqual(s.missions,dict(zip(MISSIONS,[115,85,90])))
        s.focuses.add('jingchenghezuo');self.effect(s,'ROC_econ_finish_race')
        self.effect(s,'ROC_ce_policy_refresh');self.effect(s,'ROC_committee_daily')
        self.assertEqual(s.missions,{})

    def test_head_target_boundaries_same_head_and_zero_do_not_queue(self):
        for axis,target,head in [(0,0,None),(.01,1,HEADS[1]),(49.99,1,HEADS[1]),(50,2,HEADS[0]),(-.01,3,HEADS[2]),(-49.99,3,HEADS[2]),(-50,4,HEADS[3])]:
            s=self.state(axis,head);self.days(s,100)
            self.assertEqual(s.events,[])
            self.assertEqual(s.vars['ROC_econ_head_target'],target)
            self.assertEqual(s.vars['ROC_econ_head_mismatch_days'],0)

    def test_head_question_expires_before_native_auto_choice_and_cooldown_counts_down(self):
        s=self.state(80);self.days(s,90)
        event=read_event('ROC_pingheng.1002')
        self.assertGreater(int(one(event,'timeout_days')),s.flag_days['ROC_econ_head_pending'])
        for _ in range(14):
            for flag in list(s.flag_days):
                s.flag_days[flag]-=1
                if s.flag_days[flag]<=0:s.flags.discard(flag);s.flag_days.pop(flag)
            self.days(s,1)
        before=(set(s.ideas),s.stability)
        for choice in ('a','b'):self.choose(s,1002,choice)
        self.assertEqual((s.ideas,s.stability),before)
        self.assertEqual(s.flag_days['ROC_pingheng_head_cooldown'],346)
        s.flags.discard('ROC_pingheng_head_cooldown');self.days(s,89)
        self.assertEqual(len(s.events),1)
        self.days(s,1);self.assertEqual(len(s.events),2)
        s=self.state(80,head=None);self.days(s,100);self.assertFalse(s.events)

    def test_head_target_or_incumbent_change_and_agreement_reset_continuity(self):
        s=self.state(20,HEADS[2]);self.days(s,70)
        self.assertEqual(s.vars['ROC_econ_head_mismatch_days'],70)
        s.vars['ROC_ce_policy_axis']=50;self.days(s,1)
        self.assertEqual(s.vars['ROC_econ_head_mismatch_days'],1)
        self.days(s,30);s.ideas={HEADS[3]};self.days(s,1)
        self.assertEqual(s.vars['ROC_econ_head_mismatch_days'],1)
        s.vars['ROC_ce_policy_axis']=-50;self.days(s,1)
        self.assertEqual(s.vars['ROC_econ_head_mismatch_days'],0)
        s.vars['ROC_ce_policy_axis']=80;self.days(s,89);self.assertEqual(s.events,[])
        self.days(s,1);self.assertEqual(s.events,['ROC_pingheng.1002'])

    def test_initialize_preserves_head_continuity(self):
        s=self.state(80);self.days(s,89);self.effect(s,'ROC_ce_initialize');self.days(s,1)
        self.assertEqual(s.events,['ROC_pingheng.1002'])

    def test_legacy_cooldown_end_flags_story_heads_and_postwar_block_challenges(self):
        for flag in ('ROC_pingheng_economy_minister','ROC_pingheng_head_cooldown','ROC_pingheng_end','ROC_postwar_active'):
            s=self.state(80);s.flags.add(flag);self.days(s,100);self.assertEqual(s.events,[],flag)
        for head in ('ROC_idea_YangMingzhai','ROC_idea_TaoXingzhi'):
            s=self.state(80,head);self.days(s,100);self.assertEqual(s.events,[],head)

    def test_head_accept_reject_and_cooldown_preserve_minister_term_and_leader(self):
        for axis,event,head in [(20,1001,HEADS[1]),(50,1002,HEADS[0]),(-20,1003,HEADS[2]),(-50,1004,HEADS[3])]:
            for choice in ('a','b'):
                s=self.state(axis,HEADS[3] if axis>0 else HEADS[0]);s.ideas.add('ROC_idea_YuShude');s.missions['ROC_decision_bop_jingjidahui']=712
                self.days(s,90);self.assertEqual(s.events,['ROC_pingheng.'+str(event)])
                self.assertEqual(s.flag_days['ROC_pingheng_head_cooldown'],360)
                self.choose(s,event,choice)
                self.assertEqual(s.stability,.5 if choice=='a' else .45)
                if choice=='a':self.assertIn(head,s.ideas)
                self.assertIn('ROC_idea_YuShude',s.ideas);self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'],712)
                after=(set(s.ideas),s.stability);self.choose(s,event,choice);self.assertEqual((s.ideas,s.stability),after)
                self.days(s,100);self.assertEqual(len(s.events),1)

    def test_pending_stale_head_choices_are_inert_after_route_incumbent_expiry_or_end(self):
        for change in ('route','incumbent','expiry','end','postwar','agreement'):
            for choice in ('a','b'):
                s=self.state(80);self.days(s,90)
                if change=='route':s.vars['ROC_ce_policy_axis']=-80
                elif change=='incumbent':s.ideas={HEADS[3]}
                elif change=='expiry':s.flags.discard('ROC_econ_head_pending')
                elif change=='end':s.focuses.add('jingchenghezuo')
                elif change=='postwar':s.flags.add('ROC_postwar_active')
                else:s.ideas={HEADS[0]}
                before=(set(s.ideas),s.stability);self.choose(s,1002,choice)
                self.assertEqual((s.ideas,s.stability),before,change)

    def test_focus18b_queues_fifteen_toward_projected_center_and_monthly_stays_bounded(self):
        event=read_event('ROC_focus.18');option=next(v for k,v in event if k=='option' and one(v,'name')=='ROC_focus.18.b')
        for axis,ordinary,minister in [(50,8,3),(-50,-8,-3),(16,-10,-5),(-16,10,5),(15,0,0),(-15,0,0),(0,0,0)]:
            s=self.state(axis);self.effect(s,'ROC_ce_initialize');s.vars.update(ROC_ce_policy_pending=ordinary,ROC_ma_policy_pending=minister)
            favors=(s.vars['ROC_ma_left_favor'],s.vars['ROC_ma_center_favor'])
            s.flags.add('ROC_ma_policy_ledger_initialized')
            s.run([(k,v) for k,v in option if k!='name'])
            projected=axis+ordinary+minister
            delta=max(-15,min(15,-projected)) if abs(axis)>15 else 0
            self.assertEqual(s.vars['ROC_ce_policy_pending'],ordinary+delta)
            self.assertEqual(s.vars['ROC_ma_policy_pending'],minister)
            self.assertEqual(s.vars['ROC_ma_left_favor'],favors[0]+5);self.assertEqual(s.vars['ROC_ma_center_favor'],favors[1]+5)
            self.effect(s,'ROC_ce_policy_apply_monthly');self.assertLessEqual(abs(s.vars['ROC_ce_policy_axis']-axis),1)

    def test_legacy_radicalization_rewards_recompute_actual_modifiers(self):
        for event in list(range(27,41))+[46]:
            s=self.state();s.vars.update(ROC_VAR_youyi_base=.5,ROC_VAR_zuoyi_base=.5)
            e=read_event('ROC_pingheng.'+str(event));option=next(v for k,v in e if k=='option')
            s.run([(k,v) for k,v in option if k not in ('name','trigger','ai_chance')])
            right=min(1,max(0,.5+(1 if event==46 else -.04)))
            self.assertAlmostEqual(s.vars.get('ROC_dynamic_modifier_st',0),(right-.5)*-.2,msg=str(event))
            self.assertAlmostEqual(s.vars.get('ROC_dynamic_modifier_st_zuo',0),0,msg=str(event))

    def test_new_radicalization_refresh_bookkeeping_stays_hidden_in_rewards(self):
        def visible_keys(block):
            keys=[]
            for key,value in block:
                if key=='hidden_effect':continue
                if key in self.effects:keys.extend(visible_keys(self.effects[key]))
                else:
                    keys.append(key)
                    if isinstance(value,list):keys.extend(visible_keys(value))
            return keys
        for event in list(range(27,41))+[46]:
            option=next(v for k,v in read_event('ROC_pingheng.'+str(event)) if k=='option')
            self.assertNotIn('set_variable',visible_keys(option),str(event))
        for name in ('luoshixinjingjifa','yantaogeminglilun','yongbaogemingweiyuanhuizhengzhi'):
            focus=next(v for kind,tree in read_script('common/national_focus/ROC.txt') if kind=='focus_tree' for k,v in tree if k=='focus' and one(v,'id')==name)
            self.assertNotIn('set_variable',visible_keys(one(focus,'completion_reward')),name)

    def test_legacy_focus_rewards_recompute_both_dynamic_buffs_immediately(self):
        for name,delta in [('luoshixinjingjifa',-.05),('yantaogeminglilun',-.05),('yongbaogemingweiyuanhuizhengzhi',-.2)]:
            focus=next(v for kind,tree in read_script('common/national_focus/ROC.txt') if kind=='focus_tree' for k,v in tree if k=='focus' and one(v,'id')==name)
            s=self.state();s.vars.update(ROC_VAR_youyi_base=.5,ROC_VAR_zuoyi_base=.5)
            s.run(one(focus,'completion_reward'))
            self.assertAlmostEqual(s.vars['ROC_dynamic_modifier_st'],-.2*delta)
            self.assertAlmostEqual(s.vars['ROC_dynamic_modifier_st_zuo'],-.2*delta)

    def test_common_focus_recalculates_duration_immediately_and_only_adds_ten_once(self):
        focus=next(v for kind,tree in read_script('common/national_focus/ROC.txt') if kind=='focus_tree' for k,v in tree if k=='focus' and one(v,'id')=='zhichisansanzhizhengfu')
        s=self.state(80,HEADS[0]);self.effect(s,'ROC_ce_retire_bop');s.missions.update(zip(MISSIONS,[100]*3))
        s.run(one(focus,'completion_reward'))
        self.assertEqual(s.missions,dict(zip(MISSIONS,[110]*3)))
        self.assertEqual(s.vars['ROC_zuopai_time_var'],100)
        self.assertEqual(s.vars['ROC_zhongpai_time_var'],60)
        self.assertEqual(s.vars['ROC_youpai_time_var'],45)
        self.timing(s);self.assertEqual(s.missions,dict(zip(MISSIONS,[110]*3)))

if __name__=='__main__':unittest.main()
