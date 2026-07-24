from pathlib import Path
import math
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


UKR_ICON_MAP = {
    "UKR_daxuan": "GFX_UKR_daxuan",
    "UKR_dawukelan": "GFX_UKR_dawukelan",
    "UKR_zhenyayijianfenzi": "GFX_UKR_zhenyayijianfenzi",
    "UKR_shuliyuanshouquanwei": "GFX_UKR_shuliyuanshouquanwei",
    "UKR_qingniandeminzusichao": "GFX_UKR_qingniandeminzusichao",
    "UKR_qiangdiaozhengzhichuantong": "GFX_UKR_qiangdiaozhengzhichuantong",
    "UKR_dazaomofanjun": "GFX_UKR_dazaomofanjun",
    "UKR_gesakexunlianfa": "GFX_UKR_gesakexunlianfa",
    "UKR_duixianchengnuo": "GFX_UKR_duixianchengnuo",
    "UKR_jiazhengzhengfudingdan": "GFX_UKR_jiazhengzhengfudingdan",
    "UKR_wukelanguofangweiyuanhui": "GFX_UKR_wukelanguofangweiyuanhui",
    "UKR_jihuashishi": "GFX_UKR_jihuashishi",
    "UKR_huangse_lanse": "GFX_UKR_huangse_lanse",
}

UKR_DYNAMIC_EFFECT_TOOLTIPS = {
    "UKR_shengyuweihan": "UKR_shengyuweihan_xiaoguo",
    "UKR_zhengdunjunguantuan": "UKR_zhengdunjunguantuan_xiaoguo",
    "UKR_tigaojunxiang": "UKR_tigaojunxiang_xiaoguo",
    "UKR_xunliancaodian": "UKR_xunliancaodian_xiaoguo",
    "UKR_zhihuizhongshu": "UKR_zhihuizhongshu_xiaoguo",
    "UKR_luoshijilvguizhang": "UKR_luoshijilvguizhang_xiaoguo",
    "UKR_kuodapeixunguimo": "UKR_kuodapeixunguimo_xiaoguo",
    "UKR_xiangcundidaoxiaodui": "UKR_xiangcundidaoxiaodui_xiaoguo",
    "UKR_shulilaobingmofan": "UKR_shulilaobingmofan_xiaoguo",
    "UKR_jixingjunxunlian": "UKR_jixingjunxunlian_xiaoguo",
    "UKR_baoweizhepianretu": "UKR_baoweizhepianretu_xiaoguo",
}

BATTALION_MANPOWER = {
    "infantry": 1000,
    "cavalry": 1000,
    "mountaineers": 1000,
    "motorized": 500,
    "artillery": 500,
    "light_armor": 500,
    "medium_armor": 500,
    "heavy_armor": 500,
    "modern_armor": 500,
}


def balanced_block(text: str, opening: int) -> str:
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[opening + 1:index]
    raise AssertionError("unbalanced HOI4 block")


def named_templates(text: str) -> dict[str, list[str]]:
    templates = {}
    for match in re.finditer(r"division_template\s*=\s*\{", text):
        block = balanced_block(text, match.end() - 1)
        name = re.search(r'(?m)^\s*name\s*=\s*"([^"]*)"', block)
        regiments = re.search(r"regiments\s*=\s*\{", block)
        if not name or not regiments:
            continue
        regiment_block = balanced_block(block, regiments.end() - 1)
        types = re.findall(
            r"(?m)^\s*(infantry|cavalry|mountaineers|motorized|artillery|"
            r"light_armor|medium_armor|heavy_armor|modern_armor)\s*=\s*\{",
            regiment_block,
        )
        templates[name.group(1)] = types
    return templates


def named_focus_blocks(text: str) -> dict[str, str]:
    focuses = {}
    for match in re.finditer(r"(?m)^[ \t]*focus\s*=\s*\{", text):
        block = balanced_block(text, match.end() - 1)
        focus_id = re.search(r"(?m)^\s*id\s*=\s*(\S+)", block)
        if focus_id:
            focuses[focus_id.group(1)] = block
    return focuses


def state_provinces_with_owner(owner: str) -> set[int]:
    provinces = set()
    for path in (ROOT / "history/states").glob("*.txt"):
        text = path.read_text(encoding="utf-8-sig")
        owner_match = re.search(r"(?m)^\s*owner\s*=\s*(\w+)", text)
        province_match = re.search(r"(?s)provinces\s*=\s*\{(.*?)\}", text)
        if owner_match and owner_match.group(1) == owner and province_match:
            provinces.update(
                int(value) for value in re.findall(r"\b\d+\b", province_match.group(1))
            )
    return provinces


def victory_point_provinces() -> set[int]:
    provinces = set()
    for path in (ROOT / "history/states").glob("*.txt"):
        text = path.read_text(encoding="utf-8-sig")
        for match in re.finditer(r"victory_points\s*=\s*\{", text):
            block = balanced_block(text, match.end() - 1)
            provinces.update(
                int(value)
                for value in re.findall(r"(?m)^\s*(\d+)\s+[\d.]+", block)
            )
    return provinces


def oob_locations(relative_path: str) -> list[int]:
    return [
        int(value)
        for value in re.findall(
            r"(?m)^\s*location\s*=\s*(\d+)\s*$", read(relative_path)
        )
    ]


def oob_manpower(relative_path: str) -> int:
    text = read(relative_path)
    templates = named_templates(text)
    total = 0
    for match in re.finditer(r"(?<![A-Za-z0-9_])division\s*=\s*\{", text):
        block = balanced_block(text, match.end() - 1)
        template = re.search(r'division_template\s*=\s*"([^"]*)"', block)
        if not template:
            continue
        total += sum(
            BATTALION_MANPOWER[battalion]
            for battalion in templates[template.group(1)]
        )
    return total


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8-sig")


class EuropeMilitaryAndFocusTest(unittest.TestCase):
    def test_unit_name_group_references_are_removed_from_oobs(self):
        descriptor = read("descriptor.mod")
        self.assertIn('replace_path="common/units/names_divisions"', descriptor)
        unit_files = (ROOT / "history/units").glob("*.txt")
        for path in unit_files:
            active_text = "\n".join(
                line
                for line in path.read_text(encoding="utf-8-sig").splitlines()
                if not line.lstrip().startswith("#")
            )
            self.assertNotIn("division_names_group", active_text, path.name)

    def test_ukraine_design_icons_are_installed_and_unique(self):
        focus = read("common/national_focus/Ukraine.txt")
        self.assertNotRegex(focus, r"completion_reward\s*=\s*\{\s*\}")
        gfx = read("interface/_TOD_goals.gfx")
        texture_paths = []
        for focus_id, sprite in UKR_ICON_MAP.items():
            self.assertRegex(
                focus,
                rf"(?s)\bid\s*=\s*{re.escape(focus_id)}\b.*?\bicon\s*=\s*{re.escape(sprite)}\b",
            )
            sprite_match = re.search(
                rf'(?s)name\s*=\s*"{re.escape(sprite)}".*?texturefile\s*=\s*"([^"]+)"',
                gfx,
            )
            self.assertIsNotNone(sprite_match, sprite)
            texture_paths.append(sprite_match.group(1))
            self.assertTrue((ROOT / sprite_match.group(1)).is_file(), sprite)
        self.assertEqual(len(texture_paths), len(set(texture_paths)))
        self.assertIn("UKR_jifaqianneng =", read("common/ideas/Ukraine_ideas.txt"))
        self.assertIn("local_resources_factor = 0.10", read("common/ideas/Ukraine_ideas.txt"))

    def test_ukraine_focus_icons_have_shine_sprites(self):
        shine = read("interface/UKR_goals_shine.gfx")
        for focus_id in UKR_ICON_MAP:
            sprite = f"GFX_UKR_{focus_id.removeprefix('UKR_')}"
            texture = f"gfx/interface/goals/TOD_UKR_{focus_id.removeprefix('UKR_')}.png"
            self.assertRegex(
                shine,
                rf'(?s)name\s*=\s*"{re.escape(sprite)}_shine".*?'
                rf'animationmaskfile\s*=\s*"{re.escape(texture)}"',
            )
            self.assertIn(
                'animationtexturefile = "gfx/interface/goals/shine_overlay.dds"',
                shine,
            )

    def test_ukraine_and_belarus_starting_manpower_reaches_half_of_hungary(self):
        hungary = oob_manpower("history/units/HUN_1936.txt")
        self.assertGreaterEqual(
            oob_manpower("history/units/UKR_1936.txt"), (hungary + 1) // 2
        )
        self.assertGreaterEqual(
            oob_manpower("history/units/BLR_1936.txt"), (hungary + 1) // 2
        )

    def test_ukraine_and_belarus_starting_manpower_is_about_80_percent_of_hungary(self):
        hungary = oob_manpower("history/units/HUN_1936.txt")
        target = math.ceil(hungary * 0.8)
        for relative_path in (
            "history/units/UKR_1936.txt",
            "history/units/BLR_1936.txt",
        ):
            manpower = oob_manpower(relative_path)
            self.assertGreaterEqual(manpower, target)
            self.assertLessEqual(manpower, target + 1000)

    def test_ukraine_and_belarus_divisions_start_on_victory_points(self):
        victory_points = victory_point_provinces()
        for relative_path in (
            "history/units/UKR_1936.txt",
            "history/units/BLR_1936.txt",
        ):
            locations = oob_locations(relative_path)
            self.assertTrue(locations, relative_path)
            self.assertTrue(
                all(location in victory_points for location in locations),
                (relative_path, locations),
            )

    def test_polish_divisions_are_not_deployed_in_belarusian_states(self):
        belarusian_provinces = state_provinces_with_owner("BLR")
        for province in oob_locations("history/units/POL_1936.txt"):
            self.assertNotIn(province, belarusian_provinces, province)

    def test_russian_european_event_chain_is_installed(self):
        events = read("events/Russia.txt")
        russian_history = read("history/countries/RUS - eluosidiguo.txt")
        for event_id in (
            "TODRussia.1",
            "TODRussia.2",
            "TODRussia.3",
            "TODRussia.4",
            "TODRussia.5",
            "TODRussia.6",
            "TODRussia.7",
            "TODRussia.8",
            "TODRussia.9",
            "TODRussia.10",
        ):
            self.assertIn(f"id = {event_id}", events)
        self.assertIn('country_event = { id = TODRussia.1 days = 30 }', russian_history)
        self.assertNotIn("name = TODRussia.1.d", events)
        self.assertIn("name = TODRussia.1.g", events)
        self.assertIn("date > 1938.2.28", events)
        self.assertIn("date > 1938.8.31", events)
        self.assertIn("date > 1939.2.28", events)
        self.assertNotRegex(events, r"(?m)^\s*despotism\s*=")
        self.assertNotRegex(events, r"(?m)^\s*ruling_party\s*=\s*despotism\s*$")
        self.assertIn("ruling_party = leader_despotism", events)

        localisation = read("localisation/simp_chinese/TOD_Russia_l_simp_chinese.yml")
        for event_id in ("TODRussia.1", "TODRussia.4", "TODRussia.7", "TODRussia.10"):
            self.assertRegex(localisation, rf"(?m)^\s*{event_id}\.t:0\s+\"")
            self.assertRegex(localisation, rf"(?m)^\s*{event_id}\.d:0\s+\"")

    def test_ukraine_and_belarus_use_limited_conscription(self):
        for relative_path in (
            "history/countries/UKR - wukelan.txt",
            "history/countries/BLR - Belarus-Lithuania Federation.txt",
        ):
            self.assertRegex(read(relative_path), r"(?m)^\s*limited_conscription\s*$")

    def test_state_196_is_core_of_ukraine_not_russia(self):
        state = read("history/states/196-Kherson.txt")
        self.assertIn("add_core_of = UKR", state)
        self.assertNotIn("add_core_of = RUS", state)

    def test_ukraine_dynamic_modifiers_have_localised_descriptions(self):
        modifiers = read("common/dynamic_modifiers/TOD_modifiers.txt")
        localisation = read("localisation/simp_chinese/TOD_UKR_Ukraine_l_simp_chinese.yml")
        ids = re.findall(r"(?m)^\s*(UKR_[a-z0-9_]+)\s*=\s*\{", modifiers)
        self.assertEqual(
            {"UKR_yeyudenongminjun", "UKR_gaigechuchengdejundui"},
            set(ids),
        )
        for modifier_id in ids:
            self.assertRegex(localisation, rf"(?m)^\s*{modifier_id}:0\s+\"")
            self.assertRegex(localisation, rf"(?m)^\s*{modifier_id}_desc:0\s+\"")

    def test_ukraine_dynamic_focus_effects_have_visible_tooltips(self):
        focus_blocks = named_focus_blocks(read("common/national_focus/Ukraine.txt"))
        for localisation_path in (
            "localisation/simp_chinese/TOD_UKR_Ukraine_l_simp_chinese.yml",
            "localisation/english/TOD_UKR_Ukraine_l_english.yml",
        ):
            localisation = read(localisation_path)
            for focus_id, tooltip_id in UKR_DYNAMIC_EFFECT_TOOLTIPS.items():
                self.assertIn(focus_id, focus_blocks)
                reward = re.search(
                    r"completion_reward\s*=\s*\{",
                    focus_blocks[focus_id],
                )
                self.assertIsNotNone(reward, focus_id)
                reward_block = balanced_block(
                    focus_blocks[focus_id], reward.end() - 1
                )
                self.assertIn(
                    f"custom_effect_tooltip = {tooltip_id}",
                    reward_block,
                )
                self.assertRegex(
                    localisation,
                    rf"(?m)^\s*{tooltip_id}:0\s+\"",
                )

    def test_ukraine_localisation_has_no_extra_quote_on_focus_name(self):
        for relative_path in (
            "localisation/simp_chinese/TOD_UKR_Ukraine_l_simp_chinese.yml",
            "localisation/english/TOD_UKR_Ukraine_l_english.yml",
        ):
            content = read(relative_path)
            self.assertNotRegex(
                content,
                r"(?m)^\s*UKR_qingniandeminzusichao:0\s+\"[^\"]+\"\"$",
            )

    def test_ukraine_election_completes_matching_focus(self):
        event = read("events/Ukraine.txt")
        democratic = event[event.index("\n\tid = TODUkraine.6") : event.index("\n\tid = TODUkraine.7")]
        leader = event[event.index("\n\tid = TODUkraine.7") :]
        self.assertIn("set_country_flag = UKR_shemin", democratic)
        self.assertIn("complete_national_focus = UKR_dongoudeminzhubaolei", democratic)
        self.assertIn("set_country_flag = UKR_lingxiu", leader)
        self.assertIn("complete_national_focus = UKR_dawukelan", leader)

    def test_country_oobs_are_connected(self):
        ukr_history = read("history/countries/UKR - wukelan.txt")
        self.assertIn('oob = "UKR_1936"', ukr_history)
        self.assertIn('set_naval_oob = "UKR_1936_naval"', ukr_history)
        self.assertRegex(read("history/units/UKR_1936.txt"), r"(?m)^\s*division\s*=")
        self.assertRegex(read("history/units/UKR_1936_naval.txt"), r"(?m)^\s*ship\s*=")

        pol_history = read("history/countries/POL - bolanwangguo.txt")
        self.assertIn('oob = "POL_1936"', pol_history)
        self.assertRegex(read("history/units/POL_1936.txt"), r"(?m)^\s*division\s*=")

        blr_history = read("history/countries/BLR - Belarus-Lithuania Federation.txt")
        self.assertIn('oob = "BLR_1936"', blr_history)
        self.assertRegex(read("history/units/BLR_1936.txt"), r"(?m)^\s*division\s*=")
        self.assertNotIn("division_names_group", read("history/units/POL_1936.txt"))
        self.assertIn("version_name =", read("history/units/UKR_1936_naval.txt"))

    def test_empty_country_histories_use_the_empty_oob_placeholder(self):
        for relative_path in (
            "history/countries/SRC - hongjun.txt",
            "history/countries/XIN - xinan.txt",
        ):
            content = read(relative_path)
            self.assertRegex(content, r'(?m)^\s*oob\s*=\s*"empty"\s*$')
            self.assertNotRegex(content, r'(?m)^\s*oob\s*=\s*""\s*$')

    def test_broken_startup_oobs_have_valid_references(self):
        iraq_oob = read("history/units/IRQ_1936.txt")
        self.assertIn('name = "Firqat Mushaa"', iraq_oob)
        self.assertIn('name = "Silah Alfursan"', iraq_oob)
        self.assertNotIn("division_names_group", iraq_oob)

        france_air_oob = read("history/units/FRA_1936_air_bba.txt")
        self.assertNotIn('"Béarn"', france_air_oob)

        italy_air_oob = read("history/units/ITA_air_bba.txt")
        self.assertNotRegex(italy_air_oob, r"(?m)^\s*849\s*=\s*\{")

    def test_ukraine_starting_ships_have_matching_variants(self):
        country_history = read("history/countries/UKR - wukelan.txt")
        self.assertIn('name = "乌克兰驱逐舰"', country_history)
        self.assertIn('name = "黑海潜艇"', country_history)
        self.assertRegex(
            country_history,
            r"(?s)create_equipment_variant\s*=\s*\{.*?type\s*=\s*ship_hull_light_1",
        )
        self.assertRegex(
            country_history,
            r"(?s)create_equipment_variant\s*=\s*\{.*?type\s*=\s*ship_hull_submarine_1",
        )

    def test_custom_character_origins_have_name_pools(self):
        names = read("common/names/TOD_missing_character_names.txt")
        missing_origins = {
            "ACH", "ANN", "BLT", "BNG", "BRN", "CAU", "CRF", "DAW", "EDO",
            "EXN", "EZO", "FCG", "FEA", "FET", "FRL", "FTS", "FWA", "HAS",
            "HEX", "IEA", "IOF", "JAV", "KMG", "LAF", "LAN", "MEA", "MSO",
            "MSR", "ORI", "PUC", "PUN", "QQD", "RIN", "RYU", "SAR", "SIB",
            "SMT", "SUL", "TAC", "TSO", "TAV", "UPB", "USM", "UTA",
            "VOP", "WJP", "YZR", "ZHR",
        }
        for tag in missing_origins:
            self.assertRegex(
                names,
                rf"(?m)^\s*{tag}\s*=\s*\{{\s*male\s*=\s*\{{\s*names\s*=\s*\{{[^}}]+\}}\s*\}}\s*surnames\s*=\s*\{{[^}}]+\}}\s*\}}",
            )

    def test_frl_naval_spirit_reference_is_defined(self):
        compatibility_ideas = read("common/ideas/TOD_missing_vanilla_ideas.txt")
        vanilla_ideas = read("common/ideas/navy_spirits.txt")
        self.assertNotIn("bureau_of_ordnance_spirit", compatibility_ideas)
        self.assertIn("bureau_of_ordnance_spirit", vanilla_ideas)

    def test_hungarian_east_wall_can_accept_belarus(self):
        focus = read("common/national_focus/hungary.txt")
        self.assertIn("BLR = { add_to_faction = HUN }", focus)
        self.assertNotIn("HUN = { add_to_faction = UKR }", focus)

        event = read("events/Hungary.txt")
        self.assertRegex(event, r"BLR\s*=\s*\{\s*add_to_faction\s*=\s*HUN\s*\}")


if __name__ == "__main__":
    unittest.main()
