"""Narrow script-level checks for Ming civil-war inheritance.

These tests interpret a small subset of the real Clausewitz scripts. They are
not a substitute for testing country scopes and effects in the HOI4 engine.
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOKEN = re.compile(r'#[^\n]*|"(?:\\.|[^"\\])*"|<=|>=|!=|==|[{}=<>!]|[^\s{}=<>!#"]+')


def parse_file(path):
    text = (ROOT / path).read_text(encoding="utf-8-sig")
    tokens = [m.group() for m in TOKEN.finditer(text) if not m.group().startswith("#")]
    pos = 0

    def group(nested=False):
        nonlocal pos
        result = []
        while pos < len(tokens):
            if tokens[pos] == "}":
                if not nested:
                    raise ValueError(f"unexpected closing brace in {path}")
                pos += 1
                return result
            key = tokens[pos]
            pos += 1
            if pos < len(tokens) and tokens[pos] in ("=", "<", ">", "<=", ">=", "!=", "=="):
                operator = tokens[pos]
                pos += 1
                if pos >= len(tokens):
                    raise ValueError(f"missing value in {path}")
                if tokens[pos] == "{":
                    pos += 1
                    value = group(True)
                else:
                    value = tokens[pos].strip('"')
                    pos += 1
                result.append((key, value if operator == "=" else (operator, value)))
            else:
                result.append((None, key.strip('"')))
        if nested:
            raise ValueError(f"unclosed block in {path}")
        return result

    return group()


def children(entries, key):
    return [value for name, value in entries if name == key]


def one(entries, key):
    values = children(entries, key)
    if len(values) != 1:
        raise ValueError(f"expected one {key}, found {len(values)}")
    return values[0]


def walk(entries, path=()):
    for key, value in entries:
        yield path, key, value
        if isinstance(value, list):
            yield from walk(value, path + (key,))


def event(path, event_id):
    matches = [value for key, value in parse_file(path)
               if key == "country_event" and isinstance(value, list)
               and children(value, "id") == [event_id]]
    if len(matches) != 1:
        raise ValueError(f"expected event {event_id}")
    return matches[0]


def focus(focus_id):
    tree = parse_file("common/national_focus/dongbeihongjun.txt")
    matches = [value for _, key, value in walk(tree)
               if key == "focus" and isinstance(value, list)
               and children(value, "id") == [focus_id]]
    if len(matches) != 1:
        raise ValueError(f"expected focus {focus_id}")
    return matches[0]


def transfer_result(effect, *, army=40, navy=8, air=10, stockpile=1000):
    """Apply documented ratios to a fixture; do not emulate the game engine."""
    fields = dict(effect)
    default = float(fields.get("size", 0))
    fraction = lambda name: float(fields.get(name, default))
    keep = fields.get("keep_unit_leaders_trigger", [])
    return {
        "army": army * (1 - fraction("army_ratio")),
        "navy": navy * (1 - fraction("navy_ratio")),
        "air": air * (1 - fraction("air_ratio")),
        "stockpile": stockpile * (1 - fraction("stockpile_ratio")),
        "leaders": ["loyal_general", "loyal_admiral"] if ("always", "yes") in keep else [],
    }


def initial_countries(*present):
    return {tag: {"exists": tag in present, "units": 10 if tag in present else 0,
                  "leaders": [(tag + "_visible", True), (tag + "_hidden", False)]
                  if tag in present else []}
            for tag in ("ROC", "SRC", "SCG", "SIC", "GOS", "XBJ")}


def run_peace_effect(entries, countries, scope):
    """Interpret only country scopes, existence guards, leaders and annexation."""
    for key, value in entries:
        if key == "if" and isinstance(value, list):
            limit = children(value, "limit")
            checks = children(limit[0], "country_exists") if limit else []
            if all(countries[tag]["exists"] for tag in checks):
                run_peace_effect(value, countries, scope)
        elif key in countries and isinstance(value, list):
            run_peace_effect(value, countries, key)
        elif key == "every_unit_leader" and isinstance(value, list):
            target = one(value, "set_nationality")
            include_hidden = children(value, "include_invisible") == ["yes"]
            moved = [leader for leader in countries[scope]["leaders"] if leader[1] or include_hidden]
            countries[scope]["leaders"] = [leader for leader in countries[scope]["leaders"] if leader not in moved]
            countries[target]["leaders"].extend(moved)
        elif key == "annex_country" and isinstance(value, list):
            target = one(value, "target")
            if not countries[target]["exists"]:
                raise AssertionError(f"attempted to annex absent {target}")
            if children(value, "transfer_troops") == ["yes"]:
                countries[scope]["units"] += countries[target]["units"]
            countries[target]["units"] = 0
            # Conservatively require leaders to be moved before a tag disappears.
            # The engine may retain some after annexation; this is not an engine model.
            countries[target]["leaders"] = []
            countries[target]["exists"] = False


class MingInheritanceTests(unittest.TestCase):
    def test_gps_uprising_preserves_donor_armies_and_leaders(self):
        for event_id, expected_air in (("GPSevents.10", 7), ("GPSevents.11", 5)):
            options = children(event("events/GPS.txt", event_id), "option")
            self.assertEqual(len(options), 2)
            for option in options:
                with self.subTest(event=event_id, option=one(option, "name")):
                    transfers = [(path, value) for path, key, value in walk(option)
                                 if key == "transfer_units_fraction"]
                    self.assertEqual(len(transfers), 1)
                    path, effect = transfers[0]
                    self.assertIn("GPS", path)
                    self.assertEqual(one(effect, "target"), "SRC")
                    self.assertIn(("load_oob", "SRC_1937"), [(key, value) for _, key, value in walk(option)])
                    result = transfer_result(effect)
                    self.assertAlmostEqual(result.pop("stockpile"), 300)
                    self.assertEqual(result, {
                        "army": 40, "navy": 8, "air": expected_air,
                        "leaders": ["loyal_general", "loyal_admiral"],
                    })

    def test_ming_stockpile_transfers_keep_all_units_and_commanders(self):
        script = parse_file("events/mingcivwar.txt")
        transfers = [(path, value) for path, key, value in walk(script)
                     if key == "transfer_units_fraction"]
        self.assertEqual(len(transfers), 20)
        ratios = {"GPS": 0.15, "ROC": 0.15, "XBJ": 0.2, "GOS": 0.22,
                  "XIN": 0.11, "SIC": 0.15, "MOB": 0.07, "LSM": 0.10,
                  "MLJ": 0.10, "HWH": 0.10, "STG": 0.25}
        for path, effect in transfers:
            with self.subTest(target=one(effect, "target"), path=path):
                self.assertIn("MNG", path)
                result = transfer_result(effect)
                self.assertEqual((result["army"], result["navy"], result["air"]), (40, 8, 10))
                self.assertEqual(result["leaders"], ["loyal_general", "loyal_admiral"])
                self.assertAlmostEqual(result["stockpile"], 1000 * (1 - ratios[one(effect, "target")]))

    def test_src_start_presets_match_the_safe_civil_war_transfers(self):
        script = parse_file("common/scripted_effects/TOD_SRC_start_test.txt")
        for name, source, target, air, stockpile in (
            ("TOD_SRC_start_test_prepare", "MNG", "GPS", 10, 850),
            ("TOD_SRC_start_test_captured", "GPS", "SRC", 7, 300),
            ("TOD_SRC_start_test_blocked", "GPS", "SRC", 5, 300),
        ):
            with self.subTest(preset=name):
                transfers = [(path, value) for path, key, value in walk(one(script, name))
                             if key == "transfer_units_fraction"]
                self.assertEqual(len(transfers), 1)
                path, effect = transfers[0]
                self.assertIn(source, path)
                self.assertEqual(one(effect, "target"), target)
                self.assertEqual(children(effect, "army_ratio"), ["0"])
                self.assertEqual(children(effect, "navy_ratio"), ["0"])
                result = transfer_result(effect)
                self.assertAlmostEqual(result.pop("stockpile"), stockpile)
                self.assertEqual(result, {"army": 40, "navy": 8, "air": air,
                                          "leaders": ["loyal_general", "loyal_admiral"]})

    def test_each_fast_start_preset_releases_and_loads_src_once(self):
        if not (ROOT / "common/decisions/TOD_SRC_start_test.txt").is_file():
            self.skipTest("旧 SRC 快速开局决议入口已移除")
        effects = parse_file("common/scripted_effects/TOD_SRC_start_test.txt")
        category = one(parse_file("common/decisions/TOD_SRC_start_test.txt"),
                       "TOD_SRC_start_test_category")
        presets = [(name, block) for name, block in category if isinstance(block, list)]
        self.assertEqual(len(presets), 4)
        for name, decision in presets:
            with self.subTest(preset=name):
                available = one(decision, "available")
                self.assertIn(("NOT", [("country_exists", "SRC")]), available)
                self.assertIn(("NOT", [("country_exists", "GPS")]), available)
                calls = [key for _, key, value in walk(one(decision, "complete_effect"))
                         if isinstance(key, str) and key.startswith("TOD_SRC_start_test_")
                         and value == "yes"]
                self.assertEqual(calls.count("TOD_SRC_start_test_prepare"), 1)
                expanded = [entry for call in calls for entry in walk(one(effects, call))]
                self.assertEqual(sum(key == "MNG_release_SRC" for _, key, _ in expanded), 1)
                self.assertEqual(sum(key == "load_oob" and value == "SRC_1937"
                                     for _, key, value in expanded), 1)

    def test_xbj_split_retires_same_ming_duplicates_in_both_choices(self):
        a, b = children(event("events/mingcivwar.txt", "mingcivwar.78"), "option")
        retired = lambda block: {value for path, key, value in walk(block)
                                 if key == "retire_character" and "MNG" in path
                                 and value.startswith("MNG_4_")}
        self.assertEqual(len(retired(a)), 31)
        self.assertEqual(retired(a), retired(b))

    def test_roc_is_released_before_subjugation_and_equipment_transfer(self):
        option = children(event("events/mingcivwar.txt", "mingcivwar.77"), "option")[0]
        release = next(i for i, (key, _) in enumerate(option) if key == "MNG_release_ROC")
        transfer_guard = next(i for i, (key, value) in enumerate(option)
                              if key == "if" and any(k == "transfer_units_fraction" for _, k, _ in walk(value)))
        self.assertLess(release, transfer_guard)

    def test_roc_ai_choice_does_not_delete_ming_troops_if_release_fails(self):
        option = children(event("events/mingcivwar.txt", "mingcivwar.77"), "option")[0]
        all_deletions = [value for _, key, value in walk(option)
                         if key == "delete_unit_template_and_units"]
        guarded = [branch for key, branch in option if key == "if"
                   and ("country_exists", "ROC") in one(branch, "limit")]
        guarded_deletions = [value for branch in guarded for _, key, value in walk(branch)
                             if key == "delete_unit_template_and_units"]
        self.assertEqual(len(all_deletions), 5)
        self.assertEqual(guarded_deletions, all_deletions)

    def test_roc_player_choice_releases_before_switch_and_does_not_require_existing_tag(self):
        option = children(event("events/mingcivwar.txt", "mingcivwar.77"), "option")[1]
        trigger_entries = [entry for trigger in children(option, "trigger") for entry in trigger]
        self.assertNotIn(("country_exists", "ROC"), trigger_entries)
        release = next(i for i, (key, _) in enumerate(option) if key == "MNG_release_ROC")
        switches = [i for i, (key, value) in enumerate(option)
                    if key == "if" and ("country_exists", "ROC") in one(value, "limit")
                    and any(k == "change_tag_from" and v == "ROOT" and "ROC" in path
                            for path, k, v in walk(value))]
        self.assertEqual(len(switches), 1, "the player switch must be guarded after release")
        self.assertLess(release, switches[0])

    def test_roc_player_choice_tracks_every_state_that_release_will_core(self):
        option = children(event("events/mingcivwar.txt", "mingcivwar.77"), "option")[1]
        alternatives = one(one(option, "trigger"), "OR")
        self.assertIn(("country_exists", "ROC"), alternatives)
        owned = one(one(alternatives, "MNG"), "any_owned_state")
        conditions = one(owned, "OR")
        self.assertIn(("is_core_of", "ROC"), conditions)
        release = one(parse_file("common/scripted_effects/damingneizhanyong.txt"), "MNG_release_ROC")
        release_states = {value for path, key, value in walk(release)
                          if key == "add_state_core" and "ROC" in path}
        self.assertEqual(set(children(conditions, "state")), release_states)
        self.assertEqual(len(release_states), 17)

        # Check the real initial history rather than assuming that the release
        # effect's future core additions already exist when the option is shown.
        for state_id in release_states:
            history = list((ROOT / "history/states").glob(state_id + "-*"))
            self.assertEqual(len(history), 1, state_id)
        initial_state = parse_file("history/states/814-Minnan.txt")
        history = one(one(initial_state, "state"), "history")
        self.assertEqual(one(history, "owner"), "MNG")
        self.assertNotIn("ROC", children(history, "add_core_of"))

    def test_roc_player_choice_only_executes_effects_after_successful_release(self):
        option = children(event("events/mingcivwar.txt", "mingcivwar.77"), "option")[1]
        trigger = one(one(option, "trigger"), "OR")
        candidates = one(one(one(trigger, "MNG"), "any_owned_state"), "OR")
        release_states = set(children(candidates, "state"))
        release_index = next(i for i, (key, _) in enumerate(option) if key == "MNG_release_ROC")
        effects = option[release_index + 1:]
        self.assertEqual(len(effects), 1, "all following effects must share the existence guard")
        self.assertEqual(effects[0][0], "if")
        guarded = effects[0][1]
        self.assertEqual(one(guarded, "limit"), [("country_exists", "ROC")])
        effect_keys = [key for _, key, _ in walk(guarded)]
        for required in ("change_tag_from", "set_autonomy", "delete_unit_template_and_units",
                         "transfer_units_fraction", "load_oob", "transfer_state"):
            self.assertIn(required, effect_keys)

        def scenario(roc_exists, owned_states, existing_cores=(), *, force=False):
            """Model only visibility, release availability and the existence guard."""
            owned = set(owned_states)
            cores = set(existing_cores)
            visible = roc_exists or bool(owned & (release_states | cores))
            if not visible and not force:
                return visible, False, []
            after_release = roc_exists or bool(owned & (release_states | cores))
            return visible, after_release, effect_keys if after_release else []

        normal = scenario(False, {"814"})
        existing = scenario(True, set())
        no_release = scenario(False, set())
        expired = scenario(False, set(), force=True)
        self.assertTrue(normal[0] and normal[1] and "change_tag_from" in normal[2])
        self.assertTrue(existing[0] and existing[1] and "change_tag_from" in existing[2])
        self.assertEqual(no_release, (False, False, []))
        self.assertEqual(expired, (False, False, []))

    def test_fast_start_and_timed_event_retire_same_northeast_characters(self):
        helper_path = ROOT / "common/scripted_effects/TOD_ming_inheritance.txt"
        self.assertTrue(helper_path.exists(), "the shared Northeast roster is missing")
        helper_name = "TOD_MNG_retire_gps_characters"
        roster = one(parse_file(helper_path.relative_to(ROOT)), helper_name)
        expected = set("""
            MNG_1_yu_zhishan MNG_1_yang_yuting MNG_1_ma_zhanshan MNG_1_wu_junsheng
            MNG_1_zhang_zuoxiang MNG_1_wei_yisan MNG_1_meng_enyuan MNG_1_yu_zheng
            MNG_1_shan_duowen MNG_1_ying_detian MNG_1_sun_mingjiu MNG_1_shen_honglie
            MNG_1_chang_yinghuai MNG_1_xu_lanzhou MNG_1_yu_xuezhong MNG_1_wang_yizhe
            MNG_1_zhang_haipeng MNG_1_he_zhuguo MNG_1_wang_shuchang MNG_1_xing_shilian
            MNG_1_miao_jianqiu MNG_1_bao_wenyue MNG_1_zhou_zuohua MNG_1_wen_shude
            MNG_1_wan_fulin MNG_1_wu_yuanwu MNG_1_ying_zuoqian MNG_1_sun_liechen
        """.split())
        self.assertEqual(set(children(roster, "retire_character")), expected)
        normal = one(event("events/mingcivwar.txt", "mingcivwar.76"), "immediate")
        quick = one(parse_file("common/scripted_effects/TOD_SRC_start_test.txt"),
                    "TOD_SRC_start_test_prepare")
        self.assertEqual([(key, value) for _, key, value in walk(normal) if key == helper_name],
                         [(helper_name, "yes")])
        calls = [(path, value) for path, key, value in walk(quick) if key == helper_name]
        self.assertEqual(len(calls), 1)
        self.assertIn("MNG", calls[0][0])
        self.assertEqual(calls[0][1], "yes")

    def test_fast_start_blocks_replaying_timed_northeast_events(self):
        cases = ([("events/mingcivwar.txt", "mingcivwar.76")]
                 + [("events/GPS.txt", f"GPSevents.{i}") for i in range(6, 12)])
        for path, event_id in cases:
            with self.subTest(event=event_id):
                triggers = children(event(path, event_id), "trigger")
                self.assertEqual(len(triggers), 1)
                self.assertIn(("NOT", [("has_global_flag", "TOD_SRC_start_test_active")]), triggers[0])
                self.assertEqual([entry for entry in triggers[0] if entry[0] != "NOT"],
                                 [("tag", "GPS")] if event_id.startswith("GPS") else [])
                def allowed(active):
                    flags = {"TOD_SRC_start_test_active"} if active else set()
                    return not any(key == "NOT" and inner == [("has_global_flag", flag)] and flag in flags
                                   for key, inner in triggers[0]
                                   for flag in ("TOD_SRC_start_test_active",))
                self.assertTrue(allowed(False), "normal event must remain eligible")
                self.assertFalse(allowed(True), "fast start must suppress the replay")

    def test_sichuan_negotiations_transfer_existing_visible_and_hidden_generals(self):
        cases = (("1101", "SIC", "ROC"), ("1103", "ROC", "SIC"),
                 ("1107", "SIC", "SRC"), ("1109", "SRC", "SIC"),
                 ("1113", "SCG", "ROC"), ("1115", "ROC", "SCG"),
                 ("1119", "SCG", "SRC"), ("1121", "SRC", "SCG"))
        for number, winner, loser in cases:
            with self.subTest(event=number):
                state = initial_countries(winner, loser)
                option = one(event("events/mingcivwar.txt", "mingcivwar." + number), "option")
                run_peace_effect(option, state, winner)
                self.assertFalse(state[loser]["exists"])
                self.assertEqual(state[winner]["units"], 20)
                self.assertEqual({name for name, _ in state[winner]["leaders"]},
                                 {winner + "_visible", winner + "_hidden", loser + "_visible", loser + "_hidden"})

    def test_scg_decisions_preserve_troops_and_all_generals(self):
        for path, decision, winner in (("common/decisions/SRC.txt", "SRC_SCGkaizhan", "SRC"),
                                       ("common/decisions/ROC.txt", "ROC_decision_geming_SCG", "ROC")):
            with self.subTest(winner=winner):
                found = [value for _, key, value in walk(parse_file(path)) if key == decision]
                self.assertEqual(len(found), 1)
                state = initial_countries(winner, "SCG")
                run_peace_effect(one(found[0], "remove_effect"), state, winner)
                self.assertEqual(state[winner]["units"], 20)
                self.assertIn(("SCG_hidden", False), state[winner]["leaders"])

    def test_roc_src_peace_handles_optional_scg_without_losing_forces(self):
        option = one(event("events/hetan.txt", "ROC_SRC_hetan_event.22"), "option")
        for branch_key, winner, loser in (("if", "ROC", "SRC"), ("else_if", "SRC", "ROC")):
            branch = one(option, branch_key)
            for include_scg in (False, True):
                with self.subTest(winner=winner, scg=include_scg):
                    state = initial_countries(winner, loser, *(('SCG',) if include_scg else ()))
                    run_peace_effect(branch, state, winner)
                    self.assertFalse(state[loser]["exists"])
                    self.assertEqual(state[winner]["units"], 30 if include_scg else 20)
                    self.assertIn((loser + "_hidden", False), state[winner]["leaders"])
                    if include_scg:
                        self.assertFalse(state["SCG"]["exists"])
                        self.assertIn(("SCG_hidden", False), state[winner]["leaders"])

    def test_gos_xbj_peace_keeps_xbj_troops_and_hidden_generals(self):
        state = initial_countries("GOS", "XBJ")
        option = one(event("events/hetan.txt", "GOS_XBJ_hetan_event.8"), "option")
        run_peace_effect(option, state, "GOS")
        self.assertEqual(state["GOS"]["units"], 20)
        self.assertIn(("XBJ_hidden", False), state["GOS"]["leaders"])

    def test_unification_includes_invisible_generals_before_annexation(self):
        script = parse_file("common/decisions/MNG.txt")
        decision = [value for _, key, value in walk(script) if key == "MNG_chongjiandaming_decision"][0]
        transfers = [value for _, key, value in walk(decision) if key == "every_unit_leader"]
        self.assertEqual(len(transfers), 1)
        self.assertEqual(children(transfers[0], "include_invisible"), ["yes"])
        annex = [value for _, key, value in walk(decision) if key == "annex_country"]
        self.assertEqual(children(annex[0], "transfer_troops"), ["yes"])

    def test_src_leader_focus_does_not_skip_ungranted_roles(self):
        item = focus("SRC_promote_military_officers")
        self.assertFalse(children(item, "bypass"), "a bypass skips the only army-role reward")
        self.assertEqual(one(item, "available"), [])
        self.assertEqual(one(item, "prerequisite"), [("focus", "SRC_workers_pickets")])
        self.assertEqual(one(focus("SRC_workers_pickets"), "bypass"),
                         [("NOT", [("country_exists", "GPS")])])
        rewards = one(item, "completion_reward")
        self.assertTrue(any(k == "id" and v == "SRCevents.999" for _, k, v in walk(rewards)))
        navy = focus("SRC_yinrudatonghuihaijunrencai")
        self.assertTrue(any(k == "id" and v == "SRCevents.998" for _, k, v in walk(one(navy, "completion_reward"))))

    def test_src_navy_focus_transfers_only_from_character_owner(self):
        reward = one(focus("SRC_gaibianbeiyangjianduishiguan"), "completion_reward")
        gps_scope = one(reward, "GPS")
        for character in ("GPS_shen_honglie", "GPS_wen_shude", "GPS_shan_duowen"):
            scopes = [path for path, key, value in walk(reward)
                      if key == character and isinstance(value, list)
                      and ("set_nationality", "SRC") in value]
            self.assertEqual(len(scopes), 1, character)
            self.assertIn("GPS", scopes[0], character)
            guarded = [case for case in children(gps_scope, "if")
                       if ("has_character", character) in one(case, "limit")]
            self.assertEqual(len(guarded), 1, character)
            self.assertEqual(one(guarded[0], character), [("set_nationality", "SRC")])


if __name__ == "__main__":
    unittest.main()
