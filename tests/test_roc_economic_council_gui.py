"""Static contract checks for the compact ROC committee agenda overview."""

from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_sichuan_red_opportunity import parse_clausewitz

GUI_FILE = Path("interface/ROC_economic_council.gui")
GUI_LOC = Path("localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml")
COMMITTEE_LOC = Path("localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml")
COMMITTEE_SCRIPT = Path("common/scripted_localisation/ROC_scripted_localisation.txt")
COMMITTEE_EVENTS = Path("events/ROC_committee.txt")
COMMITTEE_RULES = Path("localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml")
LEGISLATION_LOC = Path("localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml")
ECON_LOC = Path("localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml")
MAIN_LOC = Path("localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml")
LEGISLATION_EVENTS = Path("events/ROC_legislation.txt")
ECONOMIC_SCRIPT = Path("common/scripted_localisation/ROC_scripted_localisation.txt")
POWER_BALANCE_GUI = Path("interface/powerbalanceview.gui")

FOCUS_GROUPS = {
    "left": "zuoyilianmeng lianluogemingyoudang tuijinsuoyouzhigeming tudigaigejijinhua jiakuaigongsiheyingjincheng qianghuagonghuigemingxing queligongyouzhijingjizhutidiwei weichinonghuiwuzhuang kuodanongcunhezuosheguimo gemingjijinhua youxiangongnongquanyi zhengduogeminglingdaoquan xianqililunlunzhan dajixiuzhengfenzi jixugeming".split(),
    "center": "gemingtongyizhanxian qianghuazhengzhituanjie jijicanzhengyizheng xiezhugongyegaizao xiezhunongyegaizao luoshixinjingjifa zhichisansanzhizhengfu peihekaizhanqunzhongyundong jicengjibuhezuo qianghuahezuoxuanchuan yantaogeminglilun tuijinkuadanghezuo yazhifenliezhuyi yongbaogemingweiyuanhuizhengzhi jingchenghezuo".split(),
    "right": "youyilianmeng ziyoudatongmeng jingjihuanjingfanglue yaoqiubaozhangminqiquanyi huanhexiangcundouzheng jianadaqiyejiaruhui tiyihuifuguangjiaosuo tuidongnongcunjingjihuazhuanxiang tudiliuzhuanziyouhua gemingziyouhua xuanyangzhengzhiminzhu yaoqiusuxingxianzheng fangkuanzudangshenhe zhiyidatonghui lunliuzuozhuang".split(),
}
ALL_FOCI = {focus for group in FOCUS_GROUPS.values() for focus in group}
WIDGETS = {
    "ROC_econ_gui_title", "ROC_econ_gui_mandate", "ROC_econ_gui_minister_line", "ROC_econ_gui_council_line",
    "ROC_econ_gui_effect_values",
    "ROC_econ_gui_radicalization_line", "ROC_econ_gui_opposition_line",
    "ROC_econ_gui_left_line", "ROC_econ_gui_left_meta",
    "ROC_econ_gui_center_line", "ROC_econ_gui_center_meta",
    "ROC_econ_gui_right_line", "ROC_econ_gui_right_meta",
}
DEFINED_TEXTS = {
    "ROC_committee_status", "ROC_committee_radicalization_text", "ROC_committee_time_effect_summary",
    "ROC_committee_opposition_target_text",
    "ROC_committee_objection_target_name", "ROC_committee_left_agenda_name",
    "ROC_committee_center_agenda_name", "ROC_committee_right_agenda_name",
    "ROC_committee_left_agenda_meta", "ROC_committee_center_agenda_meta",
    "ROC_committee_right_agenda_meta",
}


def read_script(path):
    return parse_clausewitz((ROOT / path).read_text(encoding="utf-8-sig"), path.as_posix())


def read_loc(path):
    text = (ROOT / path).read_text(encoding="utf-8-sig")
    entries, duplicates = {}, []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#") or line == "l_simp_chinese:":
            continue
        match = re.fullmatch(r'([\w.\-]+):\d*\s*"(.*)"', line)
        if not match:
            raise AssertionError(f"unsupported localization at {path}:{number}: {line}")
        key, value = match.groups()
        if key in entries:
            duplicates.append(key)
        entries[key] = value
    return entries, duplicates


def entries_named(entries, key):
    found = [value for name, value in entries if name == key]
    if len(found) != 1:
        raise AssertionError(f"expected one {key}, got {len(found)}")
    return found[0]


def blocks_named(entries, key):
    return [value for name, value in entries if name == key and isinstance(value, list)]


def descendants(entries):
    for key, value in entries:
        yield key, value
        if isinstance(value, list):
            yield from descendants(value)


def defined_texts(script):
    return {entries_named(body, "name"): body for key, body in script if key == "defined_text"}


def legacy_loc(path, key):
    text = (ROOT / path).read_text(encoding="utf-8-sig")
    match = re.search(r'(?m)^[ \t]*' + re.escape(key) + r':0[ \t]+"([^"]*)"', text)
    if not match:
        raise AssertionError(f"missing {key}")
    return match.group(1)


def font_advances(path):
    result = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = re.search(r"\bchar id=(\d+).*?\bxadvance=(-?\d+)", line)
        if match:
            result[int(match.group(1))] = int(match.group(2))
    if not result:
        raise AssertionError(f"no advances in {path}")
    return result


class RocCommitteeGuiContract(unittest.TestCase):
    def test_economic_category_and_native_power_balance_keep_chinese_localizations(self):
        description = legacy_loc(
            "localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml",
            "ROC_economic_administration_desc",
        )
        self.assertEqual(
            legacy_loc("localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml", "ROC_economic_administration"),
            "中央经济施政",
        )
        for word in ("预算", "工程", "部长"):
            self.assertIn(word, description)
        self.assertIn("革命委员会", description)
        self.assertIn("拖他后腿", description)
        self.assertNotIn("负值自由化", description)
        self.assertNotIn("正值公有化", description)

        committee_title = legacy_loc(MAIN_LOC, "ROC_focus_sanpai")
        committee_description = legacy_loc(MAIN_LOC, "ROC_focus_sanpai_desc")
        self.assertEqual(committee_title, "革命委员会")
        for phrase in ("广州革命委员会", "最高统治机构", "大同会居于主导地位", "众多革命友党"):
            self.assertIn(phrase, committee_description)
        self.assertNotIn("象征", committee_description)
        self.assertNotIn("名义最高", committee_description)
        self.assertGreaterEqual(len(committee_description), 100)
        self.assertLessEqual(len(committee_description), 150)

        localized = {}
        for path in (ROOT / "localisation/simp_chinese").glob("*.yml"):
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                match = re.match(r"^\s*([\w.\-]+):\d+\s+\"([^\"]*)\"", line)
                if match:
                    localized.setdefault(match.group(1), []).append(match.group(2))
        economy_keys = {
            "ROC_ce_gui_title", "ROC_ce_gui_performance", "ROC_ce_gui_project_name",
            "ROC_ce_gui_project_status", "ROC_ce_gui_project_progress",
            "ROC_ce_gui_parties_heading", "ROC_ce_gui_left_favor", "ROC_ce_gui_center_favor", "ROC_ce_gui_right_favor",
            "ROC_ce_gui_no_delivery_target",
        }
        missing = sorted(
            key for key in economy_keys
            if not any(re.search(r"[\u4e00-\u9fff]", value) for value in localized.get(key, []))
        )
        native_gui = (ROOT / POWER_BALANCE_GUI).read_text(encoding="utf-8-sig")
        title = re.search(r'name\s*=\s*"title"[\s\S]*?text\s*=\s*"([^"]+)"', native_gui)
        self.assertIsNotNone(title)
        title_key = title.group(1)
        power_balance_title_missing = not any(
            value == "权力平衡" for value in localized.get(title_key, [])
        )
        self.assertEqual(
            {"economic_category_missing": missing, "power_balance_title_missing": power_balance_title_missing},
            {"economic_category_missing": [], "power_balance_title_missing": False},
        )
        self.assertEqual(title_key, "TOD_power_balance_title")
        self.assertEqual(legacy_loc(MAIN_LOC, title_key), "权力平衡")
        self.assertEqual(legacy_loc(MAIN_LOC, "ROC_balance_of_power_category_desc"), "旧经济权力平衡机制已停用。请在中央经济施政分类办理预算、工程与中央党派协商。")
        self.assertNotIn("负值自由化", legacy_loc(MAIN_LOC, "ROC_balance_of_power_category_desc"))

    def test_panel_is_compact_and_excludes_economic_fields(self):
        gui = read_script(GUI_FILE)
        gui_types = entries_named(gui, "guiTypes")
        windows = [
            body for body in blocks_named(gui_types, "containerWindowType")
            if entries_named(body, "name") == "ROC_economic_council_window"
        ]
        self.assertEqual(len(windows), 1)
        window = windows[0]
        size = dict(entries_named(window, "size"))
        self.assertEqual(size.get("width"), "500")
        self.assertEqual(int(size["height"]), 450)

        widgets = blocks_named(window, "instantTextboxType")
        self.assertEqual({entries_named(w, "name") for w in widgets}, WIDGETS)
        boxes = []
        for widget in widgets:
            name = entries_named(widget, "name")
            pos = dict(entries_named(widget, "position"))
            x, y = int(pos["x"]), int(pos["y"])
            width, height = int(entries_named(widget, "maxWidth")), int(entries_named(widget, "maxHeight"))
            expected_font = "hoi_18mbs" if name == "ROC_econ_gui_title" else "hoi_16mbs"
            self.assertEqual(entries_named(widget, "font"), expected_font)
            self.assertLessEqual(width, 400)
            self.assertGreaterEqual(x, 50)
            self.assertLessEqual(x + width, 450)
            self.assertLessEqual(y + height, int(size["height"]))
            boxes.append((y, y + height, name))
        boxes.sort()
        for a, b in zip(boxes, boxes[1:]):
            self.assertLessEqual(a[1], b[0], f"{a[2]} overlaps {b[2]}")
        self.assertFalse(blocks_named(window, "iconType"))
        self.assertFalse(blocks_named(window, "buttonType"))
        self.assertFalse(blocks_named(window, "progressBarType"))

        gui_loc, duplicates = read_loc(GUI_LOC)
        self.assertEqual([key for key in duplicates if key.startswith("ROC_econ_gui_")], [])
        self.assertEqual(gui_loc["ROC_econ_gui_title"], "革命委员会总览")
        visible = " ".join(gui_loc[key] for key in WIDGETS)
        for forbidden in ("ROC_bill_", "经济项目", "当前议案", "候选提案", "合作社", "部门审批", "任期", "试点", "产业路线", "批文"):
            self.assertNotIn(forbidden, visible)
        self.assertEqual("[ROOT.ROC_committee_radicalization_text]", gui_loc["ROC_econ_gui_radicalization_line"])
        self.assertIn("[ROOT.ROC_committee_opposition_target_text]", gui_loc["ROC_econ_gui_opposition_line"])
        committee_loc, _ = read_loc(COMMITTEE_LOC)
        for side, days in (("left", "ROC_econ_left_days"), ("center", "ROC_econ_center_days"), ("right", "ROC_econ_right_days")):
            self.assertIn(f"[ROOT.ROC_committee_{side}_agenda_name]", gui_loc[f"ROC_econ_gui_{side}_line"])
            self.assertIn(f"[ROOT.ROC_committee_{side}_agenda_meta]", gui_loc[f"ROC_econ_gui_{side}_meta"])
            self.assertIn(days, committee_loc[f"ROC_committee_gui_meta_{side}_active"])

    def test_agenda_names_cover_all_45_focuses_and_handle_inactive_states(self):
        script = read_script(COMMITTEE_SCRIPT)
        defs = defined_texts(script)
        self.assertEqual({name for name in defs if name.startswith("ROC_committee_")}, DEFINED_TEXTS)
        manager_effects = {
            "ROC_committee_gui_effect_ruan": "ROC_idea_RuanXiaoxian",
            "ROC_committee_gui_effect_chen": "ROC_idea_ChenZanxian",
            "ROC_committee_gui_effect_yu": "ROC_idea_YuShude",
            "ROC_committee_gui_effect_yan": "ROC_idea_YanYangchu",
            "ROC_committee_gui_effect_xiao": "ROC_idea_XiaoZheng",
        }
        summary_keys = {
            entries_named(branch, "localization_key"):
            list(descendants(entries_named(branch, "trigger")))
            for branch in blocks_named(defs["ROC_committee_time_effect_summary"], "text")
        }
        expected_dynamic = set(manager_effects) | {
            "ROC_committee_gui_effect_postwar", "ROC_committee_gui_effect_ended",
            "ROC_committee_gui_effect_paused", "ROC_committee_gui_effect_unknown",
        }
        self.assertEqual(expected_dynamic, set(summary_keys))
        for loc_key, idea in manager_effects.items():
            triggers = summary_keys[loc_key]
            self.assertIn(("ROC_ma_can_run", "yes"), triggers, loc_key)
            self.assertIn(("has_idea", idea), triggers, loc_key)
        self.assertIn(("has_country_flag", "ROC_postwar_active"), summary_keys["ROC_committee_gui_effect_postwar"])
        self.assertIn(("OR", [
            ("ROC_has_jixugeming", "yes"),
            ("ROC_has_jingchenghezuo", "yes"),
            ("ROC_has_lunliuzuozhuang", "yes"),
        ]), summary_keys["ROC_committee_gui_effect_ended"])
        self.assertIn(("NOT", [("ROC_ma_can_run", "yes")]), summary_keys["ROC_committee_gui_effect_paused"])
        committee_loc, _ = read_loc(COMMITTEE_LOC)
        self.assertIn("左派提前7日", committee_loc["ROC_committee_gui_effect_ruan"])
        self.assertIn("共同提前14日", committee_loc["ROC_committee_gui_effect_ruan"])
        self.assertIn("右派延后21日", committee_loc["ROC_committee_gui_effect_ruan"])
        self.assertIn("议程暂不折算", committee_loc["ROC_committee_gui_effect_paused"])
        self.assertIn("不再折算", committee_loc["ROC_committee_gui_effect_postwar"])
        self.assertEqual(len(ALL_FOCI), 45)
        for side, expected in FOCUS_GROUPS.items():
            body = defs[f"ROC_committee_{side}_agenda_name"]
            actual = [
                value for key, value in descendants(body)
                if key == "localization_key" and value in ALL_FOCI
            ]
            self.assertEqual(actual, expected)
            keys = [entries_named(branch, "localization_key") for branch in blocks_named(body, "text")]
            for fallback in ("postwar", "not_established", "not_started", "ended", "initializing"):
                self.assertIn(f"ROC_committee_gui_agenda_{fallback}", keys)
        for side in ("left", "center", "right"):
            keys = [entries_named(branch, "localization_key") for branch in blocks_named(defs[f"ROC_committee_{side}_agenda_meta"], "text")]
            for fallback in ("postwar", "ended", "not_established", "initializing"):
                self.assertIn(f"ROC_committee_gui_meta_{fallback}", keys)
            self.assertIn(f"ROC_committee_gui_meta_{side}_scheduled", keys)
            mission = {"left": "zuopai", "center": "zhongpai", "right": "youpai"}[side]
            self.assertIn(("has_active_mission", f"ROC_decision_{mission}"), list(descendants(defs[f"ROC_committee_{side}_agenda_meta"])))
        status_entries = list(descendants(defs["ROC_committee_status"]))
        for mission in ("zuopai", "zhongpai", "youpai"):
            self.assertIn(("has_active_mission", f"ROC_decision_{mission}"), status_entries)
        self.assertIn("yaoqiubaozhangminqiquanyi", FOCUS_GROUPS["right"])
        self.assertNotIn("yaoqiubaozhangminquanyi", FOCUS_GROUPS["right"])

        committee_loc, duplicates = read_loc(COMMITTEE_LOC)
        self.assertEqual([key for key in duplicates if key.startswith("ROC_committee")], [])
        refs = {v for k, v in descendants(script) if k == "localization_key" and isinstance(v, str)}
        self.assertTrue({v for v in refs if v.startswith("ROC_committee_gui_")} <= set(committee_loc))
        main = (ROOT / MAIN_LOC).read_text(encoding="utf-8-sig")
        for mission in ("ROC_decision_zuopai", "ROC_decision_zhongpai", "ROC_decision_youpai"):
            self.assertIn("$ROC_committee_rules_tt$", legacy_loc(MAIN_LOC, mission + "_desc"))
        self.assertEqual(legacy_loc(MAIN_LOC, "ROC_decision_zuopai"), "左翼激进行动中")
        self.assertEqual(legacy_loc(MAIN_LOC, "ROC_decision_youpai"), "右翼激进行动中")
        self.assertEqual(legacy_loc(MAIN_LOC, "ROC_decision_zhongpai"), "共同议程推进中")
        self.assertEqual(legacy_loc(MAIN_LOC, "ROC_decision_zuoxiantuoxie"), "拖延左派议程")
        self.assertEqual(legacy_loc(MAIN_LOC, "ROC_decision_youxiantuoxie"), "拖延右派议程")
        for key in ("ROC_tooltip_bop_sanpai_you_1", "ROC_tooltip_bop_sanpai_zuo_1", "ROC_tooltip_minister_sanpai_dongbiwu", "ROC_tooltip_sanpai_sansanzhi"):
            self.assertNotRegex(legacy_loc(MAIN_LOC, key), r"左派激进化|右派激进化|拥护统一战线")
        for focus in ALL_FOCI:
            self.assertRegex(main, rf"(?m)^[ \t]*{re.escape(focus)}:0\s+\"")
            self.assertLessEqual(len(legacy_loc(MAIN_LOC, focus + "_desc")), 110)
        desc = legacy_loc(MAIN_LOC, "youxiangongnongquanyi_desc")
        self.assertGreaterEqual(len(desc), 60)
        self.assertLessEqual(len(desc), 110)

    def test_event_localization_coverage_and_admin_language(self):
        event_text = (ROOT / COMMITTEE_EVENTS).read_text(encoding="utf-8-sig")
        event_refs = set(re.findall(r"\b(?:title|desc|name)\s*=\s*(ROC_committee\.\d+\.[A-Za-z]+)", event_text))
        required = {f"ROC_committee.{event}.{suffix}" for event in (1, 2, 3) for suffix in ("t", "d", "a", "b")}
        self.assertEqual(event_refs, required)
        committee_loc, _ = read_loc(COMMITTEE_LOC)
        self.assertTrue(required <= set(committee_loc))
        self.assertIn("经济部长", read_loc(GUI_LOC)[0]["ROC_econ_gui_mandate"])
        for event, phrase in ((1, "未能列案的会社代表"), (2, "未能列案的会社代表"), (3, "提案方")):
            body = committee_loc[f"ROC_committee.{event}.d"]
            self.assertIn(phrase, body)
            self.assertNotRegex(body, r"落后派|领先派")
        self.assertNotIn("连续议程", committee_loc["ROC_committee.2.d"])
        self.assertNotIn("围绕[ROOT.ROC_committee_objection_target_name]的议程", committee_loc["ROC_committee.3.d"])
        rules, _ = read_loc(COMMITTEE_RULES)
        self.assertTrue({"ROC_committee_delay_21_tt", "ROC_committee_delay_7_tt", "ROC_committee_stale_close", "ROC_committee_stale_tt"} <= set(rules))
        for event in (1, 2, 3):
            body = committee_loc[f"ROC_committee.{event}.d"]
            self.assertIn("[ROOT.ROC_committee_objection_target_name]", body)
            self.assertNotRegex(body, r"\b(?:21|15)\b")
        self.assertIn("未能列案的会社代表", " ".join(committee_loc[f"ROC_committee.{i}.d"] for i in (1, 2, 3)))
        self.assertIn("少数派", committee_loc["ROC_committee.2.d"])
        self.assertIn("临时休会", committee_loc["ROC_committee.3.t"])

        legislation, duplicates = read_loc(LEGISLATION_LOC)
        self.assertEqual([key for key in duplicates if key.startswith("ROC_legislation")], [])
        for key in ("ROC_legislation_readiness_sector", "ROC_legislation_readiness_vote", "ROC_legislation_readiness_condition", "ROC_legislation_readiness_short", "ROC_legislation_readiness_guarantee"):
            self.assertIn("[?ROC_bill_economic_support|0]", legislation[key])
            self.assertIn("[?ROC_bill_support|0]/[?ROC_bill_requirement|0]", legislation[key])
        self.assertIn("[?ROC_bill_sector_requirement|0]", legislation["ROC_legislation_readiness_sector"])
        for key in ("ROC_legislation_readiness_idle", "ROC_legislation_readiness_approved"):
            self.assertNotIn("[?ROC_bill_", legislation[key])
        source = (ROOT / LEGISLATION_EVENTS).read_text(encoding="utf-8-sig")
        for event in (101, 102):
            body = legislation[f"ROC_legislation.{event}.d"]
            self.assertIn("项目尚未启动" if event == 102 else "不等于项目已经开工", body)
            self.assertIn("点击原项目", body)
            self.assertIn("原实施费用", body)
            self.assertNotRegex(body, r"按约开工|项目终于开办|项目可以开办")
        for event in (12, 22, 32, 42, 52):
            key = f"ROC_legislation.{event}.desc"
            self.assertIn(key, legislation)
            self.assertIn(key, source)
            self.assertNotRegex(legislation[key], r"委员会|党外|友党|联署|表决|投票")
            self.assertIn("撤回", legislation[f"ROC_legislation.{event}.d"])
        for key in ("ROC_legislation_stage_consultation", "ROC_legislation_stage_hearing", "ROC_legislation_readiness_vote", "ROC_legislation_readiness_short"):
            self.assertTrue(any(word in legislation[key] for word in ("行业", "核账", "会签", "材料", "行政")))
        for event in (101, 102, 103, 104, 105):
            for suffix in ("t", "d", "a"):
                self.assertIn(f"ROC_legislation.{event}.{suffix}", legislation)
            self.assertNotRegex(legislation[f"ROC_legislation.{event}.d"], r"委员会|党外|友党|联署|表决|投票")
        econ, _ = read_loc(ECON_LOC)
        self.assertIn("行业利益方", econ["ROC_decision_bop_jingjidahui_desc"])
        self.assertIn("核账会签", econ["ROC_decision_bop_jingjidahui_desc"])
        self.assertNotIn("党外联署", econ["ROC_decision_bop_jingjidahui_desc"])

    def test_changed_localizations_have_bom_and_unique_keys(self):
        data = (ROOT / MAIN_LOC).read_bytes()
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        _, duplicates = read_loc(MAIN_LOC)
        # These duplicates predate the merge in the original main country file.
        legacy_duplicates = {"huananzhaofusi", "huananzhaofusi_DEF", "huananzhaofusi_ADJ", "ROC_idea_XiaMinghan"}
        legacy_duplicates.update("ROC_pingheng.9999." + suffix for suffix in "abcefghijk")
        self.assertEqual([key for key in duplicates if key not in legacy_duplicates], [])

    def test_agenda_and_status_lines_fit_measured_font_advances(self):
        gui_loc, _ = read_loc(GUI_LOC)
        committee_loc, _ = read_loc(COMMITTEE_LOC)
        econ_loc, _ = read_loc(ECON_LOC)
        central_loc, _ = read_loc(Path("localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml"))
        titles = {focus: legacy_loc(MAIN_LOC, focus) for focus in ALL_FOCI}
        manager_data = (
            ("loc_ROC_idea_RuanXiaoxian", "ROC_ce_gui_route_audit"),
            ("loc_ROC_idea_ChenZanxian", "ROC_ce_gui_route_labor"),
            ("loc_ROC_idea_YuShude", "ROC_ce_gui_route_cooperative"),
            ("loc_ROC_idea_YanYangchu", "ROC_ce_gui_route_rural"),
            ("loc_ROC_idea_XiaoZheng", "ROC_ce_gui_route_farmers"),
        )
        manager_line = gui_loc["ROC_econ_gui_minister_line"]
        effect_line = gui_loc["ROC_econ_gui_effect_values"]
        lines = [
            gui_loc["ROC_econ_gui_title"],
            gui_loc["ROC_econ_gui_mandate"],
            *[manager_line.replace("[ROOT.ROC_econ_gui_minister]", legacy_loc(MAIN_LOC, name)).replace(
                "[ROOT.ROC_ce_minister_route]", central_loc[route]
            ) for name, route in manager_data],
            manager_line.replace("[ROOT.ROC_econ_gui_minister]", econ_loc["ROC_econ_gui_minister_none"]).replace(
                "[ROOT.ROC_ce_minister_route]", central_loc["ROC_ce_gui_route_none"]
            ),
            *[effect_line.replace("[ROOT.ROC_committee_time_effect_summary]", committee_loc[key]) for key in (
                "ROC_committee_gui_effect_ruan", "ROC_committee_gui_effect_chen", "ROC_committee_gui_effect_yu",
                "ROC_committee_gui_effect_yan", "ROC_committee_gui_effect_xiao", "ROC_committee_gui_effect_paused",
                "ROC_committee_gui_effect_postwar", "ROC_committee_gui_effect_ended", "ROC_committee_gui_effect_unknown",
            )],
            "会议状态：" + committee_loc["ROC_committee_gui_status_active"],
            "会议状态：" + committee_loc["ROC_committee_gui_status_waiting"],
            "会议状态：" + committee_loc["ROC_committee_gui_status_postwar"],
            "其他党派激进程度：100/100",
            "主要反对目标：" + committee_loc["ROC_committee_gui_target_center"],
        ]
        for side, prefix in (("left", "大同党左派："), ("center", "大同党中派："), ("right", "大同党右派：")):
            lines.extend(prefix + title for title in titles.values())
            for state in ("active", "scheduled", "waiting", "ended", "postwar", "not_established", "initializing"):
                key = f"ROC_committee_gui_meta_{side}_{state}" if state in ("active", "scheduled", "waiting") else f"ROC_committee_gui_meta_{state}"
                meta = committee_loc[key]
                meta = re.sub(r"\[\?ROC_committee_(?:left|center|right)_progress\|0\]", "15", meta)
                meta = re.sub(r"\[\?ROC_econ_(?:left|center|right)_days\|0\]", "1095", meta)
                lines.append(prefix + meta)

        game = font_advances(ROOT.parents[1] / "gfx/fonts/hoi_16mbs.fnt")
        arial = font_advances(ROOT / "gfx/fonts/Arial_14s.fnt")
        for name, primary, fallback in (("hoi_16mbs", game, arial), ("Arial_14s", arial, game)):
            for line in lines:
                width, missing = 0, []
                for char in line:
                    advance = primary.get(ord(char), fallback.get(ord(char)))
                    if advance is None:
                        missing.append(char)
                    else:
                        width += advance
                self.assertFalse(missing, f"{name} lacks advances for {set(missing)!r}")
                self.assertLessEqual(width, 400, f"{name}: {width}px: {line}")


if __name__ == "__main__":
    unittest.main()
