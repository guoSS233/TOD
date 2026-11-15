"""Execute shipped governance scripts with the repository Clausewitz interpreter.

Scope selection, global event targets, and country/state checks below model only
engine primitives. Choices, costs, guards, and callbacks are read from the mod.
This does not claim to emulate the HOI4 engine.
"""
import unittest
from test_roc_allied_parties import read_script, one, named_event
from test_roc_economic_council import ScriptState

class GPSState(ScriptState):
    def __init__(self):
        effects = dict(read_script('common/scripted_effects/GPS_scripted_effects.txt'))
        effects.update(dict(read_script('common/scripted_triggers/GPS_scripted_triggers.txt')))
        super().__init__(effects)
        self.tag = 'GPS'
        self.focuses.update({'GPS_quelitangdudushiquan','GPS_gov_recovery_desk','GPS_weichijunguan','GPS_gov_tang_orders','GPS_gov_tang_appointments','GPS_gov_tang_register','GPS_gov_repair_roster'})
        self.states = [dict(id=i, owned=True, controlled=True, infrastructure=2, industrial_complex=1) for i in (847,328,408)]
        self.targets = {}
        self.current = None
        self.foreign_context = None
        self.capitulated = False
        self.rail = True
        self.command_power = 0
        self.army_xp = 0
        self.war_support = .5
    def passes(self, block):
        for k, v in block:
            if k == 'NOT':
                if any(self.passes([item]) for item in v): return False
            elif k == 'TOD_china_unified_for_ming_civil_war':
                if not getattr(self, 'unified', False): return False
            elif k == 'is_subject':
                if getattr(self, 'subject', False) != (v == 'yes'): return False
            elif k == 'country_exists' and v != 'GPS':
                if not getattr(self, 'foreign', {}).get(v, {}).get('exists', False): return False
            elif k == 'is_neighbor_of':
                if not getattr(self, 'foreign', {}).get(v, {}).get('neighbor', False): return False
            elif k == 'has_war_with':
                if not getattr(self, 'foreign', {}).get(v, {}).get('war', False): return False
            elif k == 'num_divisions':
                if not self.compare(getattr(self, 'divisions', 0),v): return False
            elif k == 'has_capitulated':
                if self.capitulated != (v == 'yes'): return False
            elif k == 'any_controlled_state':
                if not any(self.in_state(state, v) for state in self.states if state['controlled']): return False
            elif k == 'has_power_balance':
                if not self.bop: return False
            elif k == 'any_owned_state':
                states = self.foreign[self.foreign_context].get('states', []) if self.foreign_context else self.states
                if not any(self.in_state(state, v) for state in states if state['owned']): return False
            elif k in ('KOR','EZO','WJP'):
                old = self.foreign_context; self.foreign_context = k
                try: ok = self.passes(v)
                finally: self.foreign_context = old
                if not ok: return False
            elif k == 'is_coastal':
                if self.current.get('coastal',False) != (v == 'yes'): return False
            elif k == 'any_province_building_level':
                if one(v, 'building') != 'naval_base' or not self.compare(self.current.get('naval_base',0),one(v,'level')): return False
            elif k.isdigit():
                state = next((z for z in self.states if z['id']==int(k)),None)
                if state is None or not self.in_state(state,v): return False
            elif k == 'has_railway_connection':
                route = getattr(self, 'rail_routes', {}).get(one(v, 'target_state'))
                if (route is not None and route != 'gps') or (route is None and not self.rail): return False
            elif k == 'has_event_target':
                if v not in self.targets: return False
            elif k.startswith('event_target:'):
                target = self.targets.get(k.split(':',1)[1])
                if target is None or not self.in_state(target, v): return False
            elif k in ('is_owned_by','is_controlled_by'):
                if not self.current[{'is_owned_by':'owned','is_controlled_by':'controlled'}[k]]: return False
            elif k in ('infrastructure','industrial_complex','arms_factory'):
                if not self.compare(self.current.get(k,0),v): return False
            elif not super().passes([(k,v)]): return False
        return True
    def in_state(self, state, block):
        old = self.current; self.current = state
        try: return self.passes(block)
        finally: self.current = old
    def run(self, block):
        chunk=[]
        for k,v in block:
            if k in ('add_command_power', 'army_experience', 'add_war_support'):
                if chunk: super().run(chunk); chunk=[]
                attr = {'add_command_power':'command_power', 'army_experience':'army_xp', 'add_war_support':'war_support'}[k]
                setattr(self, attr, getattr(self, attr) + self.number(v))
            elif k.isdigit():
                if chunk: super().run(chunk); chunk=[]
                state=next(z for z in self.states if z['id']==int(k))
                self.targets[one(v,'save_global_event_target_as')]=state
            elif k == 'swap_ideas':
                if chunk: super().run(chunk); chunk=[]
                old,new=one(v,'remove_idea'),one(v,'add_idea')
                if old in self.ideas:
                    self.ideas.remove(old);self.ideas.add(new)
                    if old in getattr(self,'idea_days',{}): self.idea_days[new]=self.idea_days.pop(old)
            elif k == 'add_timed_idea':
                if chunk: super().run(chunk); chunk=[]
                self.ideas.add(one(v,'idea'))
            elif k == 'GPS':
                if chunk: super().run(chunk); chunk=[]
                self.run(v)
            elif k == 'random_owned_controlled_state':
                if chunk: super().run(chunk); chunk=[]
                targets=[s for s in self.states if s['owned'] and s['controlled'] and self.in_state(s,one(v,'limit'))]
                if targets:
                    self.targets[one(v,'save_global_event_target_as')]=targets[0]
            else: chunk.append((k,v))
        if chunk: super().run(chunk)
    def effect(self, name): self.run(self.effects[name])
    def option(self, num, letter, check=True):
        event=named_event(read_script('events/GPS.txt'),f'GPS_governance.{num}')
        choice=next(v for k,v in event if k=='option' and one(v,'name').endswith('.'+letter))
        if check: assert self.passes(one(choice,'trigger'))
        self.run([(k,v) for k,v in choice if k not in ('name','trigger')])

class GovernanceRuntime(unittest.TestCase):
    def test_economic_slot_rejects_parallel_and_cost_is_paid_once(self):
        s=GPSState();s.effect('GPS_gov_start_coal');s.effect('GPS_gov_start_restart')
        self.assertIn('GPS_gov_coal_pending',s.flags);self.assertNotIn('GPS_gov_restart_pending',s.flags)
        s.option(3,'c');self.assertEqual(s.pp,175)
        s.option(3,'c',check=False);self.assertEqual(s.pp,175)
        s.option(4,'a');self.assertIn('GPS_gov_coal_receipt_c',s.flags)
        self.assertNotIn('GPS_gov_economic_busy',s.flags)
        s.effect('GPS_gov_start_restart');self.assertIn('GPS_gov_restart_pending',s.flags)
    def test_lost_target_releases_only_its_slot_and_retry_is_possible(self):
        s=GPSState();s.effect('GPS_gov_start_coal');s.option(3,'a')
        s.states[0]['controlled']=False;s.option(4,'invalid')
        self.assertIn('GPS_gov_coal_failed',s.flags);self.assertNotIn('GPS_gov_coal_done',s.flags)
        self.assertNotIn('GPS_gov_economic_busy',s.flags)
        s.states[0]['controlled']=True;s.effect('GPS_gov_start_coal');s.option(3,'b');s.option(4,'a')
        self.assertIn('GPS_gov_coal_receipt_b',s.flags);self.assertNotIn('GPS_gov_coal_receipt_a',s.flags)
        self.assertNotIn('GPS_gov_coal_failed',s.flags)
    def test_open_option_rechecks_resources_and_archives_without_payment(self):
        s=GPSState();s.effect('GPS_gov_start_restart');s.pp=9
        s.option(5,'c',check=False)
        self.assertEqual(s.pp,9);self.assertIn('GPS_gov_restart_failed',s.flags)
        self.assertNotIn('GPS_gov_economic_busy',s.flags);self.assertNotIn('GPS_gov_restart_chosen',s.flags)
    def test_old_receipt_cannot_clear_another_chain(self):
        s=GPSState();s.effect('GPS_gov_start_coal');s.option(3,'a');s.option(4,'a')
        s.effect('GPS_gov_start_restart');s.option(4,'invalid')
        self.assertIn('GPS_gov_restart_pending',s.flags);self.assertIn('GPS_gov_economic_busy',s.flags)
    def test_wartime_and_wrong_route_cannot_start_settlement(self):
        s=GPSState();s.flags.add('GPS_gov_tang_register_done');s.focuses.add('GPS_xuangaopingluanshengli');s.at_war=True
        s.effect('GPS_gov_start_tang_settlement');self.assertNotIn('GPS_governance.10',s.events)
        s.at_war=False;s.focuses.discard('GPS_quelitangdudushiquan');s.focuses.add('GPS_jianglingjitilingdao')
        s.effect('GPS_gov_start_tang_settlement');self.assertNotIn('GPS_governance.10',s.events)
        s.focuses.discard('GPS_jianglingjitilingdao');s.focuses.add('GPS_quelitangdudushiquan');s.effect('GPS_gov_start_tang_settlement')
        self.assertIn('GPS_governance.10',s.events)
    def test_receipt_checks_owner_and_road(self):
        for field in ('owned','infrastructure'):
            with self.subTest(field=field):
                s=GPSState();s.effect('GPS_gov_start_orders');s.option(1,'b');s.states[0][field]=0
                s.option(2,'invalid');self.assertIn('GPS_gov_orders_failed',s.flags)
                self.assertNotIn('GPS_gov_orders_receipt_b',s.flags)

    def test_receipt_rechecks_target_at_execution_after_popup(self):
        s=GPSState();s.effect('GPS_gov_start_coal');s.option(3,'a')
        s.states[0]['controlled']=False;s.option(4,'a',check=False)
        self.assertIn('GPS_gov_coal_failed',s.flags)
        self.assertNotIn('GPS_gov_coal_done',s.flags)
        self.assertNotIn('GPS_gov_economic_busy',s.flags)
    def test_timed_repairs_are_removed_when_saved_target_is_lost(self):
        s=GPSState();s.flags.update({'GPS_gov_coal_done','GPS_gov_restart_done'})
        s.effect('GPS_gov_start_repair_roster');self.assertIn('GPS_gov_repair_effort',s.ideas)
        daily=one(one(one(read_script('common/on_actions/GPS_on_actions.txt'),'on_actions'),'on_daily'),'effect')
        s.states[0]['owned']=False;s.run(daily)
        self.assertNotIn('GPS_gov_repair_effort',s.ideas)
        self.assertIn('GPS_governance.11',s.events)
        s.run(daily);self.assertEqual(s.events.count('GPS_governance.11'),1)
    def test_restart_receipt_records_policy_and_chosen_wages(self):
        s=GPSState();s.focuses.add('GPS_goujianxingongxie')
        s.effect('GPS_gov_start_restart');s.option(5,'b');s.option(6,'a')
        s.effect('GPS_gov_start_workers_record')
        self.assertIn('GPS_gov_wages_recorded',s.flags);self.assertIn('GPS_gov_union_recorded',s.flags)
        self.assertNotIn('GPS_gov_representatives_recorded',s.flags)

    def test_capitulation_and_overlapping_routes_stop_tang_orders(self):
        for mode in ('capitulated','committee','no_control'):
            s=GPSState()
            if mode == 'capitulated': s.capitulated=True
            if mode == 'committee': s.focuses.add('GPS_jianglingjitilingdao')
            if mode == 'no_control':
                for state in s.states: state['controlled']=False
            s.effect('GPS_gov_start_orders')
            self.assertNotIn('GPS_governance.1',s.events,mode)
    def test_orders_change_bop_with_guard(self):
        for letter,expected in [('a',-.04),('b',.04),('c',0)]:
            s=GPSState();s.effect('GPS_gov_start_orders');s.option(1,letter)
            self.assertAlmostEqual(s.axis,expected)
            old=s.axis;s.option(1,letter,check=False);self.assertEqual(s.axis,old)
        s=GPSState();s.bop=False;s.effect('GPS_gov_start_orders');s.option(1,'a')
        self.assertEqual(s.bop_add_calls,0)
    def test_native_not_is_nor_and_invalid_choice_uses_and(self):
        s=GPSState()
        self.assertFalse(s.passes([('NOT',[('always','yes'),('always','no')])]))
        s.effect('GPS_gov_start_orders')
        s.states[0]['controlled']=False
        s.option(1,'invalid')
        self.assertNotIn('GPS_gov_military_busy',s.flags)

    def test_rail_and_road_coal_options_have_distinct_60_day_ideas(self):
        for rail in (True,False):
            for letter in 'abc':
                s=GPSState();s.rail=rail;s.effect('GPS_gov_start_coal');s.option(3,letter)
                mode='rail' if rail else 'road'
                self.assertIn(f'GPS_gov_coal_{mode}_{letter}',s.ideas)
                self.assertEqual(s.pp,175 if letter=='c' else 200)
                before=set(s.ideas);s.option(3,letter,check=False);self.assertEqual(s.ideas,before)
    def test_rail_control_loss_removes_only_coal_idea_once(self):
        s=GPSState();s.effect('GPS_gov_start_coal');s.option(3,'b')
        s.ideas.add('GPS_gov_restart_effort_a');s.targets['GPS_gov_restart_target']=s.states[0];s.states[1]['controlled']=False
        daily=one(one(one(read_script('common/on_actions/GPS_on_actions.txt'),'on_actions'),'on_daily'),'effect')
        s.run(daily)
        self.assertNotIn('GPS_gov_coal_rail_b',s.ideas)
        self.assertIn('GPS_gov_restart_effort_a',s.ideas)
        self.assertEqual(s.events.count('GPS_governance.12'),1)
        s.run(daily);self.assertEqual(s.events.count('GPS_governance.12'),1)
    def test_appointments_choices_and_absent_bop(self):
        for letter,expected in [('a',-.04),('b',.02),('c',0)]:
            for bop in (True,False):
                s=GPSState();s.flags.add('GPS_gov_orders_done');s.bop=bop;s.effect('GPS_gov_start_tang_appointment');s.option(7,letter)
                self.assertAlmostEqual(s.axis,expected if bop else 0)
                self.assertEqual(s.pp,175 if letter=='c' else 200)
    def test_failed_orders_can_retry_and_clear_old_choice(self):
        s=GPSState();s.effect('GPS_gov_start_orders');s.option(1,'a')
        s.states[0]['controlled']=False;s.option(2,'invalid')
        self.assertNotIn('GPS_gov_orders_done',s.flags)
        s.states[0]['controlled']=True;s.effect('GPS_gov_start_orders');s.option(1,'b');s.option(2,'a')
        self.assertIn('GPS_gov_orders_receipt_b',s.flags);self.assertNotIn('GPS_gov_orders_a',s.flags)
        self.assertNotIn('GPS_gov_orders_failed',s.flags)
    def test_all_restart_choices_apply_different_immediate_consequences(self):
        for letter,pp,idea in [('a',200,'GPS_gov_restart_effort_a'),('b',175,None),('c',190,'GPS_gov_restart_effort_c')]:
            s=GPSState();s.effect('GPS_gov_start_restart');s.option(5,letter)
            self.assertEqual(s.pp,pp)
            if idea:self.assertIn(idea,s.ideas)
            if letter=='a':self.assertAlmostEqual(s.stability,.49)
            if letter=='b':self.assertAlmostEqual(s.stability,.51)

    def test_initial_invalid_archives_without_blocking_a_retry(self):
        for num,starter,pending,done in [(1,'orders','orders','orders'),(7,'tang_appointment','tang_appointment','tang_appointment')]:
            s=GPSState();s.flags.add('GPS_gov_orders_done') if starter=='tang_appointment' else None;s.effect('GPS_gov_start_'+starter);s.states[0]['controlled']=False
            s.option(num,'invalid');self.assertNotIn('GPS_gov_'+done+'_done',s.flags)
            s.states[0]['controlled']=True;s.effect('GPS_gov_start_'+starter)
            self.assertIn('GPS_gov_'+pending+'_pending',s.flags)
    def test_failure_penalty_only_once_after_receipt_expires(self):
        s=GPSState();s.effect('GPS_gov_start_orders');s.option(1,'b');before=s.stability
        s.states[0]['owned']=False;s.option(2,'invalid');self.assertAlmostEqual(s.stability,before-.005)
        s.option(2,'invalid');self.assertAlmostEqual(s.stability,before-.005)
    def test_register_committee_and_settlement_each_have_three_choices(self):
        for num,starter,route in [(9,'tang_register','tang'),(10,'tang_settlement','tang'),(20,'committee_table','committee')]:
            for letter in 'abc':
                s=GPSState()
                if route=='committee':
                    s.focuses.discard('GPS_quelitangdudushiquan');s.focuses.add('GPS_jianglingjitilingdao')
                if num==9:s.flags.add('GPS_gov_tang_appointment_done')
                if num==10:s.focuses.add('GPS_xuangaopingluanshengli');s.flags.add('GPS_gov_tang_register_done')
                s.effect('GPS_gov_start_'+starter);s.option(num,letter)
                self.assertIn(f'GPS_gov_{starter}_{letter}',s.flags)
                if num==10 and letter=='c':self.assertNotIn('GPS_gov_tang_settlement_done',s.flags)
                if num==10 and letter=='a':self.assertIn('GPS_gov_personal_guarantee',s.ideas)
                if num==10 and letter=='b':self.assertIn('GPS_gov_written_handover',s.ideas)
    def test_coal_rail_uses_engine_controlled_path_and_road_needs_industry(self):
        triggers=dict(read_script('common/scripted_triggers/GPS_scripted_triggers.txt'))
        for end in (328,408):
            block=triggers[f'GPS_gov_coal_rail_847_{end}_possible']
            rail=one(block,'has_railway_connection')
            self.assertEqual(one(rail,'start_state'),'847');self.assertEqual(one(rail,'target_state'),str(end))
            self.assertEqual(one(rail,'build_only_on_allied'),'yes')
            weight=one(rail,'controller_priority');self.assertEqual(one(weight,'base'),'-1')
            self.assertEqual(one(one(weight,'modifier'),'tag'),'GPS')
        s=GPSState();s.rail=False;s.states[0]['industrial_complex']=0;s.effect('GPS_gov_start_coal')
        self.assertNotIn('GPS_gov_coal_pending',s.flags)
    def test_composite_not_always_explicitly_wraps_and(self):
        from test_sichuan_red_opportunity import Comparison
        def walk(items):
            for key,value in items:
                if key=='NOT':self.assertEqual(len(value),1)
                if isinstance(value,list) and not isinstance(value,Comparison):walk(value)
        for path in ('events/GPS.txt', 'common/decisions/GPS.txt', 'common/decisions/categories/GPS.txt',
                     'common/scripted_effects/GPS_scripted_effects.txt',
                     'common/scripted_triggers/GPS_scripted_triggers.txt', 'common/on_actions/GPS_on_actions.txt'):
            walk(read_script(path))

    def test_focus_start_requires_all_prerequisites_and_success_receipts(self):
        cases=[('orders','GPS_weichijunguan',None),
               ('tang_appointment','GPS_gov_tang_orders','GPS_gov_orders_done'),
               ('tang_register','GPS_gov_tang_appointments','GPS_gov_tang_appointment_done'),
               ('tang_settlement','GPS_gov_tang_register','GPS_gov_tang_register_done'),
               ('repair_roster','GPS_gov_recovery_desk','GPS_gov_coal_done'),
               ('workers_record','GPS_gov_repair_roster','GPS_gov_restart_done')]
        for effect,focus,flag in cases:
            for missing in ('focus','receipt') if flag else ('focus',):
                with self.subTest(effect=effect,missing=missing):
                    s=GPSState();s.focuses.update({'GPS_weichijunguan','GPS_gov_tang_orders','GPS_gov_tang_appointments','GPS_gov_tang_register','GPS_gov_repair_roster','GPS_xuangaopingluanshengli'})
                    s.flags.update({'GPS_gov_orders_done','GPS_gov_tang_appointment_done','GPS_gov_tang_register_done','GPS_gov_coal_done','GPS_gov_restart_done'})
                    s.flags.discard('GPS_gov_'+effect+'_done')
                    if missing=='focus':s.focuses.discard(focus)
                    else:s.flags.discard(flag)
                    s.effect('GPS_gov_start_'+effect)
                    self.assertFalse(s.events,effect);self.assertNotIn('GPS_gov_'+effect+'_done',s.flags if effect in ('repair_roster','workers_record') else set())
        for effect,failed in [('tang_appointment','orders'),('tang_register','tang_appointment'),('repair_roster','coal'),('workers_record','restart')]:
            s=GPSState();s.focuses.update({'GPS_weichijunguan','GPS_gov_tang_orders','GPS_gov_tang_appointments','GPS_gov_repair_roster'})
            s.flags.update({'GPS_gov_orders_done','GPS_gov_tang_appointment_done','GPS_gov_coal_done','GPS_gov_restart_done',f'GPS_gov_{failed}_failed'})
            s.flags.discard('GPS_gov_'+effect+'_done')
            s.effect('GPS_gov_start_'+effect)
            self.assertFalse(s.events,effect);self.assertNotIn('GPS_gov_'+effect+'_done',s.flags)
    def test_restart_lost_after_receipt_notifies_only_once(self):
        for letter in 'ac':
            with self.subTest(letter=letter):
                s=GPSState();s.effect('GPS_gov_start_restart');s.option(5,letter);s.option(6,'a')
                daily=one(one(one(read_script('common/on_actions/GPS_on_actions.txt'),'on_actions'),'on_daily'),'effect')
                s.states[0]['controlled']=False;s.run(daily);s.run(daily)
                self.assertNotIn('GPS_gov_restart_effort_'+letter,s.ideas)
                self.assertEqual(s.events.count('GPS_governance.13'),1)

class CommitteePhaseTwo(unittest.TestCase):
    def committee(self):
        s=GPSState();s.focuses.discard('GPS_quelitangdudushiquan');s.focuses.add('GPS_jianglingjitilingdao')
        s.focuses.update({'GPS_gov_committee_table','GPS_gov_joint_pay','GPS_gov_defence_roster','GPS_gov_joint_appointments','GPS_gov_old_uniforms','GPS_gov_execution_receipts'})
        s.flags.update({'GPS_gov_committee_table_done'})
        return s
    def test_three_stories_record_distinct_receipts_and_table_discount(self):
        for start,num,receipt,table in [('joint_appointment',21,22,'c'),('joint_pay',23,24,'a'),('defence_roster',25,26,'b')]:
            for letter in 'abc':
                s=self.committee();s.flags.add('GPS_gov_committee_table_'+table);s.effect('GPS_gov_start_'+start);s.option(num,letter)
                if letter=='a':self.assertEqual(s.pp,190)
                s.option(receipt,'a');self.assertIn('GPS_gov_'+start+'_receipt_'+letter,s.flags)
    def test_invalid_target_or_resource_race_releases_only_own_slot(self):
        s=self.committee();s.effect('GPS_gov_start_joint_pay');s.pp=0;s.option(23,'a',check=False)
        self.assertNotIn('GPS_gov_economic_busy',s.flags);self.assertNotIn('GPS_gov_joint_pay_done',s.flags)
        s.pp=200;s.effect('GPS_gov_start_joint_pay');s.option(23,'b');s.states[0]['controlled']=False;s.option(24,'invalid')
        self.assertNotIn('GPS_gov_joint_pay_done',s.flags);self.assertIn('GPS_gov_joint_pay_breach',s.flags)
    def test_settlement_requires_postwar_and_receipts(self):
        s=self.committee();s.effect('GPS_gov_start_committee_settlement');self.assertNotIn('GPS_governance.29',s.events)
    def test_three_slots_are_independent_and_same_slot_excludes_reentry(self):
        s=self.committee();s.effect('GPS_gov_start_joint_pay');s.effect('GPS_gov_start_joint_appointment');s.effect('GPS_gov_start_defence_roster')
        self.assertTrue({'GPS_gov_economic_busy','GPS_gov_signature_busy','GPS_gov_military_busy'} <= s.flags)
        s.effect('GPS_gov_start_restart');self.assertNotIn('GPS_gov_restart_pending',s.flags)
        s.option(23,'b');s.option(24,'a');s.option(24,'invalid')
        self.assertIn('GPS_gov_signature_busy',s.flags);self.assertIn('GPS_gov_military_busy',s.flags)
    def test_wrong_route_capitulation_and_missing_prerequisite_block_all_starts(self):
        for mode in ('route','capitulation','focus','table'):
            for n in ('joint_pay','joint_appointment','defence_roster'):
                s=self.committee()
                if mode=='route':s.focuses.discard('GPS_jianglingjitilingdao')
                if mode=='capitulation':s.capitulated=True
                if mode=='focus':s.focuses.discard('GPS_gov_committee_table')
                if mode=='table':s.flags.discard('GPS_gov_committee_table_done')
                s.effect('GPS_gov_start_'+n);self.assertFalse(s.events,(mode,n))
    def test_rotation_idea_removed_once_on_lost_control(self):
        s=self.committee();s.effect('GPS_gov_start_defence_roster');s.option(25,'a');self.assertIn('GPS_gov_defence_rotation',s.ideas)
        s.states[0]['controlled']=False
        daily=one(one(one(read_script('common/on_actions/GPS_on_actions.txt'),'on_actions'),'on_daily'),'effect');s.run(daily);s.run(daily)
        self.assertNotIn('GPS_gov_defence_rotation',s.ideas);self.assertEqual(s.events.count('GPS_governance.30'),1)
    def test_reopen_after_failure_and_breach_changes_receipt_cost(self):
        s=self.committee();s.effect('GPS_gov_start_joint_pay');s.option(23,'b');s.states[0]['owned']=False;s.option(24,'invalid')
        s.states[0]['owned']=True;s.effect('GPS_gov_start_joint_pay');s.option(23,'b');s.option(24,'a')
        self.assertIn('GPS_gov_joint_pay_breach',s.flags);self.assertIn('GPS_gov_joint_pay_done',s.flags)
        s.flags.update({'GPS_gov_joint_appointment_done','GPS_gov_defence_roster_done'});before=s.pp
        s.effect('GPS_gov_start_execution_receipts');s.option(28,'a');self.assertEqual(s.pp,before-20)
    def test_settlement_rechecks_war_and_previous_records_at_click(self):
        s=self.committee();s.focuses.add('GPS_xuangaopingluanshengli');s.flags.update({'GPS_gov_execution_receipts_done','GPS_gov_old_uniforms_done'})
        s.effect('GPS_gov_start_committee_settlement');s.at_war=True;s.option(29,'a',check=False)
        self.assertNotIn('GPS_gov_committee_settlement_done',s.flags);self.assertEqual(s.pp,200)
        self.assertNotIn('GPS_gov_signature_busy',s.flags)
    def test_later_choices_pay_once_and_defer_reopens(self):
        for n,num in [('old_uniforms',27),('execution_receipts',28),('committee_settlement',29)]:
            for letter in 'abc':
                s=self.committee();s.focuses.add('GPS_xuangaopingluanshengli');s.flags.update({'GPS_gov_joint_appointment_done','GPS_gov_joint_pay_done','GPS_gov_defence_roster_done','GPS_gov_old_uniforms_done','GPS_gov_execution_receipts_done'})
                s.flags.discard('GPS_gov_'+n+'_done');s.effect('GPS_gov_start_'+n);s.option(num,letter);pp=s.pp;s.option(num,letter,check=False)
                self.assertEqual(s.pp,pp);self.assertNotIn('GPS_gov_signature_busy',s.flags)
                if letter=='c' and num!=29:
                    self.assertNotIn('GPS_gov_'+n+'_done',s.flags);s.effect('GPS_gov_start_'+n);self.assertIn('GPS_gov_'+n+'_pending',s.flags)
                else:self.assertIn('GPS_gov_'+n+'_done',s.flags)
    def test_committee_without_bop_and_changed_route_after_popup(self):
        s=self.committee();s.bop=False;s.effect('GPS_gov_start_joint_appointment');s.option(21,'b');self.assertEqual(s.bop_add_calls,0)
        s.focuses.discard('GPS_jianglingjitilingdao');s.option(22,'a',check=False)
        self.assertNotIn('GPS_gov_joint_appointment_done',s.flags);self.assertNotIn('GPS_gov_signature_busy',s.flags)

    def test_receipts_apply_distinct_effects_only_once(self):
        expected={
            'joint_appointment': [(5,0,0,0,0),(0,3,0,-.005,0),(2,0,0,0,0)],
            'joint_pay': [(2,0,0,.005,0),(0,3,0,0,0),(0,4,0,-.005,0)],
            'defence_roster': [(0,0,3,0,0),(0,0,0,.005,0),(0,0,0,-.005,.005)],
        }
        for n,start,reply in [('joint_appointment',21,22),('joint_pay',23,24),('defence_roster',25,26)]:
            for letter,want in zip('abc',expected[n]):
                with self.subTest(chain=n,letter=letter):
                    s=self.committee();s.effect('GPS_gov_start_'+n);s.option(start,letter)
                    before=(s.pp,s.command_power,s.army_xp,s.stability,s.war_support)
                    s.option(reply,'a');after=(s.pp,s.command_power,s.army_xp,s.stability,s.war_support)
                    for actual,delta in zip((a-b for a,b in zip(after,before)),want):self.assertAlmostEqual(actual,delta)
                    s.option(reply,'a',check=False)
                    self.assertEqual((s.pp,s.command_power,s.army_xp,s.stability,s.war_support),after)
    def test_receipt_fee_discount_and_breach_precedence_and_race(self):
        for all_a,breach,fee in [(False,False,10),(True,False,5),(True,True,20),(False,True,20)]:
            s=self.committee();s.flags.update({'GPS_gov_joint_pay_done','GPS_gov_defence_roster_done','GPS_gov_joint_appointment_done'})
            if all_a:s.flags.update({'GPS_gov_joint_pay_receipt_a','GPS_gov_defence_roster_receipt_a','GPS_gov_joint_appointment_receipt_a'})
            if breach:s.flags.add('GPS_gov_joint_pay_breach')
            s.pp=fee;s.effect('GPS_gov_start_execution_receipts');s.option(28,'a');self.assertEqual(s.pp,0)
            s.option(28,'a',check=False);self.assertEqual(s.pp,0)
            s=self.committee();s.flags.update({'GPS_gov_joint_pay_done','GPS_gov_defence_roster_done','GPS_gov_joint_appointment_done'})
            if all_a:s.flags.update({'GPS_gov_joint_pay_receipt_a','GPS_gov_defence_roster_receipt_a','GPS_gov_joint_appointment_receipt_a'})
            if breach:s.flags.add('GPS_gov_joint_pay_breach')
            s.pp=fee;s.effect('GPS_gov_start_execution_receipts');s.pp=fee-1;s.option(28,'a',check=False)
            self.assertEqual(s.pp,fee-1);self.assertNotIn('GPS_gov_execution_receipts_done',s.flags)
    def test_initial_invalid_does_not_mark_breach(self):
        for n,num in [('joint_appointment',21),('joint_pay',23),('defence_roster',25)]:
            s=self.committee();s.effect('GPS_gov_start_'+n);s.states[0]['owned']=False;s.option(num,'invalid')
            self.assertNotIn('GPS_gov_'+n+'_breach',s.flags)
    def test_three_actual_a_receipts_open_five_point_review(self):
        s=self.committee()
        for n,start,reply in [('joint_pay',23,24),('defence_roster',25,26),('joint_appointment',21,22)]:
            s.effect('GPS_gov_start_'+n);s.option(start,'a');s.option(reply,'a')
        s.pp=5;s.effect('GPS_gov_start_execution_receipts');s.option(28,'a')
        self.assertEqual(s.pp,0);self.assertIn('GPS_gov_execution_receipts_done',s.flags)
    def test_review_cost_availability_matches_execution_for_every_tier(self):
        event=named_event(read_script('events/GPS.txt'),'GPS_governance.28')
        choice=next(v for k,v in event if k=='option' and one(v,'name').endswith('.a'))
        for all_a,breach,fee in [(False,False,10),(True,False,5),(True,True,20),(False,True,20)]:
            s=self.committee();s.flags.update({'GPS_gov_joint_pay_done','GPS_gov_defence_roster_done','GPS_gov_joint_appointment_done'})
            if all_a:s.flags.update({'GPS_gov_joint_pay_receipt_a','GPS_gov_defence_roster_receipt_a','GPS_gov_joint_appointment_receipt_a'})
            if breach:s.flags.add('GPS_gov_joint_pay_breach')
            s.effect('GPS_gov_start_execution_receipts');s.pp=fee-1;self.assertFalse(s.passes(one(choice,'trigger')))
            s.pp=fee;self.assertTrue(s.passes(one(choice,'trigger')))

class GovernanceBatch3(unittest.TestCase):
    def test_national_dominance_requires_real_control_and_independence(self):
        s=GPSState(); s.focuses.add('GPS_xuangaopingluanshengli')
        s.vars['num_owned_states']=20; s.unified=True; s.subject=False
        s.states.extend(dict(id=i,owned=True,controlled=True,infrastructure=2,industrial_complex=1) for i in (608,613,592))
        self.assertTrue(s.passes([('GPS_gov_national_dominance','yes')]))
        for field in ('subject','at_war'):
            setattr(s,field,True); self.assertFalse(s.passes([('GPS_gov_national_dominance','yes')])); setattr(s,field,False)
        s.vars['num_owned_states']=19; self.assertFalse(s.passes([('GPS_gov_national_dominance','yes')]))
        s.vars['num_owned_states']=20; s.states[-1]['controlled']=False
        self.assertFalse(s.passes([('GPS_gov_national_dominance','yes')]))
    def test_batch3_starts_require_existing_settlement_and_postwar(self):
        s=GPSState(); s.effect('GPS_gov_start_national_position'); self.assertNotIn('GPS_governance.40',s.events)
        s.focuses.update({'GPS_xuangaopingluanshengli','GPS_sheizhuchenfu','GPS_gov_tang_settlement'})
        s.flags.add('GPS_gov_tang_settlement_done'); s.effect('GPS_gov_start_national_position')
        self.assertIn('GPS_governance.40',s.events)
    def test_contact_guard_requires_real_neighbor_and_nonhostility(self):
        s=GPSState(); s.foreign={'STG': {'exists':True,'neighbor':True,'war':False}}
        self.assertTrue(s.passes([('GPS_gov_contact_STG','yes')]))
        for field, value in [('exists',False),('neighbor',False),('war',True)]:
            s.foreign['STG'][field]=value; self.assertFalse(s.passes([('GPS_gov_contact_STG','yes')])); s.foreign['STG'][field]=not value
    def test_demobilization_receipt_validates_original_target_and_one_shot(self):
        s=GPSState();s.effect('GPS_gov_start_demobilization');s.option(45,'a');pp=s.pp
        s.option(45,'a',check=False);self.assertEqual(s.pp,pp)
        s.states[0]['controlled']=False;s.option(46,'invalid');self.assertNotIn('GPS_gov_demobilization_done',s.flags)
        self.assertNotIn('GPS_gov_economic_busy',s.flags)
    def test_contact_fee_and_interrupted_receipt(self):
        s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_sheizhuchenfu','GPS_gov_tang_settlement'})
        s.flags.update({'GPS_gov_tang_settlement_done','GPS_gov_national_position_done','GPS_gov_tang_register_a','GPS_gov_contact_STG_pending'})
        s.foreign={'STG':{'exists':True,'neighbor':True,'war':False}}
        s.effect('GPS_gov_start_contact');s.option(41,'a');self.assertEqual(s.pp,195)
        s.foreign['STG']['neighbor']=False;s.option(42,'invalid')
        self.assertNotIn('GPS_gov_contact_STG_done',s.flags);self.assertIn('GPS_governance.43',s.events)
    def test_grain_benefit_removed_when_original_target_lost(self):
        s=GPSState();s.focuses.add('GPS_gov_rural_supply');s.effect('GPS_gov_start_grain');s.option(51,'a');s.option(52,'a')
        self.assertIn('GPS_gov_grain_effort',s.ideas)
        s.states[0]['controlled']=False
        daily=one(one(one(read_script('common/on_actions/GPS_on_actions.txt'),'on_actions'),'on_daily'),'effect')
        s.run(daily);s.run(daily)
        self.assertNotIn('GPS_gov_grain_effort',s.ideas);self.assertEqual(s.events.count('GPS_governance.53'),1)
    def test_grain_three_branches_have_distinct_receipt_effects(self):
        expected={'a':('stability',.01),'b':('war_support',.01),'c':('command_power',3)}
        for letter,(attr,delta) in expected.items():
            s=GPSState();s.focuses.add('GPS_gov_rural_supply');before=getattr(s,attr)
            s.effect('GPS_gov_start_grain');s.option(51,letter);s.option(52,'a')
            self.assertAlmostEqual(getattr(s,attr)-before,delta)
    def test_contact_fees_follow_mandate(self):
        for authority,fee in [('a',5),('b',10),('c',15)]:
            s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_sheizhuchenfu','GPS_gov_tang_settlement'})
            s.flags.update({'GPS_gov_tang_settlement_done','GPS_gov_national_position_done','GPS_gov_tang_register_'+authority,'GPS_gov_contact_STG_pending'})
            s.foreign={'STG':{'exists':True,'neighbor':True,'war':False}}
            s.effect('GPS_gov_start_contact');s.option(41,'b');self.assertEqual(s.pp,200-fee)
            s.option(41,'b',check=False);self.assertEqual(s.pp,200-fee)
    def test_sea_policy_requires_both_real_controlled_coastal_ports(self):
        s=GPSState();s.states[0].update(coastal=True,naval_base=1)
        s.foreign={'EZO':{'exists':True,'war':False,'neighbor':False,'states':[dict(id=1,owned=True,controlled=True,coastal=True,naval_base=1)]}}
        self.assertTrue(s.passes([('GPS_gov_contact_EZO','yes')]))
        for side,field in [('GPS','controlled'),('EZO','controlled'),('EZO','naval_base')]:
            state=s.states[0] if side=='GPS' else s.foreign['EZO']['states'][0]
            old=state[field];state[field]=False if field=='controlled' else 0
            self.assertFalse(s.passes([('GPS_gov_contact_EZO','yes')]))
            state[field]=old
        s.foreign['EZO']['exists']=False;self.assertFalse(s.passes([('GPS_gov_contact_EZO','yes')]))
    def test_entry_preparation_is_not_national_dominance(self):
        s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_sheizhuchenfu','GPS_gov_tang_settlement','GPS_gov_national_position'})
        s.flags.add('GPS_gov_tang_settlement_done');s.foreign={'STG':{'exists':True,'neighbor':True,'war':False}};s.divisions=5
        s.effect('GPS_gov_start_national_position');s.option(40,'c');self.assertIn('GPS_xuanzhan',s.flags)
        self.assertFalse(s.passes([('GPS_gov_national_dominance','yes')]))
    def test_peace_foothold_allows_demobilization_without_postwar_victory(self):
        s=GPSState();self.assertNotIn('GPS_xuangaopingluanshengli',s.focuses)
        s.effect('GPS_gov_start_demobilization');self.assertIn('GPS_gov_demobilization_pending',s.flags)
        s.effect('GPS_gov_start_grain');self.assertNotIn('GPS_gov_grain_pending',s.flags)
        s.at_war=True;s.option(45,'a',check=False);self.assertNotIn('GPS_gov_demobilization_done',s.flags)
    def test_national_branches_require_actual_dominance_and_different_effects(self):
        for name,num in [('national_army',47),('national_accounts',48),('local_delegation',49)]:
            for letter,pp in [('a',180),('b',185),('c',190)]:
                s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_gov_national_position','GPS_gov_'+name})
                s.flags.add('GPS_gov_national_position_done');s.vars['num_owned_states']=20;s.unified=True
                s.states.extend(dict(id=i,owned=True,controlled=True,infrastructure=2,industrial_complex=1) for i in (608,613,592))
                s.effect('GPS_gov_start_'+name);s.option(num,letter)
                self.assertEqual(s.pp,pp);self.assertIn('GPS_gov_'+name+'_done',s.flags)
                s.option(num,letter,check=False);self.assertEqual(s.pp,pp)
    def test_receipt_rechecks_race_and_releases_slot(self):
        s=GPSState();s.effect('GPS_gov_start_demobilization');s.option(45,'a');s.states[0]['controlled']=False
        s.option(46,'a',check=False)
        self.assertNotIn('GPS_gov_economic_busy',s.flags);self.assertNotIn('GPS_gov_demobilization_done',s.flags)
    def test_contact_success_click_rechecks_route_and_reports_interruption(self):
        s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_sheizhuchenfu','GPS_gov_tang_settlement'})
        s.flags.update({'GPS_gov_tang_settlement_done','GPS_gov_national_position_done','GPS_gov_contact_STG_pending'})
        s.foreign={'STG':{'exists':True,'neighbor':True,'war':False}}
        s.effect('GPS_gov_start_contact');s.option(41,'a');s.foreign['STG']['war']=True;s.option(42,'a',check=False)
        self.assertNotIn('GPS_gov_signature_busy',s.flags);self.assertNotIn('GPS_gov_contact_STG_done',s.flags)
        self.assertIn('GPS_governance.43',s.events)
    def test_entry_may_prepare_against_adjacent_roc_without_claiming_unity(self):
        s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_sheizhuchenfu','GPS_gov_tang_settlement','GPS_gov_national_position'})
        s.flags.add('GPS_gov_tang_settlement_done');s.foreign={'ROC':{'exists':True,'neighbor':True,'war':False}};s.divisions=5
        s.effect('GPS_gov_start_national_position');s.option(40,'c');self.assertIn('GPS_xuanzhan',s.flags)
    def test_contact_all_targets_and_terms_have_real_receipts(self):
        for tag in ('STG','MNG','XBJ'):
            for letter,attr,delta in [('a','command_power',3),('b','stability',.005),('c','war_support',.005)]:
                s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_sheizhuchenfu','GPS_gov_tang_settlement'})
                s.flags.update({'GPS_gov_tang_settlement_done','GPS_gov_national_position_done','GPS_gov_contact_'+tag+'_pending'})
                s.foreign={tag:{'exists':True,'neighbor':True,'war':False}};before=getattr(s,attr)
                s.effect('GPS_gov_start_contact');s.option(41,letter);s.option(42,'a')
                self.assertIn('GPS_gov_contact_'+tag+'_done',s.flags);self.assertAlmostEqual(getattr(s,attr)-before,delta)
                s.option(42,'a',check=False);self.assertAlmostEqual(getattr(s,attr)-before,delta)
    def test_diplomacy_lost_country_or_hostile_interrupts(self):
        for field,value in [('exists',False),('war',True),('neighbor',False)]:
            s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_sheizhuchenfu','GPS_gov_tang_settlement'})
            s.flags.update({'GPS_gov_tang_settlement_done','GPS_gov_national_position_done','GPS_gov_contact_MNG_pending'})
            s.foreign={'MNG':{'exists':True,'neighbor':True,'war':False}};s.effect('GPS_gov_start_contact');s.option(41,'c')
            s.foreign['MNG'][field]=value;s.option(42,'invalid');self.assertNotIn('GPS_gov_contact_MNG_done',s.flags)
            self.assertIn('GPS_governance.43',s.events)
    def test_committees_three_authorities_change_actual_fees(self):
        for letter,fee in [('a',5),('b',10),('c',15)]:
            s=GPSState();s.focuses.discard('GPS_quelitangdudushiquan');s.focuses.update({'GPS_jianglingjitilingdao','GPS_xuangaopingluanshengli','GPS_sheizhuchenfu','GPS_gov_committee_settlement'})
            s.flags.update({'GPS_gov_committee_settlement_done','GPS_gov_national_position_done','GPS_gov_committee_settlement_'+letter,'GPS_gov_contact_XBJ_pending'})
            s.foreign={'XBJ':{'exists':True,'neighbor':True,'war':False}};s.effect('GPS_gov_start_contact');s.option(41,'b');self.assertEqual(s.pp,200-fee)
    def test_eastern_policy_rechecks_foreign_route_and_cost(self):
        for tag,num in [('KOR',54),('EZO',55),('WJP',56)]:
            for letter,fee in [('a',20),('b',15),('c',0)]:
                s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_sheizhuchenfu','GPS_gov_tang_settlement'})
                s.flags.update({'GPS_gov_tang_settlement_done','GPS_gov_national_position_done'})
                s.states[0].update(coastal=True,naval_base=1)
                s.foreign={tag:{'exists':True,'neighbor':False,'war':False,'states':[dict(id=1,owned=True,controlled=True,coastal=True,naval_base=1)]}}
                s.effect('GPS_gov_start_policy_'+tag);s.option(num,letter);self.assertEqual(s.pp,200-fee)
                self.assertIn('GPS_gov_policy_'+tag+'_done',s.flags);s.option(num,letter,check=False);self.assertEqual(s.pp,200-fee)
                t=GPSState();t.focuses.update(s.focuses);t.flags.update({'GPS_gov_tang_settlement_done','GPS_gov_national_position_done'})
                t.foreign={tag:{'exists':False,'neighbor':False,'war':False,'states':[]}};t.effect('GPS_gov_start_policy_'+tag)
                self.assertNotIn('GPS_gov_policy_'+tag+'_pending',t.flags)
    def test_contact_archive_remembers_target_and_term(self):
        s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_sheizhuchenfu','GPS_gov_tang_settlement'})
        s.flags.update({'GPS_gov_tang_settlement_done','GPS_gov_national_position_done','GPS_gov_contact_STG_pending'})
        s.foreign={'STG':{'exists':True,'neighbor':True,'war':False}};s.effect('GPS_gov_start_contact');s.option(41,'b');s.option(42,'a')
        self.assertIn('GPS_gov_contact_STG_b',s.flags)
    def test_national_policies_apply_distinct_ideas_and_revoke_when_dominance_lost(self):
        for name,num in [('national_army',47),('national_accounts',48),('local_delegation',49)]:
            for letter in 'abc':
                s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_gov_national_position','GPS_gov_'+name})
                s.flags.add('GPS_gov_national_position_done');s.vars['num_owned_states']=20;s.unified=True
                s.states.extend(dict(id=i,owned=True,controlled=True,infrastructure=2,industrial_complex=1) for i in (608,613,592))
                s.effect('GPS_gov_start_'+name);s.option(num,letter)
                self.assertIn('GPS_gov_'+name+'_'+letter+'_policy',s.ideas)
                s.states[-1]['controlled']=False
                daily=one(one(one(read_script('common/on_actions/GPS_on_actions.txt'),'on_actions'),'on_daily'),'effect');s.run(daily)
                self.assertNotIn('GPS_gov_'+name+'_'+letter+'_policy',s.ideas)
    def test_batch3_effects_never_apply_foreign_scope_or_transfer_sovereignty(self):
        forbidden={'STG','MNG','XBJ','KOR','EZO','WJP','SRC','ROC','declare_war_on','annex_country','transfer_state','white_peace','add_opinion_modifier','puppet'}
        def visit(block):
            for key,value in block:
                if key in ('limit','trigger','desc'): continue
                self.assertNotIn(key,forbidden)
                if isinstance(value,list):visit(value)
        for num in list(range(40,59)):
            event=named_event(read_script('events/GPS.txt'),f'GPS_governance.{num}')
            visit([(k,v) for k,v in event if k=='option' or k=='immediate'])
    def test_regional_posture_is_removed_when_peace_or_foothold_lost(self):
        s=GPSState();s.effect('GPS_gov_start_regional_closure');s.option(44,'b')
        self.assertIn('GPS_gov_regional_closure_b_policy',s.ideas)
        s.at_war=True;daily=one(one(one(read_script('common/on_actions/GPS_on_actions.txt'),'on_actions'),'on_daily'),'effect')
        s.run(daily);s.run(daily);self.assertNotIn('GPS_gov_regional_closure_b_policy',s.ideas)
        self.assertEqual(s.events.count('GPS_governance.59'),1)
    def test_wartime_preserves_national_and_grain_policies_without_lost_control(self):
        s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_gov_national_position','GPS_gov_national_army','GPS_gov_rural_supply'})
        s.flags.add('GPS_gov_national_position_done');s.vars['num_owned_states']=20;s.unified=True
        s.states.extend(dict(id=i,owned=True,controlled=True,infrastructure=2,industrial_complex=1) for i in (608,613,592))
        s.effect('GPS_gov_start_national_army');s.option(47,'a');s.effect('GPS_gov_start_grain');s.option(51,'a');s.option(52,'a')
        s.at_war=True;daily=one(one(one(read_script('common/on_actions/GPS_on_actions.txt'),'on_actions'),'on_daily'),'effect');s.run(daily)
        self.assertIn('GPS_gov_national_army_a_policy',s.ideas);self.assertIn('GPS_gov_grain_effort',s.ideas)
        self.assertNotIn('GPS_governance.57',s.events);self.assertNotIn('GPS_governance.53',s.events)
    def test_grain_can_start_during_war_in_held_foothold(self):
        for letter in 'abc':
            s=GPSState();s.focuses.add('GPS_gov_rural_supply');s.at_war=True;s.effect('GPS_gov_start_grain')
            self.assertIn('GPS_gov_grain_pending',s.flags)
            s.option(51,letter);s.option(52,'a');self.assertIn('GPS_gov_grain_done',s.flags)

class GovernanceReviewFixes(unittest.TestCase):
    def position(self):
        s=GPSState();s.focuses.update({'GPS_xuangaopingluanshengli','GPS_sheizhuchenfu','GPS_gov_tang_settlement','GPS_gov_national_position'})
        s.flags.add('GPS_gov_tang_settlement_done');s.foreign={'STG':{'exists':True,'neighbor':True,'war':False}};s.divisions=5
        s.effect('GPS_gov_start_national_position')
        return s
    def test_entry_checks_real_railway_for_display_and_execution(self):
        event=named_event(read_script('events/GPS.txt'),'GPS_governance.40')
        opt=next(v for k,v in event if k=='option' and one(v,'name')=='GPS_governance.40.c')
        for scenario in ('rail_false','no_rail','third_country','origin_lost','both_endpoints_lost','one_route','other_route'):
            with self.subTest(scenario=scenario):
                s=self.position()
                if scenario == 'rail_false':
                    s.rail=False
                else:
                    s.rail_routes={'328':('absent' if scenario in ('no_rail','other_route') else 'foreign' if scenario=='third_country' else 'gps'), '408':('gps' if scenario=='other_route' else 'foreign' if scenario=='third_country' else 'absent')}
                if scenario=='origin_lost':
                    s.states[0]['controlled']=False
                if scenario=='both_endpoints_lost':
                    s.states[1]['controlled']=False;s.states[2]['controlled']=False
                allowed=scenario in ('one_route','other_route')
                self.assertEqual(s.passes(one(opt,'trigger')),allowed)
                s.option(40,'c',check=False)
                self.assertEqual('GPS_xuanzhan' in s.flags,allowed)
                self.assertEqual(s.pp,170 if allowed else 200)
    def test_failed_receipt_retry_success_clears_only_own_failure_and_overview(self):
        texts=read_script('common/scripted_localisation/GPS_scripted_localisation.txt')
        for name,start,first,reply,textname,other in [('demobilization','demobilization',45,46,'GetGPSGovDemobPromise','grain'),('grain','grain',51,52,'GetGPSGovGrainPromise','demobilization')]:
            with self.subTest(name=name):
                s=GPSState();s.focuses.add('GPS_gov_rural_supply');s.effect('GPS_gov_start_'+start);s.option(first,'a')
                s.states[0]['controlled']=False;s.option(reply,'invalid');self.assertIn('GPS_gov_'+name+'_failed',s.flags)
                s.states[0]['controlled']=True;s.flags.update({'GPS_gov_'+other+'_failed','GPS_gov_signature_busy'})
                s.effect('GPS_gov_start_'+start);s.option(first,'b');s.option(reply,'a')
                self.assertIn('GPS_gov_'+name+'_done',s.flags);self.assertNotIn('GPS_gov_'+name+'_failed',s.flags)
                self.assertIn('GPS_gov_'+other+'_failed',s.flags);self.assertIn('GPS_gov_signature_busy',s.flags)
                dynamic=next(v for k,v in texts if k=='defined_text' and one(v,'name')==textname)
                selected=next(one(v,'localization_key') for k,v in dynamic if k=='text' and (not any(x=='trigger' for x,_ in v) or s.passes(one(v,'trigger'))))
                self.assertEqual(selected,'GPS_gov_overview_'+name+'_b')
                before=(s.pp,s.stability,s.war_support,s.command_power,set(s.flags));s.option(reply,'a',check=False)
                self.assertEqual((s.pp,s.stability,s.war_support,s.command_power,set(s.flags)),before)

class GovernanceReviewRuntime(unittest.TestCase):
    def decision(self, name):
        return one(one(read_script('common/decisions/GPS.txt'),'GPS_gov_category'),name)
    def national(self):
        s=GPSState();s.vars['num_owned_states']=20
        s.states.extend(dict(id=i,owned=True,controlled=True,infrastructure=2,industrial_complex=1) for i in (608,613,592))
        return s
    def test_restart_requires_factory_and_selects_industrial_state(self):
        for kind in ('industrial_complex','arms_factory'):
            s=GPSState()
            for state in s.states: state['industrial_complex']=0
            d=self.decision('GPS_gov_open_restart')
            self.assertFalse(s.passes(one(d,'available')))
            s.effect('GPS_gov_start_restart');self.assertNotIn('GPS_gov_economic_busy',s.flags)
            s.states[1][kind]=1;s.states[1]['damaged']=True
            self.assertTrue(s.passes(one(d,'available')))
            s.effect('GPS_gov_start_restart');self.assertEqual(s.targets['GPS_gov_restart_target']['id'],328)
    def test_restart_lost_factory_option_and_receipt_cannot_reward_and_retry(self):
        for stage in ('option','receipt'):
            s=GPSState();s.effect('GPS_gov_start_restart')
            if stage=='receipt': s.option(5,'b')
            s.states[0]['industrial_complex']=0
            event=named_event(read_script('events/GPS.txt'),f'GPS_governance.{5 if stage=="option" else 6}')
            choice=next(v for k,v in event if k=='option' and one(v,'name').endswith('.a'))
            self.assertFalse(s.passes(one(choice,'trigger')))
            before=(s.pp,s.stability,s.army_xp,set(s.ideas))
            s.option(5 if stage=='option' else 6,'a',check=False)
            self.assertEqual((s.pp,s.army_xp,set(s.ideas)),(before[0],before[2],before[3]));self.assertLessEqual(s.stability,before[1])
            self.assertNotIn('GPS_gov_restart_done',s.flags);self.assertNotIn('GPS_gov_economic_busy',s.flags)
            s.effect('GPS_gov_start_restart');self.assertIn('GPS_gov_restart_pending',s.flags)
    def test_restore_all_saved_national_choices_without_other_side_effects(self):
        for name in ('national_army','national_accounts','local_delegation'):
            for letter in 'abc':
                s=self.national();flag=f'GPS_gov_{name}_{letter}';idea=flag+'_policy'
                s.flags.update({f'GPS_gov_{name}_done',flag,'GPS_gov_economic_busy','GPS_gov_military_busy','GPS_gov_signature_busy'})
                if name=='national_army' and letter=='c': s.ideas.add('GPS_gov_national_army_c_suspended');s.idea_days={'GPS_gov_national_army_c_suspended':70}
                d=self.decision('GPS_gov_restore_national_policies')
                self.assertTrue(s.passes(one(d,'visible')));self.assertTrue(s.passes(one(d,'available')))
                before=(s.pp,s.stability,s.war_support,s.army_xp,set(s.flags));s.at_war=True
                s.effect('GPS_gov_restore_national_policies');self.assertIn(idea,s.ideas)
                self.assertEqual((s.pp,s.stability,s.war_support,s.army_xp,set(s.flags)),before)
                self.assertFalse(s.passes(one(d,'visible')));s.effect('GPS_gov_restore_national_policies')
                self.assertEqual((s.pp,s.stability,s.war_support,s.army_xp,set(s.flags)),before)
    def test_restore_requires_control_done_and_choice(self):
        for mode in ('control','choice','done'):
            s=self.national();s.flags.update({'GPS_gov_national_army_done','GPS_gov_national_army_a'})
            if mode=='control':s.states[-1]['controlled']=False
            if mode=='choice':s.flags.remove('GPS_gov_national_army_a')
            if mode=='done':s.flags.remove('GPS_gov_national_army_done')
            d=self.decision('GPS_gov_restore_national_policies')
            if mode=='control':self.assertTrue(s.passes(one(d,'visible')));self.assertFalse(s.passes(one(d,'available')))
            else:self.assertFalse(s.passes(one(d,'visible')))
            s.effect('GPS_gov_restore_national_policies');self.assertFalse(s.ideas)

    def test_timed_army_suspension_preserves_remaining_duration_and_expires(self):
        s=self.national();s.flags.update({'GPS_gov_national_army_done','GPS_gov_national_army_c'});s.ideas.add('GPS_gov_national_army_c_policy');s.idea_days={'GPS_gov_national_army_c_policy':42}
        s.states[-1]['controlled']=False
        daily=one(one(one(read_script('common/on_actions/GPS_on_actions.txt'),'on_actions'),'on_daily'),'effect');s.run(daily);s.run(daily)
        self.assertIn('GPS_gov_national_army_c_suspended',s.ideas);self.assertEqual(s.idea_days['GPS_gov_national_army_c_suspended'],42);self.assertEqual(s.events.count('GPS_governance.57'),1)
        s.states[-1]['controlled']=True;s.effect('GPS_gov_restore_national_policies')
        self.assertEqual(s.idea_days['GPS_gov_national_army_c_policy'],42)
        s.states[-1]['controlled']=False;s.run(daily);s.ideas.remove('GPS_gov_national_army_c_suspended');s.idea_days.clear();s.states[-1]['controlled']=True
        s.effect('GPS_gov_restore_national_policies');self.assertNotIn('GPS_gov_national_army_c_policy',s.ideas)
