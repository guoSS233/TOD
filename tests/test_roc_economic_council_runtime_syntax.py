"""Regression checks for syntax rejected in the 2026-10-03 engine log.

These checks validate documented forms and simulate transitions; they do not
load the game or claim to validate its complete parser.
"""
import unittest

from test_roc_allied_parties import economic_decisions, ROOT, one, read_script
from test_roc_economic_council import ScriptState
from test_sichuan_red_opportunity import Comparison, parse_clausewitz

UTF8_BOM = b'\xef\xbb\xbf'


def walk(entries):
    for key, value in entries:
        yield key, value
        if isinstance(value, list):
            yield from walk(value)


class EconomicCouncilRuntimeSyntax(unittest.TestCase):
    def test_committee_executable_scripts_have_no_utf8_bom(self):
        paths = (
            'common/scripted_effects/ROC_scripted_effects.txt',
            'common/scripted_triggers/ROC_committee.txt',
            'events/ROC_committee.txt',
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertFalse((ROOT / path).read_bytes().startswith(UTF8_BOM))

    def test_committee_localization_keeps_utf8_bom(self):
        paths = (
            'localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml',
            'localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml',
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).read_bytes().startswith(UTF8_BOM))

    def test_controller_uses_engine_supported_check_variable_forms(self):
        paths = (
            'common/scripted_effects/ROC_scripted_effects.txt',
            'common/scripted_triggers/ROC_minister_agenda.txt',
            'common/decisions/ROC.txt',
            'events/ROC_minister_agenda.txt',
            'common/scripted_effects/ROC_scripted_effects.txt',
            'common/ideas/ROC_economic_structure.txt',
            'common/scripted_effects/ROC_scripted_effects.txt',
            'common/scripted_triggers/ROC_central_economy.txt',
            'common/decisions/ROC.txt',
            'events/ROC_central_economy.txt',
            'common/decisions/ROC.txt',
            'common/scripted_effects/ROC_scripted_effects.txt',
            'common/scripted_localisation/ROC_scripted_localisation.txt',
            'common/scripted_triggers/ROC_economic_council.txt',
            'common/on_actions/ROC_economic_council.txt',
            'events/ROC_economic_council.txt',
            'common/decisions/ROC.txt',
            'common/scripted_effects/ROC_scripted_effects.txt',
            'common/scripted_triggers/ROC_legislation.txt',
            'events/ROC_legislation.txt',
            'common/scripted_effects/ROC_scripted_effects.txt',
            'common/scripted_triggers/ROC_committee.txt',
            'events/ROC_committee.txt',
        )
        for path in paths:
            for key, value in walk(read_script(path)):
                if key != 'check_variable':
                    continue
                with self.subTest(path=path, block=value):
                    fields = dict(value)
                    if 'var' in fields:
                        self.assertIn('value', fields)
                        self.assertIn(fields.get('compare', 'equals'), {
                            'equals', 'not_equals', 'less_than',
                            'less_than_or_equals', 'greater_than',
                            'greater_than_or_equals',
                        })
                        self.assertFalse(any(isinstance(v, Comparison) for v in fields.values()))
                    else:
                        self.assertEqual(len(value), 1)
                        limit = value[0][1]
                        if isinstance(limit, Comparison):
                            self.assertIn(limit.operator, {'=', '<', '>'})

    def test_minister_credit_loop_uses_the_documented_engine_effect(self):
        # Installation documentation/effects_documentation.md names
        # while_loop_effect; accepting Python-like "while" in our test parser
        # would otherwise hide an unsupported effect from these simulations.
        script = read_script('common/scripted_effects/ROC_scripted_effects.txt')
        self.assertFalse(any(key == 'while' for key, _ in walk(script)))

    def test_legacy_economic_effects_never_write_native_axis(self):
        effects=read_script('common/scripted_effects/ROC_scripted_effects.txt')
        self.assertFalse(any(key=='add_power_balance_value' for key,value in walk(effects)))

    def test_simulator_rejects_unsupported_check_variable_shorthand(self):
        state = ScriptState({}, counter=90)
        for operator in ('>=', '<='):
            with self.subTest(operator=operator):
                block = parse_clausewitz(f'check_variable = {{ counter {operator} 90 }}', 'regression')
                with self.assertRaisesRegex(AssertionError, 'unsupported.*check_variable'):
                    state.passes(block)

    def test_explicit_comparisons_cover_inclusive_boundaries(self):
        state = ScriptState({}, counter=90, other=90)
        for compare, expected in (
            ('equals', True), ('not_equals', False), ('less_than', False),
            ('less_than_or_equals', True), ('greater_than', False),
            ('greater_than_or_equals', True),
        ):
            with self.subTest(compare=compare):
                block = parse_clausewitz(
                    'check_variable = { var = counter value = other compare = ' + compare + ' }',
                    'regression',
                )
                self.assertEqual(state.passes(block), expected)

    def test_simulator_rejects_variable_references_for_bop_effects(self):
        state = ScriptState({}, delta=.004)
        for value in ('var:delta', 'delta'):
            with self.subTest(value=value):
                with self.assertRaisesRegex(AssertionError, 'unsupported.*add_power_balance_value'):
                    state.run(parse_clausewitz(
                        'add_power_balance_value = { id = ROC_power_balance value = ' + value + ' }',
                        'regression'))
        state.run(parse_clausewitz(
            'add_power_balance_value = { id = ROC_power_balance value = 0.004 }', 'regression'))
        self.assertAlmostEqual(state.axis, .004)

    def test_personal_projects_stay_retired_and_keep_saved_durations(self):
        effects = {}
        effects.update(dict(read_script('common/scripted_effects/ROC_scripted_effects.txt')))
        for filename in ('ROC_economic_council.txt', 'ROC_legislation.txt'):
            effects.update(dict(read_script('common/scripted_triggers/' + filename)))
        decisions = economic_decisions()
        profile_ids = {'yu': 1, 'yan': 2, 'ruan': 3, 'chen': 4, 'xiao': 5}
        bill_ids = {'yu': 1, 'yan': 3, 'ruan': 5, 'chen': 7, 'xiao': 9}
        covered = set()
        for ident, decision in decisions:
            if not ident.startswith('ROC_econ_') or not ident.endswith(('_pilot', '_expansion')):
                continue
            person, kind = ident.removeprefix('ROC_econ_').split('_')
            minister = {'yu': 'YuShude', 'yan': 'YanYangchu', 'ruan': 'RuanXiaoxian',
                        'chen': 'ChenZanxian', 'xiao': 'XiaoZheng'}[person]
            days = 90 if kind == 'pilot' else 180
            state = ScriptState(
                effects,
                ROC_ce_minister_profile_id=profile_ids[person],
                ROC_econ_stage=2,
                ROC_econ_term_remaining=1095,
                ROC_bill_stage=3,
                ROC_bill_outcome=1,
                ROC_bill_id=bill_ids[person] + (kind == 'expansion'),
            )
            state.focuses.add('gaizaojingjidezhunbei')
            state.ideas.add('ROC_idea_' + minister)
            state.missions['ROC_decision_bop_jingjidahui'] = 1095
            if kind == 'expansion':
                state.flags.add('ROC_econ_' + person + '_pilot_done')
                state.focuses.add({'yu':'tuidongnongyehezuoshefazhan','yan':'tuidongxiangcunjiansheyundong','ruan':'qianghuagonghuiquanli','chen':'qianghuagonghuiquanli','xiao':'kuodamincuhuifanwei'}[person])
            self.assertEqual(one(decision, 'days_remove'), str(days))
            covered.add(ident)
            for remaining in (days - 1, days, days + 1):
                state.vars['ROC_econ_term_remaining'] = remaining
                with self.subTest(decision=ident, remaining=remaining):
                    self.assertFalse(state.passes(one(decision, 'visible')))
                self.assertFalse(state.passes(one(decision, 'available')))

            # A saved in-flight decision may remain visible to its current minister,
            # but approval flags and the old timer can never offer another purchase.
            state.decisions.add(ident)
            self.assertTrue(state.passes(one(decision, 'visible')))
            self.assertFalse(state.passes(one(decision, 'available')))
        self.assertEqual(len(covered), 10)

    def test_monthly_compatibility_refresh_never_changes_native_axis(self):
        effects=dict(read_script('common/scripted_effects/ROC_scripted_effects.txt'))
        for axis in (-1,-.996,0,.996,1):
            state=ScriptState(effects);state.axis=axis
            state.run(effects['ROC_econ_apply_monthly'])
            self.assertEqual(state.axis,axis)
            self.assertEqual(state.bop_add_calls,0)

    def test_head_status_localisation_preserves_90_day_threshold(self):
        entries = read_script('common/scripted_localisation/ROC_scripted_localisation.txt')
        head = next(value for key, value in entries if key == 'defined_text'
                    and one(value, 'name') == 'ROC_econ_gui_head_status')
        for days, expected in ((0, 'no_pending'), (89, 'mismatch'), (90, 'crisis'), (91, 'crisis')):
            state = ScriptState({}, ROC_econ_head_mismatch_days=days)
            selected = next(one(value, 'localization_key') for key, value in head
                            if key == 'text' and state.passes(one(value, 'trigger')))
            self.assertEqual(selected, 'ROC_econ_gui_head_' + expected)

    def test_refresh_exposes_100_frame_values_without_changing_ratios(self):
        effects = dict(read_script('common/scripted_effects/ROC_scripted_effects.txt'))
        for axis, remaining, term_ratio, axis_ratio in (
            (0, None, 0, .5), (0, 547.5, .5, .5),
            (-1, 1095, 0, 0), (1, 0, 1, 1),
            (-1.1, 1200, 0, -.05), (1.1, -1, 1, 1.05),
        ):
            state = ScriptState(effects)
            state.axis = axis
            if remaining is not None:
                state.missions['ROC_decision_bop_jingjidahui'] = remaining
            state.run(effects['ROC_econ_refresh'])
            with self.subTest(axis=axis, remaining=remaining):
                self.assertAlmostEqual(state.vars['ROC_econ_term_progress'], term_ratio)
                self.assertEqual(state.vars['ROC_econ_axis_progress'], .5)
                self.assertIn('ROC_econ_term_frame', state.vars)
                self.assertIn('ROC_econ_axis_frame', state.vars)
                self.assertAlmostEqual(state.vars['ROC_econ_term_frame'], term_ratio * 100)
                self.assertAlmostEqual(state.vars['ROC_econ_axis_frame'],
                                       50)


if __name__ == '__main__':
    unittest.main()
