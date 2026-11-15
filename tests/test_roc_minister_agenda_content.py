"""Content contracts for ROC minister routes, events, and shared-focus registration."""

from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_roc_great_practice import focus_map, one, scalar
from test_sichuan_red_opportunity import parse_clausewitz


MAIN_FOCUS = ROOT / "common/national_focus/ROC.txt"
POSTWAR_FOCUS = ROOT / "common/national_focus/ROC_postwar.txt"
SHARED_FOCUS = ROOT / "common/national_focus/ROC_minister_agenda.txt"
LOCALIZATION = ROOT / "localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml"
SLUGS = ("yu", "yan", "ruan", "chen", "xiao")
STAGE_SUFFIXES = ((1, "1"), (2, "step2"), (3, "2"), (4, "step4"), (5, "3"), (6, "step6"))
FOCUS_IDS = tuple(f"ROC_ma_{slug}_{suffix}" for slug in SLUGS for _, suffix in STAGE_SUFFIXES)
ENTRY_IDS = ("ROC_ma_minister_selection",) + tuple(f"ROC_ma_{slug}_appointed" for slug in SLUGS)
ALL_FOCUS_IDS = ENTRY_IDS + FOCUS_IDS
UNIFICATION_BRANCH_IDS = {
    "tongyizhonghua", "bashuzhiguo", "dongbeiwenti", "jisuiyuxi",
    "gemingdetongzhi", "yueguoshanhaiguan", "hengsaoxinan", "jiefangmobei",
    "xibeigongfa", "zhonghuayongyuangonghe",
}
EVENT_IDS = tuple(event for base in (10, 20, 30, 40, 50) for event in (base + 1, base + 2))
THEMES = {
    "yu": ("合作社信用", "城乡采购", "供销账簿"),
    "yan": ("田野调查", "县级调查", "农事示范"),
    "ruan": ("预算审计", "决算", "公共预算"),
    "chen": ("工会", "工资册", "生产协定"),
    "xiao": ("地籍", "自耕农", "土地契约"),
}
LOC_LINE = re.compile(r'^\s*([\w.\-]+):0\s+"(.*)"\s*$')


def read_localization():
    values = {}
    duplicates = []
    if not LOCALIZATION.exists():
        return values, duplicates
    for line in LOCALIZATION.read_text(encoding="utf-8-sig").splitlines():
        match = LOC_LINE.match(line)
        if not match:
            continue
        key, value = match.groups()
        if key in values:
            duplicates.append(key)
        values[key] = value
    return values, duplicates


def focus_definitions():
    source = SHARED_FOCUS.read_text(encoding="utf-8-sig") if SHARED_FOCUS.exists() else ""
    return [value for key, value in parse_clausewitz(source, SHARED_FOCUS.as_posix()) if key == "shared_focus"]


def descendants(entries):
    for key, value in entries:
        yield key, value
        if isinstance(value, list):
            yield from descendants(value)


class RocMinisterAgendaContentTests(unittest.TestCase):
    def test_entry_and_thirty_agenda_focuses_have_expected_dependencies(self):
        definitions = focus_definitions()
        by_id = {scalar(block, "id"): block for block in definitions}
        self.assertEqual(set(ALL_FOCUS_IDS), set(by_id))
        if set(by_id) != set(ALL_FOCUS_IDS):
            return

        root = by_id["ROC_ma_minister_selection"]
        self.assertEqual(scalar(root, "cost"), "1")
        self.assertEqual((scalar(root, "x"), scalar(root, "y")), ("6", "13"))
        self.assertFalse(any(key == "prerequisite" for key, _ in root))
        self.assertEqual(scalar(one(root, "ai_will_do"), "factor"), "0")
        self.assertEqual(one(root, "completion_reward"), [])
        self.assertIn(("custom_trigger_tooltip", [
            ("tooltip", "ROC_ma_appointment_completion_tt"),
            ("hidden_trigger", [("always", "no")]),
        ]), one(root, "available"))
        for slug, x in zip(SLUGS, (2, 4, 6, 8, 10)):
            focus_id = f"ROC_ma_{slug}_appointed"
            block = by_id[focus_id]
            with self.subTest(focus=focus_id):
                self.assertEqual(scalar(block, "cost"), "1")
                self.assertEqual((scalar(block, "x"), scalar(block, "y")), (str(x), "15"))
                self.assertEqual(scalar(one(block, "ai_will_do"), "factor"), "0")
                self.assertEqual(one(block, "completion_reward"), [])
                prerequisites = [
                    ref for key, value in block if key == "prerequisite"
                    for ref_key, ref in descendants(value) if ref_key == "focus"
                ]
                self.assertEqual(prerequisites, ["ROC_ma_minister_selection"])
                available = one(block, "available")
                self.assertIn(("custom_trigger_tooltip", [
                    ("tooltip", "ROC_ma_appointment_completion_tt"),
                    ("hidden_trigger", [("always", "no")]),
                ]), available)

        for slug in SLUGS:
            previous = f"ROC_ma_{slug}_appointed"
            for stage, suffix in STAGE_SUFFIXES:
                focus_id = f"ROC_ma_{slug}_{suffix}"
                block = by_id[focus_id]
                with self.subTest(focus=focus_id):
                    self.assertEqual(scalar(block, "cost"), "25.715")
                    self.assertEqual(
                        (scalar(block, "x"), scalar(block, "y")),
                        (str(2 + SLUGS.index(slug) * 2), str(15 + stage * 2)),
                    )
                    self.assertEqual(scalar(one(block, "ai_will_do"), "factor"), "0")
                    prerequisites = [
                        ref for key, value in block if key == "prerequisite"
                        for ref_key, ref in descendants(value) if ref_key == "focus"
                    ]
                    self.assertEqual(prerequisites, [previous])
                    reward = one(block, "completion_reward")
                    reward_effects = list(descendants(reward))
                    self.assertIn((f"ROC_ma_reward_{slug}_{suffix}", "yes"), reward_effects)
                    available = one(block, "available")
                    self.assertIn(("custom_trigger_tooltip", [
                        ("tooltip", "ROC_ma_automatic_completion_tt"),
                        ("hidden_trigger", [("always", "no")]),
                    ]), available)
                previous = focus_id

        for path in (MAIN_FOCUS, POSTWAR_FOCUS):
            tree = parse_clausewitz(path.read_text(encoding="utf-8-sig"), path.as_posix())
            target_tree_id = "ROC_gonghe" if path == MAIN_FOCUS else "ROC_datong_postwar"
            trees = [
                value for key, value in tree
                if key == "focus_tree" and scalar(value, "id") == target_tree_id
            ]
            self.assertEqual(1, len(trees), path.name)
            if len(trees) != 1:
                continue
            references = [value for key, value in trees[0] if key == "shared_focus"]
            self.assertEqual(["ROC_ma_minister_selection"], references, path.name)
            connected = set()
            pending = list(references)
            while pending:
                focus_id = pending.pop()
                if focus_id in connected:
                    continue
                connected.add(focus_id)
                focus_block = {scalar(block, "id"): block for block in definitions}[focus_id]
                pending.extend(
                    ref for key, value in focus_block if key == "prerequisite"
                    for ref_key, ref in descendants(value) if ref_key == "focus"
                )
                pending.extend(
                    child_id for child_id, child in by_id.items()
                    if any(key == "prerequisite" and any(ref_key == "focus" and ref == focus_id for ref_key, ref in descendants(value)) for key, value in child)
                )
            self.assertEqual(set(ALL_FOCUS_IDS), connected, path.name)

    def test_automatic_focus_columns_are_clear_of_existing_nodes(self):
        x_by_slug = dict(zip(SLUGS, (2, 4, 6, 8, 10)))
        y_by_stage = {stage: 15 + stage * 2 for stage, _ in STAGE_SUFFIXES}
        shared_positions = {
            focus_id: (x_by_slug[slug], y_by_stage[stage])
            for slug in SLUGS for stage, suffix in STAGE_SUFFIXES
            for focus_id in (f"ROC_ma_{slug}_{suffix}",)
        }
        shared_positions["ROC_ma_minister_selection"] = (6, 13)
        shared_positions.update({
            f"ROC_ma_{slug}_appointed": (x, 15)
            for slug, x in zip(SLUGS, (2, 4, 6, 8, 10))
        })
        definitions = {scalar(block, "id"): block for block in focus_definitions()}
        self.assertTrue(set(ALL_FOCUS_IDS) <= set(definitions))
        if not set(ALL_FOCUS_IDS) <= set(definitions):
            return
        layout_changed = (
            set(shared_positions)
            | {"banbugonghelinshixianfa", "hengsaoxinan"}
            | UNIFICATION_BRANCH_IDS
        )
        for focus_id, expected in shared_positions.items():
            block = definitions[focus_id]
            self.assertEqual((int(scalar(block, "x")), int(scalar(block, "y"))), expected)

        for path in (MAIN_FOCUS, POSTWAR_FOCUS):
            source = path.read_text(encoding="utf-8-sig")
            target_tree_id = "ROC_gonghe" if path == MAIN_FOCUS else "ROC_datong_postwar"
            parsed = parse_clausewitz(source, path.as_posix())
            matching_trees = [
                value for key, value in parsed
                if key == "focus_tree" and scalar(value, "id") == target_tree_id
            ]
            self.assertEqual(1, len(matching_trees), path.name)
            if len(matching_trees) != 1:
                continue
            positions = {
                focus_id: (int(scalar(block, "x")), int(scalar(block, "y")))
                for key, block in matching_trees[0] if key == "focus"
                for focus_id in (scalar(block, "id"),)
            }
            positions.update(shared_positions)
            focus_blocks = {
                scalar(block, "id"): block
                for key, block in matching_trees[0] if key == "focus"
            }
            focus_blocks.update(definitions)
            for focus_id, (x, y) in positions.items():
                for other_id, (other_x, other_y) in positions.items():
                    if focus_id >= other_id:
                        continue
                    if focus_id not in layout_changed and other_id not in layout_changed:
                        continue
                    with self.subTest(tree=path.name, left=focus_id, right=other_id):
                        self.assertFalse(
                            abs(x - other_x) * 220 < 184 and abs(y - other_y) * 120 < 90,
                            "focus cards overlap",
                        )

            half_width = 184 / (2 * 220)
            half_height = 90 / (2 * 120)

            def horizontal_intersects(y, x1, x2, ox, oy):
                low_x, high_x = sorted((x1, x2))
                return (
                    oy - half_height <= y <= oy + half_height
                    and ox - half_width <= high_x
                    and low_x <= ox + half_width
                )

            def vertical_intersects(x, y1, y2, ox, oy):
                low_y, high_y = sorted((y1, y2))
                return (
                    ox - half_width <= x <= ox + half_width
                    and oy - half_height <= high_y
                    and low_y <= oy + half_height
                )

            for focus_id, block in focus_blocks.items():
                parent_groups = [
                    [ref for ref_key, ref in descendants(value) if ref_key == "focus"]
                    for key, value in block if key == "prerequisite"
                ]
                if not (
                    focus_id.startswith("ROC_ma_")
                    or focus_id in layout_changed
                    or any(parent in layout_changed for group in parent_groups for parent in group)
                ):
                    continue
                child_x, child_y = positions[focus_id]
                for group in parent_groups:
                    for parent_id in group:
                        if parent_id not in positions:
                            continue
                        parent_x, parent_y = positions[parent_id]
                        if parent_y >= child_y:
                            continue
                        start_y = parent_y + half_height
                        end_y = child_y - half_height
                        middle_y = (start_y + end_y) / 2
                        for other_id, (other_x, other_y) in positions.items():
                            if other_id in {parent_id, focus_id}:
                                continue
                            intersects = (
                                vertical_intersects(parent_x, start_y, middle_y, other_x, other_y)
                                or horizontal_intersects(middle_y, parent_x, child_x, other_x, other_y)
                                or vertical_intersects(child_x, middle_y, end_y, other_x, other_y)
                            )
                            with self.subTest(tree=path.name, parent=parent_id, child=focus_id, obstacle=other_id):
                                self.assertFalse(intersects, "focus connector crosses another focus card")

    def test_focus_names_descriptions_and_reward_tooltips_are_complete(self):
        self.assertTrue(LOCALIZATION.exists(), "minister agenda localization should exist")
        if not LOCALIZATION.exists():
            return
        self.assertTrue(LOCALIZATION.read_bytes().startswith(b"\xef\xbb\xbf"), "localization needs UTF-8 BOM")
        loc, duplicates = read_localization()
        self.assertEqual([], [key for key in duplicates if key.startswith("ROC_ma_")])
        for focus_id in FOCUS_IDS:
            with self.subTest(focus=focus_id):
                self.assertTrue(focus_id in loc, focus_id)
                desc = loc[f"{focus_id}_desc"]
                self.assertTrue(desc.strip())
                self.assertGreaterEqual(len(desc), 80)
                self.assertLessEqual(len(desc), 203)
                slug, suffix = focus_id.removeprefix("ROC_ma_").rsplit("_", 1)
                if suffix in {"step2", "step4"}:
                    self.assertLessEqual(len(desc), 160)
                tooltip = loc[f"ROC_ma_reward_{slug}_{suffix}_tt"]
                self.assertTrue(tooltip.strip())
                self.assertIn("履职", tooltip)
                self.assertNotRegex(tooltip, r"(?:公有|市场)方向待落实[+−-]\d+")
        for focus_id in ENTRY_IDS:
            with self.subTest(focus=focus_id):
                self.assertIn(focus_id, loc)
                desc = loc[f"{focus_id}_desc"]
                self.assertTrue(desc.strip())
                self.assertLessEqual(len(desc), 203)
                self.assertNotIn("自动完成", desc)
        for key in (
            "ROC_ma_automatic_completion_tt", "ROC_ma_appointment_completion_tt",
            "ROC_ma_decision_available_tt", "ROC_ma_advance_14_tt",
            "ROC_ma_advance_21_tt", "ROC_ma_event_available_tt", "ROC_ma_event_pay_tt",
            "ROC_ma_event_compromise_tt", "ROC_ma_event_delay_tt", "ROC_ma_project_credit_tt",
            "ROC_ma_committee_link_tt", "ROC_ma_focus_unlocked_tt",
            "ROC_ma_current_action", "ROC_ma_current_action_desc",
        ):
            self.assertIn(key, loc)

    def test_each_minister_has_two_distinct_dramatic_events_with_three_options(self):
        self.assertTrue(LOCALIZATION.exists(), "minister agenda localization should exist")
        loc, duplicates = read_localization()
        self.assertEqual([], [key for key in duplicates if key.startswith("ROC_ma_")])
        stories = []
        event_path = ROOT / "events/ROC_minister_agenda.txt"
        events = {
            one(block, "id"): block
            for kind, block in parse_clausewitz(event_path.read_text(encoding="utf-8-sig"), event_path.as_posix())
            if kind == "country_event"
        }
        minister_faction = {"yu": "中", "yan": "中", "ruan": "左", "chen": "左", "xiao": "右"}
        for slug, first_event, second_event in zip(SLUGS, EVENT_IDS[::2], EVENT_IDS[1::2]):
            for decision_number, event_id in ((1, first_event), (2, second_event)):
                prefix = f"ROC_minister_agenda.{event_id}"
                with self.subTest(event=event_id):
                    for suffix in ("t", "d", "a", "b", "c"):
                        self.assertIn(f"{prefix}.{suffix}", loc)
                        if suffix != "d":
                            self.assertLessEqual(len(loc[f"{prefix}.{suffix}"]), 24)
                    story = loc[f"{prefix}.d"].replace(r"\n", "")
                    self.assertGreaterEqual(len(story), 500)
                    self.assertLessEqual(len(story), 800)
                    self.assertGreaterEqual(loc[f"{prefix}.d"].count(r"\n\n"), 2)
                    self.assertTrue(any(theme in story for theme in THEMES[slug]))
                    self.assertRegex(
                        story,
                        r"中央|部长办公室",
                        "minister disputes should be decided at the central level",
                    )
                    self.assertIn(f"大同党{minister_faction[slug]}派", story)
                    stories.append(story)

                    decision_key = f"ROC_ma_{slug}_{decision_number}_decision"
                    self.assertIn(decision_key, loc)
                    self.assertIn(f"{decision_key}_desc", loc)
                    decision_tooltip = loc[f"{decision_key}_tt"]
                    if decision_number == 1:
                        self.assertIn("撤下前任未落实安排", decision_tooltip)
                        self.assertIn("施政提前14日", decision_tooltip)
                    else:
                        self.assertIn("替换旧部长安排", decision_tooltip)
                        self.assertIn("施政提前21日", decision_tooltip)
                    options = [value for key, value in events[prefix] if key == "option"]
                    self.assertEqual(len(options), 3)
                    options_by_name = {one(option, "name"): option for option in options}
                    self.assertEqual(set(options_by_name), {f"{prefix}.{choice}" for choice in "abc"})
                    for choice in "abc":
                        effect_key = f"ROC_ma_{slug}_{decision_number}_{choice}_tt"
                        self.assertEqual(one(options_by_name[f"{prefix}.{choice}"], "custom_effect_tooltip"), effect_key)
                        self.assertIn(effect_key, loc)
                        self.assertTrue(loc[effect_key].strip())
                        self.assertNotRegex(loc[effect_key], r"(?:公有|市场)方向待落实[+−-]\d+")
                    self.assertEqual(
                        len({loc[f"ROC_ma_{slug}_{decision_number}_{choice}_tt"] for choice in "abc"}),
                        3,
                    )

        self.assertEqual(len(stories), len(set(stories)), "each minister event needs its own story")
        all_stories = "".join(stories)
        for slug, themes in THEMES.items():
            self.assertTrue(any(theme in all_stories for theme in themes), slug)

    def test_faction_favor_and_delay_explanations_use_the_three_datong_factions(self):
        self.assertTrue(LOCALIZATION.exists(), "minister agenda localization should exist")
        if not LOCALIZATION.exists():
            return
        loc, _ = read_localization()
        availability = loc["ROC_ma_decision_available_tt"]
        self.assertIn("\u73b0\u4efb\u90e8\u957f", availability)
        self.assertIn("\u8def\u7ebf\u76f8\u7b26", availability)
        self.assertIn("\u5bf9\u5e94\u89e3\u9501\u56fd\u7b56", availability)
        compromise = loc["ROC_ma_event_compromise_tt"]
        for faction in ("\u5927\u540c\u515a\u5de6\u6d3e\u4e0e\u53f3\u6d3e", "\u5927\u540c\u515a\u4e2d\u6d3e", "\u672c\u4eba\u6240\u5c5e\u6d3e\u522b"):
            self.assertIn(faction, compromise)
        committee_link = loc["ROC_ma_committee_link_tt"]
        for faction in ("\u5927\u540c\u515a\u5de6\u6d3e", "\u5927\u540c\u515a\u4e2d\u6d3e", "\u5927\u540c\u515a\u53f3\u6d3e"):
            self.assertIn(faction, committee_link)
        for key in (
            "ROC_ma_advance_14_tt", "ROC_ma_advance_21_tt", "ROC_ma_event_available_tt",
            "ROC_ma_event_pay_tt", "ROC_ma_event_delay_tt", "ROC_ma_project_credit_tt",
        ):
            self.assertTrue(loc[key].strip())
            self.assertNotIn("独立委员会", loc[key])
        for key, faction in (
            ("ROC_ma_committee_delay_left_tt", "大同党左派"),
            ("ROC_ma_committee_delay_right_tt", "大同党右派"),
        ):
            with self.subTest(key=key):
                self.assertIn(faction, loc[key])
                self.assertIn("15好感", loc[key])
                self.assertIn("延长21日", loc[key])
        for key, forbidden in {
            "ROC_ma_decision_available_tt": ("劳动党", "社会党", "中华民主同盟", "政治点数"),
            "ROC_ma_advance_14_tt": ("劳动党", "社会党", "中华民主同盟"),
            "ROC_ma_advance_21_tt": ("劳动党", "社会党", "中华民主同盟"),
            "ROC_ma_event_available_tt": ("劳动党", "社会党", "中华民主同盟"),
            "ROC_ma_event_pay_tt": ("劳动党", "社会党", "中华民主同盟"),
            "ROC_ma_event_compromise_tt": ("劳动党", "社会党", "中华民主同盟"),
            "ROC_ma_event_delay_tt": ("劳动党", "社会党", "中华民主同盟"),
            "ROC_ma_project_credit_tt": ("劳动党", "社会党", "中华民主同盟"),
            "ROC_ma_committee_link_tt": ("劳动党", "社会党", "中华民主同盟"),
        }.items():
            for phrase in forbidden:
                self.assertNotIn(phrase, loc[key])


if __name__ == "__main__":
    unittest.main()
