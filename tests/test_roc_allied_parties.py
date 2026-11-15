"""Static contract checks for ROC's allied-party meeting and projects."""

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import re
import unittest

from test_sichuan_red_opportunity import parse_clausewitz, parse_localization


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = {
    "ROC_allied_worker_coordination": {
        "cost": "35",
        "days_remove": "45",
        "days_re_enable": "120",
        "modifier": {
            "industrial_capacity_factory": "0.05",
            "production_factory_efficiency_gain_factor": "0.03",
        },
        "end_tooltip": "ROC_allied_worker_coordination_end_tt",
        "bop": "0.03",
        "variables": {"ROC_VAR_zuoyi_base": "-0.04", "ROC_VAR_youyi_base": "0.02"},
    },
    "ROC_allied_rural_cooperation": {
        "cost": "45",
        "days_remove": "60",
        "days_re_enable": "150",
        "modifier": {
            "production_speed_infrastructure_factor": "0.10",
            "consumer_goods_factor": "-0.03",
        },
        "end_tooltip": "ROC_allied_rural_cooperation_end_tt",
        "bop": "0.02",
        "variables": {"ROC_VAR_zuoyi_base": "-0.02", "ROC_VAR_youyi_base": "0.01"},
    },
    "ROC_allied_labor_arbitration": {
        "cost": "40",
        "days_remove": "45",
        "days_re_enable": "150",
        "modifier": {"stability_factor": "0.03", "industrial_capacity_factory": "-0.02"},
        "end_tooltip": "ROC_allied_labor_arbitration_end_tt",
        "bop": None,
        "variables": {"ROC_VAR_zuoyi_base": "-0.03", "ROC_VAR_youyi_base": "-0.03"},
    },
}
OPTION_KEYS = {
    "ROC_allied_parties_meeting_workers": "20",
    "ROC_allied_parties_meeting_rural": "15",
    "ROC_allied_parties_meeting_consultation": "25",
}


@lru_cache(maxsize=None)
def _parsed_script(path):
    return parse_clausewitz((ROOT / path).read_text(encoding="utf-8-sig"), path)


def read_script(path):
    # Tests may modify parsed blocks; keep the cached source private.
    return deepcopy(_parsed_script(str(path)))


def one(entries, key):
    values = [value for name, value in entries if name == key]
    if len(values) != 1:
        raise AssertionError(f"expected one {key}, found {len(values)}")
    return values[0]


def economic_decisions():
    # A shared decision category spans several blocks in the merged file.
    entries = read_script("common/decisions/ROC.txt")
    return [decision for key, block in entries if key == "ROC_economic_administration" for decision in block]


def trigger_passes(entries, active_projects):
    for key, value in entries:
        if key == "NOT":
            if trigger_passes(value, active_projects):
                return False
        elif key == "OR":
            if not any(trigger_passes([branch], active_projects) for branch in value):
                return False
        elif key == "has_decision":
            if value not in active_projects:
                return False
        else:
            raise AssertionError(f"unsupported busy trigger condition {key}")
    return True


def named_event(events, event_id):
    matches = [
        value
        for name, value in events
        if name == "country_event"
        and isinstance(value, list)
        and any(key == "id" and item == event_id for key, item in value)
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one {event_id} event, found {len(matches)}")
    return matches[0]


def read_event(event_id):
    path = ROOT / "events/ROC.txt"
    text = path.read_text(encoding="utf-8-sig")
    pattern = re.compile(
        rf"(?ms)^country_event\s*=\s*\{{[^\n]*\n(?:(?!^country_event\s*=).)*?"
        rf"^[\t ]*id\s*=\s*{re.escape(event_id)}\b(?:(?!^country_event\s*=).)*?^\}}"
    )
    match = pattern.search(text)
    if not match:
        raise AssertionError(f"could not isolate {event_id}")
    return one(parse_clausewitz(match.group(), str(path)), "country_event")


def named_effect(entries, key):
    matches = [value for name, value in entries if name == key]
    if len(matches) != 1 or not isinstance(matches[0], list):
        raise AssertionError(f"expected one {key} block")
    return matches[0]


class RocAlliedPartiesContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_roc_economic_council import ScriptState
        cls.State = ScriptState
        cls.effects = dict(read_script('common/scripted_effects/ROC_scripted_effects.txt'))
        cls.effects.update(dict(read_script('common/scripted_triggers/ROC_economic_council.txt')))
        cls.effects.update(dict(read_script('common/scripted_effects/ROC_scripted_effects.txt')))
        cls.effects.update(dict(read_script('common/scripted_triggers/ROC_legislation.txt')))
        cls.event = read_event('ROC_pingheng.50')
        cls.decisions = {key: value for key, value in economic_decisions() if key.startswith('ROC_allied_')}
        cls.localized = parse_localization((ROOT / 'localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml').read_bytes())

    def test_old_focus_unlocks_four_projects_independent_of_committee_exit_with_busy_guard(self):
        expected=set(PROJECTS)|{'ROC_allied_commercial_credit'}
        self.assertEqual(set(self.decisions),expected)
        for ident,block in self.decisions.items():
            state=self.State(self.effects)
            state.focuses.update({'gaizaojingjidezhunbei','lianluogemingyoudang'})
            self.assertTrue(state.passes(one(block,'available')),ident)
            for active in expected:
                state.decisions={active}
                self.assertFalse(state.passes(one(block,'available')),ident)
            state.decisions.clear();state.focuses.add('jixugeming')
            self.assertTrue(state.passes(one(block,'visible')),ident)
            self.assertFalse(state.passes(one(block,'cancel_trigger')),ident)
            state.focuses.discard('gaizaojingjidezhunbei')
            self.assertTrue(state.passes(one(block,'cancel_trigger')),ident)
            self.assertEqual(one(block,'cancel_effect'),[])
        legacy=one(read_script('common/decisions/categories/ROC.txt'),'ROC_allied_parties_category')
        self.assertEqual(one(legacy,'visible'),[('always','no')])

    def test_project_values_modifiers_central_support_and_guarded_end_effects(self):
        expected=dict(PROJECTS)
        expected['ROC_allied_commercial_credit']={'cost':'40','days_remove':'60','days_re_enable':'150','modifier':{'production_speed_industrial_complex_factor':'0.05','political_power_cost':'0.1'}}
        for ident,values in expected.items():
            block=self.decisions[ident]
            for key in ('cost','days_remove','days_re_enable'):self.assertEqual(one(block,key),values[key])
            self.assertEqual(dict(one(block,'modifier')),values['modifier'])
            state=self.State(self.effects);state.focuses.update({'gaizaojingjidezhunbei','lianluogemingyoudang','gemingweiyuanhui'})
            state.missions.update(ROC_decision_bop_jingjidahui=1000,ROC_decision_zhongpai=20)
            state.run(one(block,'remove_effect'))
            self.assertEqual(state.axis,0)
            self.assertEqual(state.vars.get('ROC_econ_pending_shift',0),0)
            self.assertGreater(state.vars.get('ROC_ma_left_favor',0)+state.vars.get('ROC_ma_right_favor',0),0)
            self.assertEqual(state.missions['ROC_decision_zhongpai'],20)
            self.assertNotIn('ROC_VAR_zuoyi_base',state.vars)
            self.assertNotIn('ROC_VAR_youyi_base',state.vars)
            state.focuses.discard('gaizaojingjidezhunbei');before=dict(state.vars)
            state.run(one(block,'remove_effect'));self.assertEqual(state.vars,before)

    def test_meeting_effects_and_chinese_localization_are_complete(self):
        self.assertEqual(one(self.event, 'title'), 'ROC_pingheng.50.t')
        self.assertEqual(one(self.event, 'fire_only_once'), 'yes')
        self.assertEqual(one(self.event, 'is_triggered_only'), 'yes')
        options = {one(option, 'name'): option for key, option in self.event if key == 'option'}
        self.assertEqual(set(options), set(OPTION_KEYS))
        for ident, power in OPTION_KEYS.items():
            self.assertEqual(one(options[ident], 'add_political_power'), power)
        self.assertIn(('ROC_econ_shift_public_030', 'yes'), options['ROC_allied_parties_meeting_workers'])
        localized, duplicates = self.localized
        self.assertEqual([key for key in duplicates if key.startswith(("ROC_allied_", "ROC_pingheng.50."))], [])
        self.assertTrue((ROOT / 'localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml').read_bytes().startswith(b'\xef\xbb\xbf'))
        for ident in self.decisions:
            self.assertIn(ident, localized)
            self.assertIn(ident + '_desc', localized)
        meeting_desc = localized['ROC_allied_parties_meeting_desc']
        for topic in ('\u751f\u4ea7\u534f\u4f5c', '\u519c\u6751\u4e92\u52a9', '\u4ef2\u88c1\u89c4\u5219', '\u5de5\u5546\u4fe1\u7528'):
            self.assertIn(topic, meeting_desc)


if __name__ == '__main__':
    unittest.main()
