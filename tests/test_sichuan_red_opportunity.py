"""Static contract checks for the Sichuan red-opportunity scripts.

These checks inspect and narrowly interpret the production Clausewitz files.
They do not run the HOI4 engine and cannot verify engine-side command semantics.
"""

from pathlib import Path
import re
import unittest
from typing import NamedTuple


ROOT = Path(__file__).resolve().parents[1]
CORE_FILES = (
    Path("common/on_actions/SIC_red_opportunity.txt"),
    Path("common/scripted_triggers/SIC_red_opportunity.txt"),
    Path("common/scripted_effects/SIC_scripted_effects.txt"),
    Path("common/decisions/SIC.txt"),
    Path("common/decisions/categories/SIC.txt"),
    Path("events/SIC_red_opportunity.txt"),
)
CONNECTED_FILES = (
    Path("common/decisions/SIC.txt"),
    Path("common/scripted_effects/SIC_scripted_effects.txt"),
    Path("events/SiChuan.txt"),
)
LOCALIZATION_FILE = Path(
    "localisation/simp_chinese/TOD_SIC_l_simp_chinese.yml"
)
REQUIRED_LOCALIZATION_KEYS = {
    "SIC_red_opportunity_category",
    "SIC_red_opportunity_category_desc",
    "SIC_red_relief",
    "SIC_red_relief_desc",
    "SIC_red_negotiate",
    "SIC_red_negotiate_desc",
    "SIC_red_raids",
    "SIC_red_raids_desc",
    "SIC_red_opportunity_conditions_tt",
    "SIC_red_relief_tt",
    "SIC_red_negotiate_tt",
    "SIC_red_raids_tt",
    "SIC_red_raids_cp_cost",
    "SIC_red_raids_cp_cost_blocked",
    "SIC_red_raids_cp_cost_tooltip",
    "TODSICRED.1.t",
    "TODSICRED.1.d",
    "TODSICRED.1.a",
}


def parse_localization(data: bytes) -> tuple[dict[str, str], list[str]]:
    """Read the simple key:0 "value" entries used by this localization file."""
    text = data.decode("utf-8-sig")
    entries: dict[str, str] = {}
    duplicates: list[str] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "l_simp_chinese:":
            continue
        match = re.fullmatch(r'([\w.\-]+):\d*\s*"(.*)"', stripped)
        if not match:
            raise ValueError(f"unsupported localization syntax at line {line_number}: {line}")
        key, value = match.groups()
        if key in entries:
            duplicates.append(key)
        entries[key] = value
    return entries, duplicates


class Comparison(NamedTuple):
    operator: str
    value: str


def parse_clausewitz(text: str, source: str) -> list[tuple[str, object]]:
    """Parse only the assignment/group/comparison syntax used by these files."""
    tokens: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char == "#":
            newline = text.find("\n", index)
            index = len(text) if newline < 0 else newline + 1
            continue
        if char == '"':
            index += 1
            value: list[str] = []
            while index < len(text) and text[index] != '"':
                if text[index] == "\\":
                    index += 1
                    if index == len(text):
                        raise ValueError(f"unterminated escape in {source}")
                value.append(text[index])
                index += 1
            if index == len(text):
                raise ValueError(f"unterminated quote in {source}")
            index += 1
            tokens.append("".join(value))
            continue
        if char in "{}=":
            tokens.append(char)
            index += 1
            continue
        if char in "<>!":
            operator = char
            index += 1
            if index < len(text) and text[index] == "=":
                operator += "="
                index += 1
            tokens.append(operator)
            continue
        start = index
        while index < len(text) and not text[index].isspace() and text[index] not in '{}=#"<>!':
            index += 1
        if start == index:
            raise ValueError(f"unsupported token {text[index]!r} in {source}")
        tokens.append(text[start:index])

    operators = {"<", ">", "<=", ">=", "!=", "=="}

    def parse_group(position: int, requires_close: bool) -> tuple[list[tuple[str, object]], int]:
        pairs: list[tuple[str, object]] = []
        while position < len(tokens):
            if tokens[position] == "}":
                if not requires_close:
                    raise ValueError(f"unexpected closing brace in {source}")
                return pairs, position + 1
            key = tokens[position]
            if key in ("{", "=", *operators):
                raise ValueError(f"unsupported syntax near {key!r} in {source}")
            position += 1
            if position >= len(tokens):
                raise ValueError(f"missing value for {key!r} in {source}")
            if tokens[position] == "=":
                position += 1
                if position >= len(tokens):
                    raise ValueError(f"missing value for {key!r} in {source}")
                if tokens[position] == "{":
                    value, position = parse_group(position + 1, True)
                else:
                    value = tokens[position]
                    position += 1
            elif tokens[position] in operators:
                operator = tokens[position]
                position += 1
                if position >= len(tokens) or tokens[position] in "{}=":
                    raise ValueError(f"missing comparison value for {key!r} in {source}")
                value = Comparison(operator, tokens[position])
                position += 1
            else:
                raise ValueError(f"unsupported syntax after {key!r} in {source}")
            pairs.append((key, value))
        if requires_close:
            raise ValueError(f"unclosed brace in {source}")
        return pairs, position

    result, end = parse_group(0, False)
    if end != len(tokens):
        raise ValueError(f"unparsed tokens in {source}")
    return result


def one_block(entries: list[tuple[str, object]], key: str) -> list[tuple[str, object]]:
    values = [value for name, value in entries if name == key]
    if len(values) != 1 or not isinstance(values[0], list):
        raise ValueError(f"expected one block named {key}")
    return values[0]


def descendant_entries(entries: list[tuple[str, object]]):
    for key, value in entries:
        yield key, value
        if isinstance(value, list):
            yield from descendant_entries(value)


def _compare(actual: float, comparison: Comparison) -> bool:
    expected = float(comparison.value)
    return {
        "<": actual < expected,
        "<=": actual <= expected,
        ">": actual > expected,
        ">=": actual >= expected,
        "==": actual == expected,
        "!=": actual != expected,
    }[comparison.operator]


def evaluate_trigger(
    entries: list[tuple[str, object]],
    state: dict[str, object],
    trigger_defs: dict[str, list[tuple[str, object]]],
) -> bool:
    """Evaluate only the production trigger operators used by this feature."""
    for key, value in entries:
        if key == "NOT":
            if not isinstance(value, list) or evaluate_trigger(value, state, trigger_defs):
                return False
        elif key == "OR":
            if not isinstance(value, list) or not any(
                evaluate_trigger([branch], state, trigger_defs) for branch in value
            ):
                return False
        elif key == "AND":
            if not isinstance(value, list) or not evaluate_trigger(value, state, trigger_defs):
                return False
        elif key in trigger_defs:
            if value != "yes" or not evaluate_trigger(trigger_defs[key], state, trigger_defs):
                return False
        elif key == "check_variable":
            if not isinstance(value, list) or len(value) != 1:
                raise ValueError("unsupported check_variable structure")
            variable, comparison = value[0]
            if not isinstance(comparison, Comparison):
                raise ValueError("unsupported check_variable comparison")
            variables = state["variables"]
            if not isinstance(variables, dict) or not _compare(float(variables.get(variable, 0)), comparison):
                return False
        elif key == "tag":
            if value != state["tag"]:
                return False
        elif key == "country_exists":
            if value not in state["countries"]:
                return False
        elif key == "has_country_flag":
            if value not in state["flags"]:
                return False
        elif key == "has_war":
            if (value == "yes") != bool(state["at_war"]):
                return False
        elif key == "has_war_with":
            if value not in state.get("war_targets", set()):
                return False
        elif key == "always":
            if value != "yes":
                return False
        elif key == "has_stability":
            if not isinstance(value, Comparison) or not _compare(float(state["stability"]), value):
                return False
        elif key == "has_idea":
            if value not in state["ideas"]:
                return False
        elif key in ("owns_state", "controls_state"):
            field = "owns_831" if key == "owns_state" else "controls_831"
            if value != "831" or not bool(state[field]):
                return False
        else:
            raise ValueError(f"unsupported production trigger: {key}")
    return True


def red_opportunity_state(unrest: float = 60, organization: float = 60) -> dict[str, object]:
    return {
        "tag": "SIC",
        "countries": set(),
        "flags": set(),
        "variables": {"SIC.minzhong": unrest, "SIC_red_organization": organization},
        "at_war": False,
        "stability": 0.34,
        "ideas": set(),
        "owns_831": True,
        "controls_831": True,
    }


def script_definitions(path: Path) -> dict[str, list[tuple[str, object]]]:
    entries = parse_clausewitz((ROOT / path).read_text(encoding="utf-8-sig"), path.as_posix())
    definitions: dict[str, list[tuple[str, object]]] = {}
    for name, value in entries:
        if not isinstance(value, list):
            raise ValueError(f"unexpected non-block definition: {name}")
        if name in definitions:
            if path == Path("common/decisions/SIC.txt") and name == "SIC_chuanneijushi_categories":
                definitions[name].extend(value)
            else:
                raise ValueError(f"unexpected duplicate definition: {name}")
        else:
            definitions[name] = value
    return definitions


class SichuanRedOpportunityContractTests(unittest.TestCase):
    def test_production_scripts_parse_and_preserve_existing_uprising_event(self) -> None:
        missing = [path.as_posix() for path in CORE_FILES if not (ROOT / path).is_file()]
        self.assertEqual(missing, [], f"missing production scripts: {missing}")
        trees = {
            path: parse_clausewitz(
                (ROOT / path).read_text(encoding="utf-8-sig"), path.as_posix()
            )
            for path in (*CORE_FILES, *CONNECTED_FILES)
        }

        localization, _ = parse_localization((ROOT / LOCALIZATION_FILE).read_bytes())
        references = set()
        decisions = [(name, value) for key, block in trees[Path("common/decisions/SIC.txt")] if key == "SIC_chuanneijushi_categories" for name, value in block if name.startswith("SIC_red_")]
        for decision, value in decisions:
            if isinstance(value, list):
                references.update((decision, f"{decision}_desc"))
        category_file = trees[Path("common/decisions/categories/SIC.txt")]
        for category, value in category_file:
            if isinstance(value, list) and category == "SIC_red_opportunity_category":
                references.update((category, f"{category}_desc"))
        text_fields = {"title", "desc", "name", "custom_effect_tooltip", "custom_cost_text"}
        for path in CORE_FILES:
            for key, value in descendant_entries(trees[path]):
                if key in text_fields and isinstance(value, str) and value.startswith(("SIC_red", "TODSICRED.")):
                    references.add(value)
        self.assertLessEqual(references, localization.keys())

        warning_id_count = sum(
            len(re.findall(r"\bid\s*=\s*TODSICRED\.1\b", path.read_text(encoding="utf-8-sig")))
            for path in (ROOT / "events").rglob("*.txt")
        )
        self.assertEqual(warning_id_count, 1)

        legacy_tree = trees[Path("events/SiChuan.txt")]
        legacy_events = [
            value for key, value in legacy_tree
            if key == "country_event" and isinstance(value, list)
            and any(name == "id" and item == "TODSIC.1001" for name, item in value)
        ]
        self.assertEqual(len(legacy_events), 1)
        legacy_event = legacy_events[0]
        guarded_war = one_block(one_block(legacy_event, "immediate"), "if")
        war_limit = one_block(guarded_war, "limit")
        self.assertIn(("tag", "SIC"), war_limit)
        self.assertIn(("country_exists", "SCG"), war_limit)
        self.assertIn(("has_country_flag", "SIC_red_uprising_started"), war_limit)
        self.assertEqual(one_block(war_limit, "NOT"), [("has_war_with", "SCG")])
        war = one_block(guarded_war, "declare_war_on")
        self.assertEqual(dict(war).get("target"), "SCG")
        switch_options = [
            value for key, value in legacy_event if key == "option" and isinstance(value, list)
            and any(name == "name" and item == "TODSIC.1001.a" for name, item in value)
        ]
        self.assertEqual(len(switch_options), 1)
        self.assertEqual(dict(one_block(switch_options[0], "SCG")).get("change_tag_from"), "ROOT")

    def test_simplified_chinese_localization_has_bom_unique_keys_and_contract_entries(self) -> None:
        path = ROOT / LOCALIZATION_FILE
        self.assertTrue(path.is_file(), f"missing localization: {LOCALIZATION_FILE}")
        data = path.read_bytes()
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"), "localization must be UTF-8 with BOM")
        entries, duplicates = parse_localization(data)
        red_duplicates = [key for key in duplicates if key.startswith(("SIC_red", "TODSICRED."))]
        self.assertEqual(red_duplicates, [], f"duplicate red-opportunity localization keys: {red_duplicates}")
        self.assertTrue(
            REQUIRED_LOCALIZATION_KEYS.issubset(entries),
            f"missing localization keys: {sorted(REQUIRED_LOCALIZATION_KEYS - entries.keys())}",
        )
        self.assertTrue(all(entries[key].strip() for key in REQUIRED_LOCALIZATION_KEYS))

    def test_player_text_shows_current_values_and_uses_plain_place_names(self) -> None:
        entries, _ = parse_localization((ROOT / LOCALIZATION_FILE).read_bytes())
        gui_entries, _ = parse_localization((ROOT / "localisation/simp_chinese/TOD_SIC_l_simp_chinese.yml").read_bytes())
        self.assertIn("[?SIC.minzhong|0]", gui_entries["SIC_provincial_gui_unrest"])
        self.assertIn("[?SIC.gongye|0]", gui_entries["SIC_provincial_gui_industry"])
        self.assertIn("[?SIC_red_organization|0]", gui_entries["SIC_provincial_gui_organization"])
        category = entries["SIC_red_monthly_rules_tt"] + entries["SIC_red_opportunity_conditions_tt"]
        for fact in ("80", "12", "60", "79", "8", "40", "6", "0", "100", "川中", "四川革命政府"):
            self.assertIn(fact, category)

        player_text = " ".join(entries[key] for key in REQUIRED_LOCALIZATION_KEYS)
        player_text = re.sub(r"\[\?[^\]]+\]", "", player_text)
        for internal_id in ("SCG", "SIC_red_", "TODSICRED", "831"):
            self.assertNotIn(internal_id, player_text)

    def test_decision_text_explains_cost_effect_and_cooldown(self) -> None:
        entries, _ = parse_localization((ROOT / LOCALIZATION_FILE).read_bytes())
        self.assertIn("35", entries["SIC_red_relief_tt"])
        self.assertIn("5", entries["SIC_red_relief_tt"])
        self.assertIn("10", entries["SIC_red_relief_tt"])
        self.assertIn("30", entries["SIC_red_relief_tt"])
        self.assertIn("40", entries["SIC_red_negotiate_tt"])
        self.assertIn("12", entries["SIC_red_negotiate_tt"])
        self.assertIn("5", entries["SIC_red_negotiate_tt"])
        self.assertIn("30", entries["SIC_red_negotiate_tt"])
        self.assertIn("25", entries["SIC_red_raids_tt"])
        self.assertIn("10", entries["SIC_red_raids_tt"])
        self.assertIn("20", entries["SIC_red_raids_tt"])
        self.assertIn("8", entries["SIC_red_raids_tt"])
        self.assertIn("30", entries["SIC_red_raids_tt"])

    def test_uprising_eligibility_uses_production_triggers_for_fourteen_cases(self) -> None:
        triggers = script_definitions(Path("common/scripted_triggers/SIC_red_opportunity.txt"))
        window = triggers["SIC_red_window_open_trigger"]
        stability_conditions = [
            (key, value)
            for key, value in descendant_entries(window)
            if key in ("has_stability", "stability")
        ]
        self.assertEqual(stability_conditions, [("has_stability", Comparison("<", "0.35"))])

        eligible = triggers["SIC_red_uprising_eligible_trigger"]
        cases = [
            ("unrest below 60", {"unrest": 59}, False),
            ("organization below 60", {"organization": 59}, False),
            ("34.99 percent stability", {"stability": 0.3499}, True),
            ("35 percent stability", {"stability": 0.35}, False),
            ("war opens window", {"stability": 0.9, "at_war": True}, True),
            ("military disorder opens window", {"stability": 0.9, "disorder": True}, True),
            ("no action window", {"stability": 0.5}, False),
            ("unrest exactly 100", {"unrest": 100}, True),
            ("unrest above 100", {"unrest": 101}, True),
            ("revolutionary government exists", {"scg_exists": True}, False),
            ("state no longer owned", {"owns_831": False}, False),
            ("state no longer controlled", {"controls_831": False}, False),
            ("uprising already started", {"uprising_started": True}, False),
            ("scope is not Sichuan", {"tag": "SCG"}, False),
        ]
        self.assertEqual(len(cases), 14)
        for name, changes, expected in cases:
            state = red_opportunity_state(
                changes.get("unrest", 60), changes.get("organization", 60)
            )
            state["stability"] = changes.get("stability", 0.3499)
            state["at_war"] = changes.get("at_war", False)
            state["tag"] = changes.get("tag", "SIC")
            if changes.get("disorder"):
                state["ideas"].add("SIC_hunluandejundui")
            if changes.get("scg_exists"):
                state["countries"].add("SCG")
            if not changes.get("owns_831", True):
                state["owns_831"] = False
            if not changes.get("controls_831", True):
                state["controls_831"] = False
            if changes.get("uprising_started"):
                state["flags"].add("SIC_red_uprising_started")
            with self.subTest(name=name):
                actual = evaluate_trigger(eligible, state, triggers)
                self.assertEqual(actual, expected)

    def test_monthly_country_hook_and_missing_variable_initialization(self) -> None:
        hooks = script_definitions(Path("common/on_actions/SIC_red_opportunity.txt"))["on_actions"]
        monthly = one_block(hooks, "on_monthly_SIC")
        self.assertEqual(one_block(monthly, "effect"), [("SIC_red_monthly_effect", "yes")])
        effects = script_definitions(Path("common/scripted_effects/SIC_scripted_effects.txt"))
        initialize = one_block(effects["SIC_red_initialize_effect"], "if")
        self.assertEqual(
            one_block(one_block(initialize, "limit"), "NOT"),
            [("has_variable", "SIC_red_organization")],
        )
        self.assertEqual(one_block(initialize, "set_variable"), [("SIC_red_organization", "0")])

    def test_monthly_growth_clamp_and_one_time_warning_structure(self) -> None:
        effects = script_definitions(Path("common/scripted_effects/SIC_scripted_effects.txt"))
        monthly = one_block(effects["SIC_red_monthly_effect"], "if")
        self.assertEqual(one_block(monthly, "limit"), [("SIC_red_pre_uprising_trigger", "yes")])
        growth = [value for key, value in monthly if key in ("if", "else_if")][:3]
        self.assertEqual(len(growth), 3)
        for branch, threshold, delta in zip(growth, ("80", "60", "40"), ("12", "8", "-6")):
            limit = one_block(branch, "limit")
            if threshold != "40":
                limit = one_block(limit, "NOT")
            self.assertEqual(one_block(limit, "check_variable"), [("SIC.minzhong", Comparison("<", threshold))])
            self.assertEqual(one_block(branch, "add_to_variable"), [("SIC_red_organization", delta)])
        self.assertEqual(
            one_block(effects["SIC_red_clamp_organization_effect"], "clamp_variable"),
            [("var", "SIC_red_organization"), ("min", "0"), ("max", "100")],
        )
        warning = [value for key, value in monthly if key == "if"][1]
        limit = one_block(warning, "limit")
        self.assertEqual(
            limit,
            [("NOT", [("check_variable", [("SIC_red_organization", Comparison("<", "24"))])]),
             ("NOT", [("has_country_flag", "SIC_red_warning_sent")])],
        )
        self.assertLess(warning.index(("set_country_flag", "SIC_red_warning_sent")),
                        next(i for i, (key, _) in enumerate(warning) if key == "country_event"))
        self.assertEqual(one_block(warning, "country_event"), [("id", "TODSICRED.1")])
        self.assertLess(monthly.index(("SIC_red_clamp_organization_effect", "yes")),
                        monthly.index(("if", warning)))
        self.assertEqual(monthly[-1], ("SIC_red_try_uprising_effect", "yes"))

    def test_executor_uses_eligibility_guard_before_transfer_and_oob(self) -> None:
        effects = script_definitions(Path("common/scripted_effects/SIC_scripted_effects.txt"))
        execute = one_block(effects["SIC_red_try_uprising_effect"], "if")
        self.assertEqual(one_block(execute, "limit"), [("SIC_red_uprising_eligible_trigger", "yes")])
        self.assertLess(execute.index(("set_country_flag", "SIC_red_uprising_started")),
                        next(i for i, (key, _) in enumerate(execute) if key == "SCG"))
        self.assertEqual(one_block(execute, "SCG"),
                         [("transfer_state", "831"), ("add_state_core", "831"), ("load_oob", "SCG_1937")])
        self.assertEqual(one_block(execute, "country_event"), [("id", "TODSIC.1001")])
        legacy = (ROOT / "common/decisions/SIC.txt").read_text(encoding="utf-8-sig")
        self.assertNotIn("TODSIC.1001", legacy)

    def test_actual_decision_costs_cooldowns_and_refresh(self) -> None:
        decisions = script_definitions(Path("common/decisions/SIC.txt"))["SIC_chuanneijushi_categories"]
        expected = {
            "SIC_red_relief": ("35", [("SIC.gongye", "-5"), ("SIC.minzhong", "-10")]),
            "SIC_red_negotiate": ("40", [("SIC_red_organization", "-12"), ("SIC.minzhong", "-5")]),
            "SIC_red_raids": ("25", [("SIC_red_organization", "-20"), ("SIC.minzhong", "8")]),
        }
        for name, (cost, changes) in expected.items():
            with self.subTest(decision=name):
                decision = one_block(decisions, name)
                self.assertEqual(dict(decision)["cost"], cost)
                self.assertEqual(dict(decision)["days_re_enable"], "30")
                self.assertGreater(float(dict(one_block(decision, "ai_will_do"))["base"]), 0)
                hidden = one_block(one_block(decision, "complete_effect"), "hidden_effect")
                self.assertEqual([one_block([entry], "add_to_variable")[0] for entry in hidden if entry[0] == "add_to_variable"], changes)
                self.assertEqual(hidden[-1], ("SIC_red_refresh_governance_effect", "yes"))
        raids = one_block(decisions, "SIC_red_raids")
        self.assertEqual(one_block(one_block(raids, "custom_cost_trigger"), "NOT"), [("command_power", Comparison("<", "10"))])
        self.assertIn(("add_command_power", "-10"), one_block(one_block(raids, "complete_effect"), "hidden_effect"))

    def test_trigger_interpreter_rejects_unknown_production_syntax(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported production trigger"):
            evaluate_trigger(
                [("unrecognized_trigger", "yes")], red_opportunity_state(), {}
            )


if __name__ == "__main__":
    unittest.main()
