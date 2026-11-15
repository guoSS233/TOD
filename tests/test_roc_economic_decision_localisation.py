"""Localization contracts for ROC minister focus decision unlock feedback."""

from collections import Counter
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
FOCUS_FILE = ROOT / "common/national_focus/ROC_minister_agenda.txt"
SCRIPTED_LOCALISATION = ROOT / "common/scripted_localisation/ROC_scripted_localisation.txt"
LOCALISATION_FILES = (
    ROOT / "localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml",
)
FLAG_TOKEN_SOURCES = (
    (
        ROOT / "common/decisions/categories/ROC.txt",
        ("FLAG_ROC_decision_gonggubianjie_unlocked", "FLAG_ROC_decision_beifa_unlocked"),
    ),
    (
        ROOT / "common/scripted_triggers/ROC_central_economy.txt",
        ("ROC_ce_survey_done",),
    ),
)
LOC_LINE = re.compile(r'^\s*([\w.\-]+):0\s+"(.*)"\s*$')

# Static expected unlock map from the assigned gate specification. The
# decision gates are being edited separately, so this remains independent of
# their implementation while checking the user-facing feedback.
EXPECTED_UNLOCKS = {
    "ROC_ma_yu_1": (
        "于树德：合作社信用", "筹办实业", "疏通商路", "支持民营信贷",
    ),
    "ROC_ma_yu_step2": ("于树德：城乡采购",),
    "ROC_ma_yu_2": ("兴修农田",),
    "ROC_ma_yan_1": ("晏阳初：乡村调查", "兴修农田", "疏通商路"),
    "ROC_ma_yan_step2": ("晏阳初：农技推广",),
    "ROC_ma_yan_2": ("筹办实业", "促进产业技术协作"),
    "ROC_ma_ruan_1": ("阮啸仙：预算稽核", "筹办实业", "疏通商路", "国企税收减免"),
    "ROC_ma_ruan_step2": ("阮啸仙：决算核查", "农业经营：推行集体化经营"),
    "ROC_ma_ruan_2": ("兴修农田", "重点产业公私合营"),
    "ROC_ma_chen_1": ("陈赞贤：工资核验", "筹办实业", "疏通商路", "扩大工人参与管理"),
    "ROC_ma_chen_step2": ("陈赞贤：生产协定", "农业经营：推行集体化经营"),
    "ROC_ma_chen_2": ("兴修农田", "国企税收减免", "重点产业公私合营"),
    "ROC_ma_chen_step4": ("促进产业技术协作",),
    "ROC_ma_xiao_1": ("萧铮：地籍复核", "兴修农田", "疏通商路"),
    "ROC_ma_xiao_step2": ("萧铮：小农市场", "农业经营：实行包产到户"),
    "ROC_ma_xiao_2": ("筹办实业", "支持民营信贷"),
    "ROC_ma_xiao_step4": ("重组低效国企",),
}

REQUIRED_LOCALIZATION_KEYS = (
    "ROC_ma_decision_available_tt",
    "ROC_ma_focus_unlocked_tt",
    "ROC_ma_current_action",
    "ROC_ma_current_action_desc",
    "ROC_ma_adopt_agriculture_available_tt",
    "ROC_ce_administration_active_tt",
    "ROC_ce_administration_inactive_tt",
    "ROC_ce_survey_done",
    "FLAG_ROC_decision_gonggubianjie_unlocked",
    "FLAG_ROC_decision_beifa_unlocked",
)


def read_localizations():
    values = {}
    occurrences = Counter()
    for path in LOCALISATION_FILES:
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            match = LOC_LINE.match(line)
            if match:
                key, value = match.groups()
                occurrences[key] += 1
                values[key] = value
    return values, occurrences


def balanced_block(source, opening_index):
    depth = 0
    for index in range(opening_index, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[opening_index:index + 1]
    raise AssertionError("unclosed Clausewitz block")


def focus_blocks():
    source = FOCUS_FILE.read_text(encoding="utf-8-sig")
    for match in re.finditer(r"(?m)^shared_focus\s*=\s*\{", source):
        block = balanced_block(source, match.end() - 1)
        focus_id = re.search(r"\bid\s*=\s*([A-Za-z0-9_]+)", block)
        if focus_id:
            yield focus_id.group(1), block


class RocEconomicDecisionLocalizationTests(unittest.TestCase):
    def test_required_keys_exist_once_and_yaml_files_keep_utf8_bom(self):
        loc, occurrences = read_localizations()
        for path in LOCALISATION_FILES:
            with self.subTest(file=path.name):
                self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))
        for key in REQUIRED_LOCALIZATION_KEYS:
            with self.subTest(key=key):
                self.assertTrue(key in loc, f"missing localization key {key}")
                self.assertEqual(occurrences[key], 1)
        self.assertFalse(
            "FLAG_ROC_ce_survey_done" in loc,
            "ROC_ce_survey_done uses its exact country-flag token without FLAG_",
        )
        self.assertIn("中央经济施政不再有效", loc["ROC_ce_administration_inactive_tt"])

    def test_flag_localizations_match_the_actual_roc_flag_tokens(self):
        loc, _ = read_localizations()
        for path, flags in FLAG_TOKEN_SOURCES:
            source = path.read_text(encoding="utf-8-sig")
            actual_flags = set(
                re.findall(r"\bhas_country_flag\s*=\s*([A-Za-z0-9_]+)", source)
            )
            for flag in flags:
                with self.subTest(flag=flag):
                    self.assertIn(flag, actual_flags)
                    self.assertTrue(flag in loc, f"missing exact flag localization {flag}")

    def test_dynamic_mission_name_returns_a_real_focus_label_without_recursion(self):
        loc, _ = read_localizations()
        self.assertEqual(loc["ROC_ma_current_action"], "[ROOT.ROC_ma_current_action]")
        self.assertIn("自动", loc["ROC_ma_current_action_desc"])
        self.assertTrue(
            "委员会" in loc["ROC_ma_current_action_desc"]
            or "三派" in loc["ROC_ma_current_action_desc"]
        )
        self.assertIn("项目", loc["ROC_ma_current_action_desc"])

        source = SCRIPTED_LOCALISATION.read_text(encoding="utf-8-sig")
        matching = []
        for match in re.finditer(r"(?m)^defined_text\s*=\s*\{", source):
            block = balanced_block(source, match.end() - 1)
            name = re.search(r"\bname\s*=\s*([A-Za-z0-9_]+)", block)
            if name and name.group(1) == "ROC_ma_current_action":
                matching.append(block)
        self.assertEqual(len(matching), 1)
        return_keys = re.findall(
            r"\blocalization_key\s*=\s*([A-Za-z0-9_]+)", matching[0]
        )
        self.assertTrue(return_keys)
        self.assertNotIn("ROC_ma_current_action", return_keys)
        for key in return_keys:
            with self.subTest(return_key=key):
                self.assertTrue(
                    key in loc, f"missing scripted localization key {key}"
                )

    def test_focus_unlock_tooltips_match_the_static_expected_gate_map(self):
        loc, occurrences = read_localizations()
        definitions = dict(focus_blocks())
        self.assertTrue(set(EXPECTED_UNLOCKS) <= set(definitions))
        for focus_id, decision_names in EXPECTED_UNLOCKS.items():
            suffix = focus_id.removeprefix("ROC_ma_")
            tooltip_key = f"ROC_ma_{suffix}_unlocks_tt"
            focus = definitions[focus_id]
            reward = re.search(
                r"\bcompletion_reward\s*=\s*\{", focus
            )
            self.assertIsNotNone(reward, focus_id)
            reward_block = balanced_block(focus, reward.end() - 1)
            with self.subTest(focus=focus_id):
                self.assertIn(
                    f"custom_effect_tooltip = {tooltip_key}", reward_block
                )
                self.assertTrue(
                    tooltip_key in loc, f"missing unlock tooltip {tooltip_key}"
                )
                if tooltip_key not in loc:
                    continue
                self.assertEqual(occurrences[tooltip_key], 1)
                self.assertIn("在任期间", loc[tooltip_key])
                quoted_names = tuple(re.findall(r"“([^”]+)”", loc[tooltip_key]))
                self.assertEqual(quoted_names, decision_names)
                self.assertNotRegex(loc[tooltip_key], r"\bROC_[A-Za-z0-9_]+\b")

    def test_decision_and_agriculture_gates_describe_the_focus_unlock(self):
        loc, _ = read_localizations()
        for key in (
            "ROC_ma_decision_available_tt",
            "ROC_ma_focus_unlocked_tt",
            "ROC_ma_adopt_agriculture_available_tt",
        ):
            with self.subTest(key=key):
                self.assertTrue(key in loc, f"missing localization key {key}")
                if key not in loc:
                    continue
                self.assertNotIn("阶段", loc[key])
                self.assertTrue("对应部长" in loc[key] or "部长" in loc[key])
                self.assertIn("国策", loc[key])
        self.assertIn("现任部长", loc["ROC_ma_decision_available_tt"])
        self.assertIn("在任", loc["ROC_ma_focus_unlocked_tt"])
        self.assertIn("在任", loc["ROC_ma_adopt_agriculture_available_tt"])


if __name__ == "__main__":
    unittest.main()
