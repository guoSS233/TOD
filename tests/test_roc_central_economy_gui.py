"""Contracts for the unified ROC economy and committee overview."""

from pathlib import Path
import re
import sys
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_sichuan_red_opportunity import parse_clausewitz


CATEGORY = ROOT / "common/decisions/categories/ROC.txt"
SCRIPTED_GUI = ROOT / "common/scripted_guis/ROC_central_economy.txt"
SCRIPTED_LOC = ROOT / "common/scripted_localisation/ROC_scripted_localisation.txt"
GUI = ROOT / "interface/ROC_central_economy.gui"
GUI_GFX = ROOT / "interface/ROC_economic_council.gfx"
LOCALISATION = ROOT / "localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml"
AGENDA_LOC = ROOT / "localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml"
COMMITTEE_SCRIPTED_LOC = ROOT / "common/scripted_localisation/ROC_scripted_localisation.txt"
COMMITTEE_LOC = ROOT / "localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml"
LEGACY_LOC = ROOT / "localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml"
POSTWAR_LOC = ROOT / "localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml"
SLUGS = ("yu", "yan", "ruan", "chen", "xiao")
FOCUS_IDS = tuple(
    f"ROC_ma_{slug}_{stage}"
    for slug in SLUGS for stage in ("1", "step2", "2", "step4", "3", "step6")
)
OLD_FOCI = (
    "national_accounts", "joint_program", "industrial_delivery", "agricultural_delivery",
    "transport_delivery", "acceptance_rules", "mining_development", "commercial_circulation",
)
FORBIDDEN_FACTIONS = ("劳动党", "社会党", "中华民主同盟", "大同会中央", "四党", "四方", "独立委员会")


def descendants(entries):
    for key, value in entries:
        yield key, value
        if isinstance(value, list):
            yield from descendants(value)


def one(entries, key):
    matches = [value for name, value in entries if name == key]
    if len(matches) != 1:
        raise AssertionError(f"expected one {key}, found {len(matches)}")
    return matches[0]


def scalar(entries, key):
    value = one(entries, key)
    if isinstance(value, list):
        raise AssertionError(f"expected scalar {key}")
    return value


def parse_script(path):
    return parse_clausewitz(path.read_text(encoding="utf-8-sig"), path.as_posix())


def read_localization(path):
    values = {}
    duplicates = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        match = re.fullmatch(r'\s*([\w.\-]+):?0?\s*"(.*)"\s*', line)
        if not match:
            if line.strip() and line.strip() != "l_simp_chinese:" and not line.strip().startswith("#"):
                raise AssertionError(f"invalid localization line {line_number} in {path.name}")
            continue
        key, value = match.groups()
        if key in values:
            duplicates.append(key)
        values[key] = value
    return values, duplicates


def get_defined_texts():
    return {
        scalar(block, "name"): block
        for key, block in parse_script(SCRIPTED_LOC)
        if key == "defined_text"
    }


def branches(block):
    return [value for key, value in block if key == "text"]


def branch_for(block, loc_key):
    return next(
        branch for branch in branches(block)
        if scalar(branch, "localization_key") == loc_key
    )


def font_advances(path):
    advances = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = re.search(r"\bchar id=(\d+).*?\bxadvance=(-?\d+)", line)
        if match:
            advances[int(match.group(1))] = int(match.group(2))
    if not advances:
        raise AssertionError(f"no glyph advances found in {path}")
    return advances


class RocCentralEconomyGuiContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loc, cls.duplicates = read_localization(LOCALISATION)
        cls.agenda_loc, cls.agenda_duplicates = read_localization(AGENDA_LOC)
        cls.committee_loc, cls.committee_duplicates = read_localization(COMMITTEE_LOC)
        cls.legacy_loc, _ = read_localization(LEGACY_LOC)
        cls.postwar_loc, _ = read_localization(POSTWAR_LOC)
        cls.scripts = get_defined_texts()

    def test_economic_and_committee_categories_register_separate_overviews(self):
        self.assertEqual([], [key for key in self.duplicates if key.startswith(("ROC_ce_", "ROC_ma_", "ROC_econ_"))])
        categories = parse_script(CATEGORY)
        category = one(categories, "ROC_economic_administration")
        committee = one(categories, "ROC_focus_sanpai")
        self.assertEqual("ROC_central_economy_window", scalar(category, "scripted_gui"))
        self.assertEqual("ROC_economic_council_window", scalar(committee, "scripted_gui"))
        visible_requirements = list(descendants(one(category, "visible")))
        committee_requirements = list(descendants(one(committee, "visible")))
        self.assertIn(("ROC_ce_administration_active", "yes"), visible_requirements)
        self.assertNotIn(("ROC_has_gemingweiyuanhui", "yes"), visible_requirements)
        self.assertIn(("ROC_has_gemingweiyuanhui", "yes"), committee_requirements)
        self.assertNotIn(("ROC_ce_administration_active", "yes"), committee_requirements)

        source = CATEGORY.read_text(encoding="utf-8-sig")
        self.assertIn("scripted_gui = ROC_economic_council_window", source)
        self.assertEqual(self.loc["ROC_economic_administration"], "中央经济施政")
        description = self.loc["ROC_economic_administration_desc"]
        for term in ("预算", "工程", "部长", "大同党左、中、右三派", "拖他后腿", "革命委员会"):
            self.assertIn(term, description)
        for forbidden in FORBIDDEN_FACTIONS:
            self.assertNotIn(forbidden, description)

    def test_overview_has_readable_layout_and_all_active_rows(self):
        gui = parse_script(GUI)
        gui_types = one(gui, "guiTypes")
        window = next(
            block for key, block in gui_types
            if key == "containerWindowType" and scalar(block, "name") == "ROC_central_economy_window"
        )
        size = one(window, "size")
        self.assertEqual("500", scalar(size, "width"))
        height = int(scalar(size, "height"))
        panel = one(window, "containerWindowType")
        panel_top = int(scalar(one(panel, "position"), "y"))
        panel_bottom = panel_top + int(scalar(one(panel, "size"), "height"))
        self.assertLessEqual(panel_bottom, height)
        self.assertFalse(any(key == "alwaystransparent" for key, _ in panel))
        self.assertEqual("yes", scalar(one(panel, "background"), "alwaystransparent"))
        widgets = {
            scalar(block, "name"): block
            for key, block in window
            if key in ("instantTextBoxType", "iconType")
        }
        required_widgets = {
            "ROC_ce_gui_title", "ROC_ce_gui_mandate", "ROC_ce_gui_minister", "ROC_ce_gui_term",
            "ROC_ce_gui_current_action", "ROC_ce_gui_current_action_desc", "ROC_ce_gui_current_action_percent",
            "ROC_ce_gui_performance",
            "ROC_ce_gui_project_name", "ROC_ce_gui_project_status", "ROC_ce_gui_project_progress",
            "ROC_ce_gui_policy_axis", "ROC_ce_gui_policy_route", "ROC_ce_gui_policy_effects",
            "ROC_ce_gui_parties_heading", "ROC_ce_gui_left_favor", "ROC_ce_gui_center_favor",
            "ROC_ce_gui_right_favor", "ROC_ce_gui_committee_heading", "ROC_ce_gui_head",
        }
        expected_icons = {
            "ROC_ce_gui_current_action_bar": "GFX_ROC_econ_action_progress",
            "ROC_ce_gui_policy_axis_track": "GFX_bop_bar_bg",
            "ROC_ce_gui_policy_axis_midpoint": "GFX_bop_splitter",
            "ROC_ce_gui_policy_axis_needle": "GFX_bop_needle",
        }
        self.assertEqual(required_widgets | set(expected_icons), set(widgets))
        for name, sprite in expected_icons.items():
            self.assertEqual(sprite, scalar(widgets[name], "spriteType"))
            self.assertEqual("yes", scalar(widgets[name], "alwaystransparent"))
        self.assertEqual("ROC_econ_head_rules_tt", scalar(widgets["ROC_ce_gui_head"], "pdx_tooltip"))

        for name in required_widgets:
            widget = widgets[name]
            expected_font = "hoi_18mbs" if name == "ROC_ce_gui_title" else "hoi_16mbs"
            self.assertEqual(expected_font, scalar(widget, "font"))
            expected_height = "40" if name in {"ROC_ce_gui_current_action_desc", "ROC_ce_gui_project_status", "ROC_ce_gui_policy_effects", "ROC_ce_gui_head"} else "20"
            self.assertEqual(expected_height, scalar(widget, "maxHeight"))
        self.assertEqual("ROC_ce_performance_tt", scalar(widgets["ROC_ce_gui_performance"], "pdx_tooltip"))
        texts = {name: scalar(widgets[name], "text") for name in required_widgets}
        expected_dynamic = {
            "ROC_ce_gui_mandate": "[ROOT.ROC_ce_mandate_status]",
            "ROC_ce_gui_term": "[ROOT.ROC_ce_term_status]",
            "ROC_ce_gui_current_action": "[ROOT.ROC_ma_current_action]",
            "ROC_ce_gui_current_action_desc": "[ROOT.ROC_ma_current_action_desc]",
            "ROC_ce_gui_performance": "[ROOT.ROC_ce_performance_text]",
            "ROC_ce_gui_project_progress": "[ROOT.ROC_ce_project_progress_text]",
            "ROC_ce_gui_policy_axis": "[ROOT.ROC_ce_policy_status]",
            "ROC_ce_gui_policy_route": "ROC_ce_gui_policy_route",
            "ROC_ce_gui_policy_effects": "[ROOT.ROC_ce_policy_effect_summary]",
            "ROC_ce_gui_left_favor": "[ROOT.ROC_ce_left_favor_text]",
            "ROC_ce_gui_center_favor": "[ROOT.ROC_ce_center_favor_text]",
            "ROC_ce_gui_right_favor": "[ROOT.ROC_ce_right_favor_text]",
        }
        for name, value in expected_dynamic.items():
            self.assertEqual(value, texts[name])
        for name, value in texts.items():
            if name not in expected_dynamic:
                self.assertIn(value, self.loc, name)
        self.assertEqual("ROC_ma_committee_link_tt", scalar(widgets["ROC_ce_gui_committee_heading"], "pdx_tooltip"))
        self.assertEqual("ROC_ce_policy_queues_tt", scalar(widgets["ROC_ce_gui_policy_route"], "pdx_tooltip"))
        self.assertIn("革命委员会", self.loc["ROC_ce_gui_committee_heading"])
        self.assertIn("[ROOT.ROC_committee_opposition_target_text]", self.agenda_loc["ROC_ma_committee_link_tt"])
        root_functions = set(re.findall(r"\[ROOT\.([\w.]+)\]", GUI.read_text(encoding="utf-8-sig")))
        root_functions.update(re.findall(r"\[ROOT\.([\w.]+)\]", self.loc["ROC_ce_gui_policy_route"]))
        self.assertTrue(root_functions)
        self.assertTrue(root_functions <= set(self.scripts), root_functions - set(self.scripts))
        scripted_gui = parse_script(SCRIPTED_GUI)
        registration = one(one(scripted_gui, "scripted_gui"), "ROC_central_economy_window")
        properties = one(registration, "properties")
        self.assertEqual("ROC_ma_gui_progress_frame", scalar(one(properties, "ROC_ce_gui_current_action_bar"), "frame"))
        self.assertEqual("ROC_ce_policy_needle_x", scalar(one(properties, "ROC_ce_gui_policy_axis_needle"), "x"))
        triggers = one(registration, "triggers")
        for name in ("ROC_ce_gui_current_action_bar_visible", "ROC_ce_gui_current_action_percent_visible"):
            self.assertEqual([("ROC_ma_show_stage_progress", "yes")], one(triggers, name))
        self.assertIn("[?ROC_ma_gui_progress_percent|0]%", self.loc[texts["ROC_ce_gui_current_action_percent"]])

        self.assertEqual("248", scalar(one(widgets["ROC_ce_gui_policy_axis_midpoint"], "position"), "x"))
        self.assertEqual("0", scalar(one(widgets["ROC_ce_gui_policy_axis_needle"], "position"), "x"))
        rectangles = []
        bar_scale = int(scalar(widgets["ROC_ce_gui_current_action_bar"], "scale"))
        row_icons = {"ROC_ce_gui_policy_axis_track": (360, 16), "ROC_ce_gui_current_action_bar": (80 * bar_scale, 3 * bar_scale)}
        for name in required_widgets | set(row_icons):
            widget = widgets[name]
            pos = one(widget, "position")
            x, y = int(scalar(pos, "x")), int(scalar(pos, "y"))
            if name in row_icons:
                width, widget_height = row_icons[name]
            else:
                width, widget_height = int(scalar(widget, "maxWidth")), int(scalar(widget, "maxHeight"))
            self.assertGreaterEqual(x, 50, name)
            self.assertLessEqual(x + width, 450, name)
            self.assertGreaterEqual(y, panel_top, name)
            self.assertLessEqual(y + widget_height, panel_bottom - 12, name)
            rectangles.append((name, x, y, x + width, y + widget_height))
        for index, earlier in enumerate(rectangles):
            for later in rectangles[index + 1:]:
                intersects = earlier[1] < later[3] and later[1] < earlier[3] and earlier[2] < later[4] and later[2] < earlier[4]
                self.assertFalse(intersects, f"overlap: {earlier[0]} and {later[0]}")

    def test_agenda_progress_sprite_frames_fill_in_elapsed_order(self):
        sprite = one(one(parse_script(GUI_GFX), "spriteTypes"), "spriteType")
        self.assertEqual("GFX_ROC_econ_action_progress", scalar(sprite, "name"))
        self.assertEqual("101", scalar(sprite, "noOfFrames"))
        with Image.open(ROOT / scalar(sprite, "texturefile")) as atlas:
            self.assertEqual((101 * 80, 3), atlas.size)
            fills = [
                sum(atlas.getpixel((frame * 80 + x, 1)) == (206, 164, 83) for x in range(80))
                for frame in range(101)
            ]
        self.assertEqual((0, 42, 78), (fills[0], fills[54], fills[100]))
        self.assertEqual(sorted(fills), fills)

    def test_current_action_distinguishes_pause_vacancy_active_stages_and_execution(self):
        action = self.scripts["ROC_ma_current_action"]
        desc = self.scripts["ROC_ma_current_action_desc"]
        expected_titles = {
            "ROC_ma_gui_action_waiting_conference", "ROC_ma_gui_action_waiting_successor",
            "ROC_ma_gui_action_no_minister", "ROC_ma_gui_action_execution", "ROC_ma_gui_action_rearming",
            "ROC_ma_gui_action_initializing",
            *FOCUS_IDS,
        }
        self.assertEqual(expected_titles, {scalar(branch, "localization_key") for branch in branches(action)})
        expected_desc = {
            "ROC_ma_gui_action_waiting_conference_desc", "ROC_ma_gui_action_waiting_successor_desc",
            "ROC_ma_gui_action_no_minister_desc", "ROC_ma_gui_action_active_desc",
            "ROC_ma_gui_action_execution_desc", "ROC_ma_gui_action_rearming_desc",
            "ROC_ma_gui_action_initializing_desc",
        }
        self.assertEqual(expected_desc, {scalar(branch, "localization_key") for branch in branches(desc)})
        for key in expected_titles | expected_desc:
            self.assertIn(key, self.agenda_loc)

        conference = branch_for(action, "ROC_ma_gui_action_waiting_conference")
        successor = branch_for(action, "ROC_ma_gui_action_waiting_successor")
        vacant = branch_for(action, "ROC_ma_gui_action_no_minister")
        execution = branch_for(action, "ROC_ma_gui_action_execution")
        self.assertIn(("has_country_flag", "ROC_econ_conference_pending"), set(descendants(one(conference, "trigger"))))
        self.assertIn(("has_country_flag", "ROC_econ_resignation_pending"), set(descendants(one(successor, "trigger"))))
        vacant_requirements = list(descendants(one(vacant, "trigger")))
        execution_requirements = list(descendants(one(execution, "trigger")))
        self.assertIn(("var", "ROC_ce_minister_profile_id"), vacant_requirements)
        self.assertIn(("var", "ROC_ma_stage"), execution_requirements)
        self.assertIn(("check_variable", [
            ("var", "ROC_ma_stage"), ("value", "7"), ("compare", "equals"),
        ]), one(execution, "trigger"))

        suffixes = ("1", "step2", "2", "step4", "3", "step6")
        for owner, slug in enumerate(SLUGS, 1):
            for stage, suffix in enumerate(suffixes, 1):
                requirements = one(branch_for(action, f"ROC_ma_{slug}_{suffix}"), "trigger")
                with self.subTest(minister=slug, stage=stage):
                    for variable, expected in (
                        ("ROC_ce_minister_profile_id", owner),
                        ("ROC_ma_clock_owner", owner),
                        ("ROC_ma_stage", stage),
                    ):
                        self.assertIn(("check_variable", [
                            ("var", variable), ("value", str(expected)), ("compare", "equals"),
                        ]), requirements)

        for key in (
            "ROC_ma_gui_action_waiting_conference_desc", "ROC_ma_gui_action_waiting_successor_desc",
            "ROC_ma_gui_action_no_minister_desc", "ROC_ma_gui_action_rearming_desc",
        ):
            text = self.agenda_loc[key]
            self.assertNotIn("ROC_ma_days_remaining", text)
            self.assertNotIn("余 [?", text)
        self.assertIn("ROC_ma_days_remaining", self.agenda_loc["ROC_ma_gui_action_active_desc"])
        self.assertIn("ROC_ma_days_remaining", self.agenda_loc["ROC_ma_gui_action_execution_desc"])
        self.assertIn("六阶段", self.agenda_loc["ROC_ma_gui_action_execution"])
        self.assertIn("六阶段", self.agenda_loc["ROC_ma_gui_action_execution_desc"])
        self.assertIn("已保存", self.agenda_loc["ROC_ma_gui_action_waiting_successor_desc"])
        self.assertIn("不计入继任者", self.agenda_loc["ROC_ma_gui_action_waiting_successor_desc"])

    def test_performance_waits_for_an_active_term(self):
        performance = self.scripts["ROC_ce_performance_text"]
        branches_by_key = {scalar(branch, "localization_key"): branch for branch in branches(performance)}
        self.assertEqual(
            {
                "ROC_ce_gui_performance",
                "ROC_ce_gui_performance_waiting_term",
                "ROC_ce_gui_performance_initializing",
            },
            set(branches_by_key),
        )
        active_requirements = list(descendants(one(branches_by_key["ROC_ce_gui_performance"], "trigger")))
        waiting_requirements = list(descendants(one(branches_by_key["ROC_ce_gui_performance_waiting_term"], "trigger")))
        self.assertIn(("has_country_flag", "ROC_econ_term_active"), active_requirements)
        self.assertIn(("has_country_flag", "ROC_ce_initialized"), waiting_requirements)
        self.assertNotIn(("has_country_flag", "ROC_econ_term_active"), waiting_requirements)
        self.assertIn("任期尚未确立", self.loc["ROC_ce_gui_performance_waiting_term"])

    def test_idle_project_row_explains_the_next_step_without_claiming_progress(self):
        project_progress = self.scripts["ROC_ce_project_progress_text"]
        branch_keys = {scalar(branch, "localization_key") for branch in branches(project_progress)}
        self.assertEqual({
            "ROC_ce_gui_project_progress_initializing",
            "ROC_ce_gui_project_progress_active",
            "ROC_ce_gui_project_progress_no_delivery_target",
            "ROC_ce_gui_project_progress_waiting_conference",
            "ROC_ce_gui_project_progress_waiting_successor",
            "ROC_ce_gui_project_progress_idle",
        }, branch_keys)
        self.assertIn("推进部长施政30日", self.loc["ROC_ce_gui_project_progress_idle"])
        self.assertIn("会议结束后", self.loc["ROC_ce_gui_project_progress_waiting_conference"])
        self.assertIn("部长继任后", self.loc["ROC_ce_gui_project_progress_waiting_successor"])

    def test_seven_legacy_central_economy_events_are_three_faction_localized(self):
        for key in (
            "ROC_ce_datong_status", "ROC_ce_labor_status", "ROC_ce_socialist_status", "ROC_ce_democratic_status",
        ):
            self.assertNotIn(key, self.scripts)
        for focus in OLD_FOCI:
            self.assertNotIn(f"ROC_ce_{focus}", self.loc)
            self.assertNotIn(f"ROC_ce_{focus}_desc", self.loc)
            self.assertNotIn(f"ROC_ce_{focus}_effect_tt", self.loc)
            self.assertNotIn(f"ROC_pw_ce_{focus}", self.loc)

        for event in range(1, 7):
            for suffix in ("t", "d", "a", "b", "c", "a_tt", "b_tt", "c_tt"):
                key = f"ROC_central_economy.{event}.{suffix}"
                self.assertIn(key, self.loc)
                for forbidden in FORBIDDEN_FACTIONS:
                    self.assertNotIn(forbidden, self.loc[key], key)
            body = self.loc[f"ROC_central_economy.{event}.d"]
            for faction in ("大同党左派", "大同党中派", "大同党右派"):
                self.assertIn(faction, body, f"event {event} needs all three factions")
        for suffix in ("desc", "a", "b", "c", "d", "e", "a_tt", "b_tt", "c_tt", "d_tt", "e_tt"):
            key = f"ROC_central_economy.7.{suffix}"
            self.assertIn(key, self.loc)
            for forbidden in FORBIDDEN_FACTIONS:
                self.assertNotIn(forbidden, self.loc[key], key)

        public = self.loc["ROC_ce_policy_public_tt"]
        market = self.loc["ROC_ce_policy_market_tt"]
        for text in (public, market, self.loc["ROC_ce_focus_contribution_tt"]):
            for forbidden in FORBIDDEN_FACTIONS:
                self.assertNotIn(forbidden, text)
        self.assertIn("左派好感+12", public)
        self.assertIn("右派好感−4", public)
        self.assertIn("右派好感+8", market)
        self.assertIn("左派好感−8", market)
        self.assertNotIn("待落实", public)
        self.assertNotIn("待落实", market)
        public_shift = self.loc["ROC_ce_policy_public_020_tt"]
        market_shift = self.loc["ROC_ce_policy_market_020_tt"]
        self.assertIn("公有方向待落实+2", public_shift)
        self.assertIn("左派好感+12", public_shift)
        self.assertIn("市场方向待落实−2", market_shift)
        self.assertIn("右派好感+8", market_shift)
        self.assertIn("问责压力−3", self.loc["ROC_ce_focus_contribution_tt"])

    def test_seven_structure_tiers_and_gui_text_fit_measured_fonts(self):
        tiers = ("mixed", "market_1", "market_2", "market_3", "public_1", "public_2", "public_3")
        for suffix in ("name", "current"):
            for tier in tiers:
                self.assertIn(f"ROC_ce_gui_structure_{tier}_{suffix}", self.loc)
        self.assertIn("ROC_ce_structure_tiers_tt", self.loc)
        for label in ("经济结构", "待落实", "[?ROC_ce_policy_axis|+0]", "通用[?ROC_ce_policy_pending|+0]", "部长[?ROC_ma_policy_pending|+0]"):
            self.assertIn(label, self.loc["ROC_ce_gui_policy_axis"])
        queues = self.loc["ROC_ce_policy_queues_tt"]
        for phrase in ("通用政策", "部长办法", "撤下", "优先", "保留", "每月最多落实一点"):
            self.assertIn(phrase, queues)
        self.assertIn("[?ROC_ma_policy_pending|+0]", queues)
        self.assertIn("[?ROC_ce_policy_pending|+0]", queues)

        gui = parse_script(GUI)
        window = next(
            block for key, block in one(gui, "guiTypes")
            if key == "containerWindowType" and scalar(block, "name") == "ROC_central_economy_window"
        )
        widgets = {scalar(w, "name"): w for key, w in window if key == "instantTextBoxType"}
        game_font = font_advances(ROOT.parents[1] / "gfx/fonts/hoi_16mbs.fnt")
        title_font = font_advances(ROOT.parents[1] / "gfx/fonts/hoi_18mbs.fnt")
        small_font = font_advances(ROOT / "gfx/fonts/Arial_14s.fnt")
        self.assertTrue(set(FOCUS_IDS) <= set(self.agenda_loc), "all route names must be localized")
        longest_focus_name = max(
            (self.agenda_loc[key] for key in FOCUS_IDS),
            key=len,
        )
        committee_focus_keys = {
            value for key, value in descendants(parse_script(COMMITTEE_SCRIPTED_LOC))
            if key == "localization_key" and isinstance(value, str) and not value.startswith("ROC_committee_gui_")
        }
        longest_committee_name = max((self.legacy_loc[key] for key in committee_focus_keys), key=len)
        longest_structure_effect = max(
            (self.loc[f"ROC_ce_gui_structure_{tier}_current"] for tier in tiers),
            key=len,
        )
        lines = {
            "ROC_ce_gui_title": [self.loc["ROC_ce_gui_title"]],
            "ROC_ce_gui_mandate": [self.loc["ROC_ce_gui_mandate"]],
            "ROC_ce_gui_minister": ["经济部长：萧铮（小生产者）", "经济部长：未任命（路线未定）"],
            "ROC_ce_gui_term": [self.loc["ROC_ce_gui_term_active"], self.loc["ROC_ce_gui_term_waiting_successor"]],
            "ROC_ce_gui_current_action": [longest_focus_name, self.agenda_loc["ROC_ma_gui_action_execution"]],
            "ROC_ce_gui_current_action_percent": [re.sub(r"§[Y!]", "", self.loc["ROC_ce_gui_current_action_percent"])],
            "ROC_ce_gui_current_action_desc": [
                self.agenda_loc["ROC_ma_gui_action_active_desc"].replace("[?ROC_ma_stage|0]", "6"),
                self.agenda_loc["ROC_ma_gui_action_execution_desc"],
                self.agenda_loc["ROC_ma_gui_action_waiting_successor_desc"],
            ],
            "ROC_ce_gui_performance": [
                self.loc["ROC_ce_gui_performance"].replace("[?ROC_ce_actual|0]", "100")
                .replace("[?ROC_ce_expected|0]", "100").replace("[?ROC_ce_pressure|0]", "100"),
                self.loc["ROC_ce_gui_performance_waiting_term"],
                self.loc["ROC_ce_gui_performance_initializing"],
            ],
            "ROC_ce_gui_project_name": ["当前项目：筹办实业"],
            "ROC_ce_gui_project_status": [
                "项目状态：项目建设中", "项目状态：暂无在建项目；可从已解锁工程中选择",
            ],
            "ROC_ce_gui_project_progress": [
                "实物进度 100%；目标 100%", self.loc["ROC_ce_gui_project_progress_idle"],
            ],
            "ROC_ce_gui_policy_axis": [
                self.loc["ROC_ce_gui_policy_axis"].replace("[ROOT.ROC_ce_policy_tier_name]", "公有化三档")
                .replace("[?ROC_ce_policy_axis|+0]", "+100").replace("[?ROC_ce_policy_pending|+0]", "+30")
                .replace("[?ROC_ma_policy_pending|+0]", "−30"),
                self.loc["ROC_ce_gui_policy_initializing"],
            ],
            "ROC_ce_gui_policy_route": ["现行办法：阮啸仙·公有审计", "现行办法：尚未选择部长办法"],
            "ROC_ce_gui_policy_effects": ["当前档效果：" + longest_structure_effect, self.loc["ROC_ce_gui_policy_effect_initializing"]],
            "ROC_ce_gui_parties_heading": [self.loc["ROC_ce_gui_parties_heading"]],
            "ROC_ce_gui_left_favor": ["大同党左派 100/100", self.loc["ROC_ce_gui_favor_initializing_left"]],
            "ROC_ce_gui_center_favor": ["大同党中派 100/100", self.loc["ROC_ce_gui_favor_initializing_center"]],
            "ROC_ce_gui_right_favor": ["大同党右派 100/100", self.loc["ROC_ce_gui_favor_initializing_right"]],
            "ROC_ce_gui_committee_heading": [self.loc["ROC_ce_gui_committee_heading"]],
            "ROC_ce_gui_head": [
                f"首脑：{minister} · {status}"
                for minister in ("谭平山", "黄炎培", self.loc["ROC_econ_head_unknown"])
                for status in (self.loc["ROC_econ_gui_head_crisis"], self.loc["ROC_econ_gui_head_mismatch"])
            ],
        }
        for name, samples in lines.items():
            widget = widgets[name]
            width = int(scalar(widget, "maxWidth"))
            max_lines = int(scalar(widget, "maxHeight")) // 20
            font_name = scalar(widget, "font")
            font = title_font if font_name == "hoi_18mbs" else small_font if font_name == "Arial_14s" else game_font
            for text in samples:
                text = re.sub(r"\[\?[^\]]+\]", "100", text)
                text = re.sub(r"\[ROOT\.[^\]]+\]", "公有三档", text)
                used_lines = 1
                pixels = 0
                for character in text:
                    advance = font.get(ord(character), small_font.get(ord(character), 14))
                    if pixels + advance > width:
                        used_lines += 1
                        pixels = 0
                    pixels += advance
                self.assertLessEqual(used_lines, max_lines, f"{name} exceeds {max_lines} lines with {text!r}")


if __name__ == "__main__":
    unittest.main()
