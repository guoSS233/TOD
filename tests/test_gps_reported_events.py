"""Regressions for restored GPS focus events and their consumed rewards."""
import re
import unittest
from pathlib import Path

from test_roc_allied_parties import read_script, one, named_event
from test_gps_governance_runtime import GPSState

RESTORED_EVENTS = (42, 43, 44, 45, 46, 47, *range(49, 60))


def focus_reward(focus_id):
    tree = one(read_script("common/national_focus/GPS.txt"), "focus_tree")
    return one(next(b for k, b in tree if k == "focus" and one(b, "id") == focus_id), "completion_reward")


def reserve_migration():
    actions = one(read_script("common/on_actions/GPS_on_actions.txt"), "on_actions")
    daily = one(one(actions, "on_daily"), "effect")
    scope = one(one(daily, "if"), "GPS")
    matches = [[(k, b)] for k, b in scope if k == "if" and
               ("has_completed_focus", "GPS_dongyuanyubeiyi") in one(b, "limit")]
    if len(matches) != 1:
        raise AssertionError("Expected one legacy reserve migration")
    return matches[0]

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


def event_blocks(text):
    # Tokenize strings/comments first so braces in them cannot end an event.
    tokens = list(re.finditer(r'"(?:\\.|[^"\\])*"|#[^\n]*|[{}]|[^\s{}"#]+', text))
    for index, token in enumerate(tokens):
        if token.group() != "country_event" or index + 2 >= len(tokens):
            continue
        if [t.group() for t in tokens[index + 1:index + 3]] != ["=", "{"]:
            continue
        depth = 1
        for end in tokens[index + 3:]:
            depth += (end.group() == "{") - (end.group() == "}")
            if depth == 0:
                yield text[token.start():end.end()]
                break
        else:
            raise AssertionError("Unclosed country_event block")


class ReportedGpsEvents(unittest.TestCase):
    def test_governance_political_power_checks_use_engine_supported_operators(self):
        # The native 2026-11-06 log rejected the first >= 25 in governance
        # event 1 and then lost the remaining event definitions. The local
        # Clausewitz test parser accepts >=, so definition checks miss this.
        for path in ("events/GPS.txt", "common/scripted_triggers/GPS_scripted_triggers.txt"):
            with self.subTest(path=path):
                script = re.sub(r'#[^\n]*', '', read(path))
                unsupported = re.findall(r'\bhas_political_power\s*(?:>=|<=|!=|==)\s*\S+', script)
                self.assertEqual(unsupported, [], "Native political-power checks support <, >, or =")

    def test_governance_demobilization_accepts_exact_cost_and_rejects_shortfall(self):
        event = named_event(read_script("events/GPS.txt"), "GPS_governance.45")
        for letter, cost in (("a", 20), ("b", 15), ("c", 10)):
            choice = next(value for key, value in event if key == "option"
                          and one(value, "name") == f"GPS_governance.45.{letter}")
            for pp, allowed in ((cost - .01, False), (cost, True), (cost + .01, True)):
                with self.subTest(option=letter, pp=pp):
                    state = GPSState()
                    state.pp = pp
                    state.effect("GPS_gov_start_demobilization")
                    self.assertEqual(state.events, ["GPS_governance.45"])
                    self.assertEqual(state.passes(one(choice, "trigger")), allowed)
                    state.option(45, letter, check=False)
                    self.assertAlmostEqual(state.pp, pp - cost if allowed else pp)
                    self.assertEqual("GPS_gov_demobilization_chosen" in state.flags, allowed)

    def test_governance_shared_fee_checks_keep_all_cost_boundaries(self):
        cases = (
            ("GPS_gov_receipts_cost_affordable", 20, {"GPS_gov_joint_pay_breach"}),
            ("GPS_gov_receipts_cost_affordable", 5, {
                "GPS_gov_joint_pay_receipt_a", "GPS_gov_defence_roster_receipt_a",
                "GPS_gov_joint_appointment_receipt_a"}),
            ("GPS_gov_receipts_cost_affordable", 10, set()),
            ("GPS_gov_contact_fee_affordable", 5, {"GPS_gov_tang_register_a"}),
            ("GPS_gov_contact_fee_affordable", 10, {"GPS_gov_tang_register_b"}),
            ("GPS_gov_contact_fee_affordable", 15, set()),
        )
        for trigger, cost, flags in cases:
            for pp, allowed in ((cost - .01, False), (cost, True), (cost + .01, True)):
                with self.subTest(trigger=trigger, cost=cost, pp=pp):
                    state = GPSState()
                    state.pp = pp
                    state.flags.update(flags)
                    self.assertEqual(state.passes([(trigger, "yes")]), allowed)

    def test_merged_governance_definitions_are_top_level_registered_and_calls_resolve(self):
        events = read_script("events/GPS.txt")
        namespaces = set()
        definitions = {}
        for key, value in events:
            if key == "add_namespace":
                namespaces.add(value)
            elif key == "country_event":
                event_id = one(value, "id")
                self.assertIn(event_id.rsplit(".", 1)[0], namespaces)
                self.assertNotIn(event_id, definitions)
                definitions[event_id] = value
        expected = {f"GPS_governance.{n}" for n in (*range(1, 14), *range(20, 31), *range(40, 60))}
        self.assertEqual({key for key in definitions if key.startswith("GPS_governance.")}, expected)

        def check_calls(entries):
            for key, value in entries:
                if not isinstance(value, list):
                    continue
                if key == "country_event" and not any(k == "title" for k, _ in value):
                    event_id = one(value, "id")
                    if event_id.startswith(("GPS_governance.", "GPSevents.")):
                        self.assertIn(event_id, definitions)
                check_calls(value)

        for path in ("events/GPS.txt", "common/national_focus/GPS.txt", "common/decisions/GPS.txt",
                     "common/scripted_effects/GPS_scripted_effects.txt", "common/on_actions/GPS_on_actions.txt"):
            with self.subTest(path=path):
                check_calls(read_script(path))

    def test_reported_focus_calls_have_unique_event_definitions(self):
        focus = read("common/national_focus/GPS.txt")
        blocks = list(event_blocks(read("events/GPS.txt")))
        for number in (45, 46):
            with self.subTest(event=number):
                self.assertRegex(focus, rf'country_event\s*=\s*{{\s*id\s*=\s*GPSevents\.{number}\b')
                matches = [b for b in blocks if re.search(rf'^\s*id\s*=\s*GPSevents\.{number}\s*$', b, re.M)]
                self.assertEqual(len(matches), 1, f"GPSevents.{number} needs exactly one definition")

    def test_reported_events_are_guarded_and_localized(self):
        events = read("events/GPS.txt")
        loc = read("localisation/simp_chinese/TOD_GPS_l_simp_chinese.yml")
        self.assertRegex(events, r'(?m)^add_namespace\s*=\s*GPSevents\s*$')
        for number in (45, 46):
            with self.subTest(event=number):
                blocks = [b for b in event_blocks(events) if re.search(rf'^\s*id\s*=\s*GPSevents\.{number}\s*$', b, re.M)]
                self.assertEqual(len(blocks), 1)
                block = blocks[0]
                self.assertRegex(block, r'is_triggered_only\s*=\s*yes\b')
                self.assertRegex(block, r'fire_only_once\s*=\s*yes\b')
                self.assertRegex(block, r'trigger\s*=\s*{\s*tag\s*=\s*GPS\s*}')
                for field, suffix in (("title", "t"), ("desc", "d"), ("name", "a")):
                    key = f"GPSevents.{number}.{suffix}"
                    self.assertRegex(block, rf'{field}\s*=\s*{re.escape(key)}\b')
                    self.assertEqual(len(re.findall(rf'^\s*{re.escape(key)}:0\s+".+"\s*$', loc, re.M)), 1)

    def test_all_focus_event_calls_and_historical_chain_resolve(self):
        events = read_script("events/GPS.txt")
        def check_calls(entries):
            for key, value in entries:
                if not isinstance(value, list):
                    continue
                if key == "country_event":
                    event_id = one(value, "id")
                    if event_id.startswith("GPSevents.") and not any(k == "title" for k, _ in value):
                        named_event(events, event_id)
                check_calls(value)
        check_calls(read_script("common/national_focus/GPS.txt"))
        check_calls(events)
        self.assertEqual(one(one(named_event(events, "GPSevents.42"), "option"), "country_event"), [("id", "GPSevents.43")])
        self.assertEqual(one(one(named_event(events, "GPSevents.43"), "option"), "country_event"), [("id", "GPSevents.44"), ("days", "40")])

    def test_restored_events_keep_existing_rewards_in_focuses(self):
        events = read_script("events/GPS.txt")
        loc = read("localisation/simp_chinese/TOD_GPS_l_simp_chinese.yml")
        for number in RESTORED_EVENTS:
            with self.subTest(event=number):
                event = named_event(events, f"GPSevents.{number}")
                self.assertEqual(one(event, "fire_only_once"), "yes")
                self.assertEqual(one(event, "is_triggered_only"), "yes")
                self.assertEqual(one(event, "trigger"), [("tag", "GPS")])
                keys = [one(event, "title"), one(event, "desc")]
                for _, option in [(k, v) for k, v in event if k == "option"]:
                    keys.append(one(option, "name"))
                    allowed = {"name", "country_event"} if number < 57 else {"name", "trigger", "set_country_flag", "XBJ", "STG", "unlock_decision_category_tooltip"}
                    self.assertTrue(all(k in allowed for k, _ in option), "The event must not repeat numerical focus rewards")
                for key in set(keys):
                    self.assertEqual(len(re.findall(rf'^\s*{re.escape(key)}:0\s+".+"\s*$', loc, re.M)), 1)

    def test_faction_meetings_set_only_the_matching_historical_flag(self):
        for focus, number, flag in (("GPS_huijianwubeixi", 57, "GPS_huijianwubeixi"), ("GPS_mihuijiaotongxi", 58, "GPS_huijianjiaotongxi")):
            with self.subTest(focus=focus):
                state = GPSState()
                state.run([(k, v) for k, v in focus_reward(focus) if k == "country_event"])
                self.assertEqual(state.events, [f"GPSevents.{number}"])
                state.run([(k, v) for k, v in one(named_event(read_script("events/GPS.txt"), f"GPSevents.{number}"), "option") if k != "name"])
                self.assertIn(flag, state.flags)
        self.assertFalse(any(k == "country_event" for k, _ in focus_reward("GPS_baozhangguoqiliyi")))

    def test_historical_alignment_choices_require_the_matching_surviving_country(self):
        event = named_event(read_script("events/GPS.txt"), "GPSevents.59")
        choices = [v for k, v in event if k == "option"]
        self.assertEqual(len(choices), 3)
        for index, (tag, other, flag) in enumerate((("XBJ", "STG", "GPS_huijianjiaotongxi"), ("STG", "XBJ", "GPS_huijianwubeixi"))):
            choice = choices[index]
            state = GPSState()
            state.flags.add(flag)
            for alive, rival, expected in ((True, False, True), (False, False, False), (True, True, False)):
                state.foreign = {tag: {"exists": alive}, other: {"exists": rival}}
                self.assertEqual(state.passes(one(choice, "trigger")), expected)
            state.flags.clear()
            state.foreign = {tag: {"exists": True}, other: {"exists": False}}
            self.assertFalse(state.passes(one(choice, "trigger")))
            # The surviving foreign country subordinates GPS, then takes over the
            # player from event ROOT; neither command may run in GPS scope.
            self.assertEqual(one(choice, tag), [("set_autonomy", [("target", "GPS"), ("autonomy_state", "autonomy_integrated_puppet")]), ("change_tag_from", "ROOT")])
        self.assertEqual(one(choices[2], "set_country_flag"), "GPS_xuanzhan")

    def test_reserve_reward_reaches_the_dynamic_modifier_and_preserves_other_values(self):
        state = GPSState()
        state.vars.update(GPS_fengzhaojiaofei=.07, GPS_fengzhaojiaofei_fangyu=.3)
        state.run(focus_reward("GPS_dongyuanyubeiyi"))
        variable = one(one(read_script("common/dynamic_modifiers/TOD_GPS_modifiers.txt"), "GPS_fengzhaojiaofei"), "conscription_factor")
        self.assertAlmostEqual(state.vars[variable], .27)
        self.assertEqual(state.vars["GPS_fengzhaojiaofei_fangyu"], .3)
        self.assertEqual(state.war_support, .4)
        self.assertNotIn("conscription_factor", state.vars)
        self.assertIn("奉诏剿匪", next(line for line in read("localisation/simp_chinese/TOD_GPS_l_simp_chinese.yml").splitlines() if line.startswith("GPS_dongyuanyubeiyi_xiaoguo:")))

    def test_old_reserve_value_migrates_once_and_new_focus_is_not_granted_twice(self):
        migration = reserve_migration()
        for legacy, completed, expected in ((.2, True, .27), (0, True, .07), (.2, False, .07)):
            with self.subTest(legacy=legacy, completed=completed):
                state = GPSState()
                state.vars.update(conscription_factor=legacy, GPS_fengzhaojiaofei=.07, GPS_fengzhaojiaofei_fangyu=.3)
                if completed:
                    state.focuses.add("GPS_dongyuanyubeiyi")
                state.run(migration)
                state.run(migration)
                self.assertAlmostEqual(state.vars["GPS_fengzhaojiaofei"], expected)
                self.assertEqual(state.vars["conscription_factor"], 0 if completed else legacy)
                self.assertEqual(state.vars["GPS_fengzhaojiaofei_fangyu"], .3)
        state = GPSState()
        state.run(focus_reward("GPS_dongyuanyubeiyi"))
        state.focuses.add("GPS_dongyuanyubeiyi")
        state.run(migration)
        state.run(migration)
        self.assertAlmostEqual(state.vars["GPS_fengzhaojiaofei"], .2)

    def test_factory_tooltip_describes_existing_dynamic_modifier_reward(self):
        loc = read("localisation/simp_chinese/TOD_GPS_l_simp_chinese.yml")
        key = "GPS_minyonggongchangjunyonghua_xiaoguo"
        values = re.findall(rf'^\s*{key}:0\s+"(.*)"\s*$', loc, re.M)
        self.assertEqual(len(values), 1, "The focus tooltip must resolve to Chinese text")
        self.assertIn("工厂产出: §G+10.0%§!", values[0])
        modifiers = read("common/dynamic_modifiers/TOD_GPS_modifiers.txt")
        self.assertRegex(modifiers, r'industrial_capacity_factory\s*=\s*GPS_fengyupiaodang_chanchu\b')


if __name__ == "__main__":
    unittest.main()
