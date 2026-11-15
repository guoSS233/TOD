"""Behavioral execution of production approval scripts; not an engine simulation."""
import unittest
from test_roc_allied_parties import economic_decisions, ROOT, one, read_script, named_event
from test_roc_economic_council import ScriptState
from test_roc_economic_council_runtime_syntax import walk

PEOPLE = [('yu', 'YuShude', 'tuidongnongyehezuoshefazhan'),
          ('yan', 'YanYangchu', 'tuidongxiangcunjiansheyundong'),
          ('ruan', 'RuanXiaoxian', 'qianghuagonghuiquanli'),
          ('chen', 'ChenZanxian', 'qianghuagonghuiquanli'),
          ('xiao', 'XiaoZheng', 'kuodamincuhuifanwei')]

class Legislation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.effects = dict(read_script("common/scripted_effects/ROC_scripted_effects.txt"))
        for directory in ('scripted_effects', 'scripted_triggers'):
            for filename in ('ROC_economic_council.txt', 'ROC_legislation.txt'):
                path = ROOT / 'common' / directory / filename
                if path.exists(): cls.effects.update(dict(read_script(str(path))))
        cls.projects = dict(economic_decisions())

    def state(self, person=0, expansion=False):
        s = ScriptState(self.effects)
        s.focuses.update({'gemingweiyuanhui', 'gaizaojingjidezhunbei'})
        s.focuses.add(PEOPLE[person][2])
        s.ideas.add('ROC_idea_' + PEOPLE[person][1])
        s.missions['ROC_decision_bop_jingjidahui'] = 700 if expansion else 1000
        if expansion:
            s.flags.add('ROC_econ_' + PEOPLE[person][0] + '_pilot_done')
            s.focuses.add(PEOPLE[person][2])
        self.run_effect(s, 'ROC_econ_refresh')
        return s

    def run_effect(self, s, name):
        self.assertIn(name, self.effects, 'missing production approval behavior: ' + name)
        s.run(self.effects[name])

    def submit(self, s):
        self.run_effect(s, 'ROC_bill_refresh_candidate')
        decision = one(economic_decisions(), 'ROC_bill_submit')
        self.assertTrue(s.passes(one(decision, 'available')))
        self.assertEqual(one(decision, 'cost'), '15')
        s.pp -= float(one(decision, 'cost'))
        s.run(one(decision, 'complete_effect'))

    def test_submission_does_not_implement_and_locks_policy(self):
        s = self.state()
        self.assertFalse(s.passes(one(self.projects['ROC_econ_yu_pilot'], 'available')))
        self.submit(s)
        self.assertEqual(s.pp, 185)
        self.assertEqual(s.vars['ROC_bill_stage'], 1)
        self.assertEqual(s.vars['ROC_bill_days_left'], 45)
        self.assertFalse(s.passes([('ROC_econ_policy_free', 'yes')]))
        self.assertTrue(s.passes([('ROC_econ_allied_free', 'yes')]))
        self.assertFalse(s.decisions)
        self.assertEqual(s.axis, 0)
        self.assertEqual(s.vars.get('ROC_econ_pending_shift', 0), 0)

    def test_three_preparations_recompute_without_accumulation(self):
        for effect, focus, flag, expected, pp in [
            ('materials', None, None, 3, 175), ('signatures', None, None, 2, 165),
            ('signatures', None, 'ROC_bill_rural_record', 2, 165),
            ('party', None, None, 1, 185), ('party', 'qianghuazhengzhituanjie', None, 1, 185)]:
            s = self.state(1)
            if focus: s.focuses.add(focus)
            if flag: s.flags.add(flag)
            self.submit(s)
            self.run_effect(s, 'ROC_bill_prepare_' + effect)
            self.assertEqual(s.pp, pp)
            self.assertEqual(s.vars['ROC_bill_stage'], 2)
            for _ in range(3): self.run_effect(s, 'ROC_bill_refresh_support')
            self.assertEqual(s.vars['ROC_bill_support'], expected)
            self.run_effect(s, 'ROC_bill_prepare_' + effect)
            self.assertEqual(s.pp, pp)

    def test_formal_approval_single_use_and_project_identity(self):
        for person, (name, _, _) in enumerate(PEOPLE):
            for expansion in (False, True):
                approved = self.state(person, expansion)
                approved.focuses.update({'qianghuazhengzhituanjie', 'jingchenghezuo'})
                self.submit(approved)
                self.run_effect(approved, 'ROC_bill_prepare_materials')
                self.run_effect(approved, 'ROC_bill_vote')
                expected_id = 2 * person + 1 + int(expansion)
                approved.run(approved.effects['ROC_ce_refresh'])
                self.assertEqual(approved.vars['ROC_bill_outcome'], 1)
                self.assertEqual(approved.vars['ROC_bill_stage'], 3)
                self.assertEqual(approved.vars['ROC_bill_id'], expected_id)
                project = 'ROC_econ_' + name + ('_expansion' if expansion else '_pilot')
                other = 'ROC_econ_' + name + ('_pilot' if expansion else '_expansion')
                self.assertFalse(approved.passes(one(self.projects[project], 'visible')))
                self.assertFalse(approved.passes(one(self.projects[project], 'available')))
                self.assertFalse(approved.passes(one(self.projects[other], 'visible')))
                self.assertFalse(approved.passes(one(self.projects[other], 'available')))
                before = approved.pp
                self.run_effect(approved, 'ROC_bill_vote')
                self.assertEqual(approved.pp, before)
                self.assertEqual(approved.vars['ROC_bill_stage'], 3)
                self.assertEqual(approved.vars['ROC_bill_id'], expected_id)
                self.assertEqual(one(self.projects[project], 'cost'),
                                 '35' if not expansion else ('60' if person in (2, 3) else '50'))
                self.assertEqual(one(self.projects[project], 'days_remove'), '180' if expansion else '90')

                # An obsolete action in an existing save may still callback after
                # the update; this is a paid saved action, not a new purchase.
                wrong_saved = self.state(person, expansion)
                wrong_saved.vars.update(ROC_bill_stage=3, ROC_bill_id=expected_id,
                                        ROC_bill_outcome=1, ROC_bill_last_id=expected_id)
                wrong_saved.run(wrong_saved.effects['ROC_ce_refresh'])
                wrong_saved.decisions.add(other)
                wrong_saved.pp -= float(one(self.projects[other], 'cost'))
                self.assertTrue(wrong_saved.passes(one(self.projects[other], 'visible')))
                self.assertFalse(wrong_saved.passes(one(self.projects[other], 'available')))
                wrong_saved.run(one(self.projects[other], 'complete_effect'))
                self.assertEqual(wrong_saved.vars['ROC_bill_stage'], 3)
                self.assertEqual(wrong_saved.vars['ROC_bill_id'], expected_id)

                saved = self.state(person, expansion)
                saved.vars.update(ROC_bill_stage=3, ROC_bill_id=expected_id,
                                  ROC_bill_outcome=1, ROC_bill_last_id=expected_id)
                saved.run(saved.effects['ROC_ce_refresh'])
                saved.decisions.add(project)
                saved.pp -= float(one(self.projects[project], 'cost'))
                paid_pp = saved.pp
                self.assertTrue(saved.passes(one(self.projects[project], 'visible')))
                self.assertFalse(saved.passes(one(self.projects[project], 'available')))
                saved.run(one(self.projects[project], 'complete_effect'))
                self.assertEqual(saved.pp, paid_pp)
                self.assertEqual(saved.vars['ROC_bill_stage'], 0)
                self.assertEqual(saved.vars['ROC_bill_id'], 0)
                saved.run(one(self.projects[project], 'complete_effect'))
                self.assertEqual(saved.vars['ROC_bill_stage'], 0)
                self.assertEqual(saved.vars['ROC_bill_id'], 0)
                actual = saved.vars.get('ROC_ce_actual', 0)
                saved.run(one(self.projects[project], 'remove_effect'))
                self.assertIn('ROC_econ_' + name + ('_expansion' if expansion else '_pilot') + '_done', saved.flags)
                self.assertEqual(saved.vars['ROC_ce_actual'], actual + 2)
                self.assertEqual(saved.pp, paid_pp)

    def test_outcomes_administration_costs_and_audit(self):
        cases = [('vote', 'party', 3, 185, .5, 0),
                 ('conditional', 'signatures', 2, 145, .5, 3),
                 ('force', 'party', 4, 155, .47, 0),
                 ('force', 'materials', 1, 155, .48, 3),
                 ('withdraw', 'signatures', 5, 165, .5, 0)]
        for result, preparation, outcome, pp, stability, stage in cases:
            s = self.state(1)
            self.submit(s)
            self.run_effect(s, 'ROC_bill_prepare_' + preparation)
            self.run_effect(s, 'ROC_bill_' + result)
            self.assertEqual(s.vars['ROC_bill_outcome'], outcome)
            self.assertEqual(s.vars['ROC_bill_stage'], stage)
            self.assertEqual(s.pp, pp)
            self.assertAlmostEqual(s.stability, stability)
            self.assertEqual(s.vars.get('ROC_VAR_youyi_base', 0), 0)
            self.assertEqual('ROC_bill_supervision' in s.flags, result == 'conditional' or (result == 'force' and preparation == 'party'))
            before = (s.pp, s.stability, dict(s.vars))
            self.run_effect(s, 'ROC_bill_' + result)
            self.assertEqual((s.pp, s.stability, s.vars), before)

    def test_administrative_threshold_is_independent_of_party_pressure_and_endings(self):
        s = self.state()
        s.flags.update({'ROC_bill_rural_record', 'ROC_bill_credit_record'})
        self.submit(s)
        self.assertEqual(s.vars['ROC_bill_support'], 1)
        for pressure in (.499, .5, .501):
            s.vars['ROC_VAR_youyi_base'] = pressure
            self.run_effect(s, 'ROC_bill_refresh_support')
            self.assertEqual(s.vars['ROC_bill_requirement'], 2)
        s.flags.add('ROC_bill_supervision')
        self.run_effect(s, 'ROC_bill_refresh_support')
        self.assertEqual(s.vars['ROC_bill_requirement'], 3)
        for ending in ('jixugeming', 'lunliuzuozhuang', 'jingchenghezuo'):
            s.focuses.add(ending)
            self.run_effect(s, 'ROC_bill_refresh_support')
            self.assertEqual(s.vars['ROC_bill_support'], 1)
            self.assertTrue(s.passes([('ROC_bill_valid', 'yes')]))

    def test_invalidations_old_implementation_and_minimum_time(self):
        for invalid in ('minister', 'pending', 'resignation', 'administration', 'term', 'time'):
            s = self.state()
            self.submit(s)
            if invalid == 'minister': s.ideas = {'ROC_idea_XiaoZheng'}
            elif invalid == 'pending': s.flags.add('ROC_econ_conference_pending')
            elif invalid == 'resignation': s.flags.add('ROC_econ_resignation_pending')
            elif invalid == 'administration': s.focuses.discard('gaizaojingjidezhunbei')
            elif invalid == 'term': s.missions.clear()
            else: s.missions['ROC_decision_bop_jingjidahui'] = 89
            self.run_effect(s, 'ROC_bill_daily')
            self.assertEqual(s.vars['ROC_bill_stage'], 0)
            self.assertEqual(s.vars['ROC_bill_outcome'], 5)
            self.assertEqual(s.pp, 185)
        s = self.state()
        s.decisions.add('ROC_econ_yu_pilot')
        self.run_effect(s, 'ROC_bill_daily')
        self.assertIn('ROC_econ_yu_pilot', s.decisions)
        for days, expected in ((103, 0), (104, 1)):
            s = self.state()
            s.missions['ROC_decision_bop_jingjidahui'] = days
            self.run_effect(s, 'ROC_econ_refresh')
            self.run_effect(s, 'ROC_bill_refresh_candidate')
            self.assertEqual(s.vars['ROC_bill_candidate'], expected)

    def test_timeout_and_reset_do_not_restart_term(self):
        s = self.state()
        self.submit(s)
        for _ in range(44): self.run_effect(s, 'ROC_bill_daily')
        self.assertEqual(s.vars['ROC_bill_stage'], 1)
        self.run_effect(s, 'ROC_bill_daily')
        self.assertEqual(s.vars['ROC_bill_stage'], 0)
        self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'], 1000)
        self.assertIn('ROC_bill_submit_cooldown', s.flags)

    def test_events_are_guarded_timed_and_notification_only(self):
        path = ROOT / 'events/ROC_legislation.txt'
        self.assertTrue(path.exists(), 'approval events not implemented')
        entries = read_script(str(path))
        for group in range(1, 6):
            for phase in (1, 2):
                event = named_event(entries, f'ROC_legislation.{group}{phase}')
                self.assertEqual(one(event, 'timeout_days'), '7')
                for key, option in event:
                    if key == 'option':
                        self.assertNotEqual(one(event, 'desc'), one(option, 'name'),
                                            'Event prose must not reuse an option localization key.')
                        s = self.state()
                        for k, effect in option:
                            if k == 'hidden_effect': s.run(effect)
                        self.assertEqual(s.pp, 200)
                        self.assertEqual(s.stability, .5)
        for outcome in range(101, 105):
            event = named_event(entries, 'ROC_legislation.' + str(outcome))
            self.assertFalse(any(key == 'immediate' for key, _ in event))
            self.assertEqual(one(one(event, 'option'), 'name'), f'ROC_legislation.{outcome}.a')

    def test_category_split_and_cooperation_record_source(self):
        categories = dict(read_script('common/decisions/categories/ROC.txt'))
        self.assertEqual(one(categories['ROC_economic_administration'],'scripted_gui'),'ROC_central_economy_window')
        self.assertEqual(one(categories['ROC_economic_administration'], 'visible_when_empty'), 'yes',
                         'The committee overview must remain after faction missions end.')
        decisions = dict(economic_decisions())
        for ident, record in [('ROC_allied_worker_coordination', 'worker'), ('ROC_allied_rural_cooperation', 'rural'),
                              ('ROC_allied_labor_arbitration', 'arbitration'), ('ROC_allied_commercial_credit', 'credit')]:
            s = self.state()
            s.focuses.add('lianluogemingyoudang')
            s.run(one(decisions[ident], 'cancel_effect'))
            self.assertNotIn('ROC_bill_' + record + '_record', s.flags)
            s.run(one(decisions[ident], 'remove_effect'))
            self.assertEqual(s.flag_days['ROC_bill_' + record + '_record'], 180)

    def test_stale_windows_have_close_option_without_new_proposal_side_effects(self):
        entries = read_script('events/ROC_legislation.txt')
        for group in range(1, 6):
            for phase in (1, 2):
                event = named_event(entries, f'ROC_legislation.{group}{phase}')
                close = next(option for key, option in event if key == 'option' and one(option, 'name') == 'ROC_bill_stale_close')
                s = self.state((group - 1 + 1) % 5)
                self.submit(s)
                self.assertTrue(s.passes(one(close, 'trigger')))
                self.assertFalse(any(k == 'hidden_effect' for k, _ in close))
                for key, option in event:
                    if key == 'option':
                        before = (s.pp, s.stability, dict(s.vars), list(s.events))
                        for k, effect in option:
                            if k == 'hidden_effect': s.run(effect)
                        self.assertEqual((s.pp, s.stability, s.vars, s.events), before)

    def test_force_affordability_preserves_administrative_result(self):
        for prepared, boundary in ((True, 20), (False, 30)):
            for pp, allowed in ((boundary - 1, False), (boundary, True)):
                s = self.state(1)
                self.submit(s)
                self.run_effect(s, 'ROC_bill_prepare_' + ('materials' if prepared else 'party'))
                s.pp = pp
                self.assertEqual(s.passes([('ROC_bill_force_ready', 'yes')]), prepared)
                self.assertEqual(s.passes([('ROC_bill_force_affordable', 'yes')]), allowed)
                self.run_effect(s, 'ROC_bill_force')
                if allowed:
                    self.assertEqual(s.pp, 0)
                    self.assertEqual(s.vars['ROC_bill_outcome'], 1 if prepared else 4)
                else:
                    self.assertEqual(s.pp, pp)
                    self.assertEqual(s.stability, .5)
                    self.assertEqual(s.vars['ROC_bill_stage'], 2)

    def test_exact_submission_and_preparation_funds(self):
        s = self.state()
        self.run_effect(s, 'ROC_bill_refresh_candidate')
        for pp, can in ((14, False), (15, True)):
            s.pp = pp
            self.assertEqual(s.passes([('ROC_bill_submit_ready', 'yes')]), can)
        self.submit(s)
        self.assertEqual(s.pp, 0)
        self.assertEqual(s.vars['ROC_bill_stage'], 1)
        s.pp = 9
        self.run_effect(s, 'ROC_bill_prepare_materials')
        self.assertEqual(s.pp, 9)
        self.assertEqual(s.vars['ROC_bill_stage'], 1)
        s.pp = 10
        self.run_effect(s, 'ROC_bill_prepare_materials')
        self.assertEqual(s.pp, 0)
        self.assertEqual(s.vars['ROC_bill_stage'], 2)

    def test_old_paid_project_stays_unavailable_but_settles_once_from_saved_timer(self):
        s = self.state()
        s.run(s.effects['ROC_ce_refresh'])
        s.decisions.add('ROC_econ_yu_pilot')
        saved = self.projects['ROC_econ_yu_pilot']
        self.assertTrue(s.passes(one(saved, 'visible')))
        self.assertFalse(s.passes(one(saved, 'available')))
        paid_pp = s.pp - float(one(saved, 'cost'))
        s.pp = paid_pp
        self.run_effect(s, 'ROC_bill_daily')
        s.run(one(saved, 'remove_effect'))
        self.assertIn('ROC_econ_yu_pilot_done', s.flags)
        self.assertEqual(s.vars.get('ROC_econ_pending_shift',0),0)
        self.assertEqual(s.vars['ROC_ce_actual'],2)
        self.assertEqual(s.pp, paid_pp)

    def test_failed_force_creates_audit_without_party_pressure(self):
        for person in (1, 2):
            s = self.state(person)
            self.submit(s)
            self.run_effect(s, 'ROC_bill_prepare_party')
            self.run_effect(s, 'ROC_bill_force')
            self.assertEqual(s.vars.get('ROC_VAR_zuoyi_base', 0), 0)
            self.assertEqual(s.vars.get('ROC_VAR_youyi_base', 0), 0)
            self.assertIn('ROC_bill_supervision', s.flags)

    def test_three_endings_keep_approval_and_term(self):
        for ending in ('jixugeming', 'lunliuzuozhuang', 'jingchenghezuo'):
            s = self.state()
            s.focuses.add(ending)
            s.focuses.add('qianghuazhengzhituanjie')
            self.submit(s)
            self.run_effect(s, 'ROC_bill_prepare_materials')
            self.run_effect(s, 'ROC_bill_vote')
            self.assertEqual(s.vars['ROC_bill_stage'], 3)
            self.run_effect(s, 'ROC_econ_finish_race')
            self.run_effect(s, 'ROC_bill_daily')
            self.assertEqual(s.vars['ROC_bill_stage'], 3)
            self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'], 1000)

    def test_approval_boundary_and_supervision_raise_future_requirement(self):
        # A low-conflict policy pilot reaches administration but still lacks an industry guarantee.
        s = self.state(1)
        self.submit(s)
        self.run_effect(s, 'ROC_bill_prepare_party')
        self.assertEqual(s.vars['ROC_bill_requirement'], 2)
        self.assertEqual(s.vars['ROC_bill_support'], 1)
        before = s.pp
        self.run_effect(s, 'ROC_bill_conditional')
        self.assertEqual(s.vars['ROC_bill_stage'], 2)
        self.assertEqual(s.pp, before)
        # Expansion with industry guarantees can be tried under an existing fiscal audit.
        s = self.state(expansion=True)
        s.flags.add('ROC_bill_supervision')
        self.submit(s)
        self.run_effect(s, 'ROC_bill_prepare_signatures')
        self.assertEqual(s.vars['ROC_bill_requirement'], 4)
        self.assertEqual(s.vars['ROC_bill_support'], 3)
        before = s.pp
        self.run_effect(s, 'ROC_bill_conditional')
        self.assertEqual(s.vars['ROC_bill_stage'], 3)
        self.assertEqual(s.pp, before - 20)
        self.assertEqual(s.flag_days['ROC_bill_supervision'], 180)
        self.run_effect(s, 'ROC_bill_invalidate')
        s.flags.discard('ROC_bill_submit_cooldown')
        self.submit(s)
        self.assertEqual(s.vars['ROC_bill_requirement'], 4)

    def test_industry_cooperation_record_expires_without_changing_administration(self):
        decisions = dict(economic_decisions())
        s = self.state(1)
        s.focuses.add('lianluogemingyoudang')
        s.run(one(decisions['ROC_allied_labor_arbitration'], 'remove_effect'))
        self.submit(s)
        self.assertEqual(s.vars['ROC_bill_support'], 1)
        s.focuses.add('lunliuzuozhuang')
        self.run_effect(s, 'ROC_bill_refresh_support')
        self.assertEqual(s.vars['ROC_bill_support'], 1)
        self.assertEqual(s.flag_days['ROC_bill_arbitration_record'], 180)
        s.flags.discard('ROC_bill_arbitration_record')
        self.run_effect(s, 'ROC_bill_refresh_support')
        self.assertEqual(s.vars['ROC_bill_support'], 1)

    def test_new_term_and_reappointment_cancel_approved_bill_without_reward(self):
        for effect in ('ROC_econ_clear_term_projects', 'ROC_econ_direct_appointment_refresh', 'ROC_econ_remove_ministers'):
            s = self.state()
            s.focuses.add('qianghuazhengzhituanjie')
            self.submit(s)
            self.run_effect(s, 'ROC_bill_prepare_materials')
            self.run_effect(s, 'ROC_bill_vote')
            self.assertEqual(s.vars['ROC_bill_stage'], 3)
            self.run_effect(s, effect)
            self.assertEqual(s.vars['ROC_bill_stage'], 0)
            self.assertEqual(s.vars['ROC_bill_outcome'], 5)
            self.assertEqual(s.vars.get('ROC_econ_pending_shift', 0), 0)
            self.assertEqual(s.missions['ROC_decision_bop_jingjidahui'], 1000)

    def test_administrative_approval_does_not_shorten_political_agenda(self):
        for force in (False, True):
            s = self.state()
            s.missions['ROC_decision_zhongpai'] = 2
            s.vars['ROC_econ_center_help_used'] = 29
            self.submit(s)
            self.run_effect(s, 'ROC_bill_prepare_materials')
            effect = 'ROC_bill_force' if force else 'ROC_bill_vote'
            self.run_effect(s, effect)
            self.run_effect(s, effect)
            self.assertEqual(s.missions['ROC_decision_zhongpai'], 2)
            self.assertEqual(s.vars['ROC_econ_center_help_used'], 29)

    def test_rules_have_bom_unique_keys_and_cover_core_tooltips(self):
        from test_sichuan_red_opportunity import parse_localization
        p = ROOT / 'localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml'
        data = p.read_bytes()
        self.assertTrue(data.startswith(b'\xef\xbb\xbf'))
        localized, duplicates = parse_localization(data)
        self.assertEqual([key for key in duplicates if key.startswith("ROC_bill_")], [])
        for path in ('events/ROC_legislation.txt', 'common/decisions/ROC.txt'):
            for key, value in walk(read_script(path)):
                if key in ('custom_effect_tooltip', 'tooltip'):
                    self.assertIn(value, localized)

    def test_submission_cannot_charge_for_a_stale_candidate(self):
        s = self.state()
        self.run_effect(s, 'ROC_bill_refresh_candidate')
        self.assertEqual(s.vars['ROC_bill_candidate'], 1)
        s.ideas = {'ROC_idea_XiaoZheng'}
        self.assertFalse(s.passes([('ROC_bill_submit_ready', 'yes')]))
        self.run_effect(s, 'ROC_bill_refresh_candidate')
        self.assertEqual(s.vars['ROC_bill_candidate'], 9)
        self.assertTrue(s.passes([('ROC_bill_submit_ready', 'yes')]))

    def test_stale_close_uses_explicit_conjunction_and_each_failure_branch(self):
        event = named_event(read_script('events/ROC_legislation.txt'), 'ROC_legislation.11')
        close = next(option for key, option in event if key == 'option' and one(option, 'name') == 'ROC_bill_stale_close')
        guard = one(one(close, 'trigger'), 'NOT')
        self.assertEqual(len(guard), 1, 'NOT must contain a single explicit AND, not multiple trigger children')
        self.assertEqual(len(one(guard, 'AND')), 3)
        for failure in ('valid', 'stage', 'id'):
            s = self.state(4 if failure == 'id' else 0)
            self.submit(s)
            if failure == 'valid': s.ideas.clear()
            elif failure == 'stage': self.run_effect(s, 'ROC_bill_prepare_party')
            self.assertTrue(s.passes(one(close, 'trigger')), failure)

if __name__ == '__main__': unittest.main()
