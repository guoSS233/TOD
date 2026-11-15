"""Static contract checks for the ROC postwar national focus tree."""

from collections import defaultdict
from pathlib import Path
import csv
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAYOUT_PATH = ROOT / "docs/design/ROC_postwar_focus_layout.csv"
FOCUS_PATH = ROOT / "common/national_focus/ROC_postwar.txt"
IDEA_PATH = ROOT / "common/ideas/ROC_postwar.txt"
LOCALISATION_PATH = ROOT / "localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml"
PARTIES = ("progressives", "constitutionalists", "liberals", "datong")
ENDINGS = {
    "progressives": "heavenly_order",
    "constitutionalists": "wise_ruler",
    "liberals": "gentlemen",
    "datong": "commonwealth",
}
REAL_EFFECT = re.compile(
    r"\b(?:add_political_power|add_stability|add_war_support|add_army_experience|"
    r"add_navy_experience|add_air_experience|add_tech_bonus|add_timed_idea|"
    r"add_ideas|add_building_construction)\s*="
)


def read_layout():
    with LAYOUT_PATH.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def scope_end(source, open_brace):
    depth = 0
    quoted = False
    escaped = False
    comment = False
    for index in range(open_brace, len(source)):
        char = source[index]
        if comment:
            if char == "\n":
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == "#":
            comment = True
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    raise AssertionError("unclosed Clausewitz scope")


def named_scopes(source, name):
    scopes = []
    pattern = re.compile(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{")
    for match in pattern.finditer(source):
        brace = source.find("{", match.start(), match.end())
        end = scope_end(source, brace)
        scopes.append(source[brace + 1 : end - 1])
    return scopes


def one_scope(source, name):
    scopes = named_scopes(source, name)
    if len(scopes) != 1:
        raise AssertionError(f"expected one {name} scope, found {len(scopes)}")
    return scopes[0]


def focus_blocks(source):
    pattern = re.compile(r"(?m)^\s*focus\s*=\s*\{")
    result = []
    for match in pattern.finditer(source):
        brace = source.find("{", match.start(), match.end())
        end = scope_end(source, brace)
        result.append(source[brace + 1 : end - 1])
    return result


def scalar(block, key):
    matches = re.findall(rf"(?m)^\s*{re.escape(key)}\s*=\s*([^\s#]+)", block)
    if len(matches) != 1:
        raise AssertionError(f"expected one {key}, found {len(matches)}")
    return matches[0]


def prerequisite_blocks(block):
    return [
        re.findall(r"\bfocus\s*=\s*(ROC_pw_[A-Za-z0-9_]+)", item)
        for item in named_scopes(block, "prerequisite")
    ]


def ids_in_scope(block, key):
    return re.findall(r"\bfocus\s*=\s*(ROC_pw_[A-Za-z0-9_]+)", one_scope(block, key))


class RocPostwarTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read_layout()
        cls.by_key = {row["key"]: row for row in cls.rows}
        cls.focus_source = FOCUS_PATH.read_text(encoding="utf-8-sig") if FOCUS_PATH.exists() else ""
        tree_scopes = named_scopes(cls.focus_source, "focus_tree")
        cls.tree = tree_scopes[0] if len(tree_scopes) == 1 else ""
        cls.blocks = [block for block in focus_blocks(cls.tree)
                      if not scalar(block, "id").startswith("ROC_pw_ce_")]
        cls.by_id = {
            scalar(block, "id"): block
            for block in cls.blocks
            if re.search(r"(?m)^\s*id\s*=", block)
        }
        cls.ideas = IDEA_PATH.read_text(encoding="utf-8-sig") if IDEA_PATH.exists() else ""
        cls.localisation_bytes = LOCALISATION_PATH.read_bytes() if LOCALISATION_PATH.exists() else b""
        cls.localisation = cls.localisation_bytes.decode("utf-8-sig")

    def test_layout_has_59_unique_nodes_and_is_a_dag(self):
        self.assertEqual(59, len(self.rows))
        self.assertEqual(59, len(self.by_key))
        positions = [(row["x"], row["y"]) for row in self.rows]
        self.assertEqual(len(positions), len(set(positions)), "two focus icons overlap")
        by_row = defaultdict(list)
        for row in self.rows:
            by_row[int(row["y"])].append(int(row["x"]))
        for y, xs in by_row.items():
            xs.sort()
            self.assertTrue(all(b - a >= 2 for a, b in zip(xs, xs[1:])), f"crowded row {y}")
        for row in self.rows:
            parents = row["parents"].split("|") if row["parents"] else []
            self.assertTrue(set(parents) <= self.by_key.keys(), row["key"])
            self.assertIn(row["parent_mode"], {"any", "all"}, row["key"])

        visiting, visited = set(), set()

        def visit(key):
            if key in visiting:
                self.fail(f"focus dependency cycle includes {key}")
            if key in visited:
                return
            visiting.add(key)
            row = self.by_key[key]
            for parent in row["parents"].split("|") if row["parents"] else []:
                visit(parent)
            visiting.remove(key)
            visited.add(key)

        for key in self.by_key:
            visit(key)

    def test_tree_is_hidden_and_matches_every_csv_node(self):
        header = self.tree.split("\n\tfocus = {", 1)[0]
        self.assertEqual("ROC_datong_postwar", scalar(header, "id"))
        self.assertEqual("no", scalar(header, "default"))
        country = one_scope(self.tree, "country")
        self.assertEqual("0", scalar(country, "factor"))
        self.assertEqual(59, len(self.blocks))
        self.assertEqual(59, len(self.by_id))
        expected = {f"ROC_pw_{row['key']}" for row in self.rows}
        self.assertEqual(expected, set(self.by_id))
        for row in self.rows:
            block = self.by_id[f"ROC_pw_{row['key']}"]
            self.assertEqual(row["x"], scalar(block, "x"), row["key"])
            self.assertEqual(row["y"], scalar(block, "y"), row["key"])

    def test_prerequisites_match_any_and_all_semantics(self):
        for row in self.rows:
            block = self.by_id[f"ROC_pw_{row['key']}"]
            parent_ids = [f"ROC_pw_{key}" for key in row["parents"].split("|") if key]
            actual = prerequisite_blocks(block)
            if not parent_ids:
                self.assertEqual([], actual, row["key"])
            elif row["parent_mode"] == "any":
                self.assertEqual([set(parent_ids)], [set(ids) for ids in actual], row["key"])
            else:
                self.assertEqual({frozenset((parent,)) for parent in parent_ids},
                                 {frozenset(ids) for ids in actual}, row["key"])

    def test_four_party_choices_are_pairwise_mutually_exclusive(self):
        for party in PARTIES:
            block = self.by_id[f"ROC_pw_{party}"]
            actual = set(ids_in_scope(block, "mutually_exclusive"))
            expected = {f"ROC_pw_{other}" for other in PARTIES if other != party}
            self.assertEqual(expected, actual, party)
        for row in self.rows:
            if row["key"] not in PARTIES:
                self.assertEqual([], named_scopes(self.by_id[f"ROC_pw_{row['key']}"] , "mutually_exclusive"))

    def test_each_party_can_reach_its_own_ending_and_shared_nodes_remain_reachable(self):
        for party, ending in ENDINGS.items():
            blocked = set(PARTIES) - {party}
            reachable = {key for key, row in self.by_key.items() if not row["parents"]}
            changed = True
            while changed:
                changed = False
                for key, row in self.by_key.items():
                    if key in reachable or key in blocked or not row["parents"]:
                        continue
                    parents = row["parents"].split("|")
                    available = any(p in reachable for p in parents) if row["parent_mode"] == "any" else all(
                        p in reachable for p in parents
                    )
                    if available:
                        reachable.add(key)
                        changed = True
            self.assertIn(ending, reachable, f"{party} cannot complete {ending}")
            self.assertFalse(set(ENDINGS.values()) & (reachable - {ending}), party)

        all_reachable = {key for key, row in self.by_key.items() if not row["parents"]}
        changed = True
        while changed:
            changed = False
            for key, row in self.by_key.items():
                if key in all_reachable or not row["parents"]:
                    continue
                parents = row["parents"].split("|")
                available = any(p in all_reachable for p in parents) if row["parent_mode"] == "any" else all(
                    p in all_reachable for p in parents
                )
                if available:
                    all_reachable.add(key)
                    changed = True
        self.assertEqual(set(self.by_key), all_reachable)

    def test_rewards_icons_and_localisation_are_complete(self):
        self.assertTrue(self.localisation_bytes.startswith(b"\xef\xbb\xbf"), "localisation needs a UTF-8 BOM")
        keys = re.findall(r"(?m)^\s*([A-Za-z0-9_.-]+):0\s+", self.localisation)
        postwar_keys = [key for key in keys if key.startswith("ROC_pw_")]
        self.assertEqual(len(postwar_keys), len(set(postwar_keys)), "duplicate postwar localisation key")
        localised = set(keys)
        icons = set()
        for row in self.rows:
            key = row["key"]
            block = self.by_id[f"ROC_pw_{key}"]
            name_key = scalar(block, "icon")
            icons.add(name_key)
            self.assertIn(f"ROC_pw_{key}", localised, key)
            self.assertIn(f"ROC_pw_{key}_desc", localised, key)
            rewards = named_scopes(block, "completion_reward")
            self.assertEqual(1, len(rewards), key)
            self.assertRegex(rewards[0], REAL_EFFECT, key)

        base_goals = ROOT.parent.parent / "interface/goals.gfx"
        base_icons = set(re.findall(r'name\s*=\s*"([^"]+)"', base_goals.read_text(encoding="utf-8-sig")))
        for icon in icons:
            self.assertIn(icon, base_icons, f"undefined vanilla focus icon: {icon}")

        for tooltip in re.findall(r"custom_effect_tooltip\s*=\s*(ROC_pw_[A-Za-z0-9_]+)", self.focus_source):
            self.assertIn(tooltip, localised, f"missing tooltip localization: {tooltip}")
        for name in re.findall(r"(?ms)add_tech_bonus\s*=\s*\{\s*name\s*=\s*(ROC_pw_[A-Za-z0-9_]+)", self.focus_source):
            self.assertIn(name, localised, f"missing research bonus localization: {name}")

        idea_ids = set(re.findall(r"(?m)^\s*(ROC_pw_(?:ending|timed)_[a-z_]+)\s*=\s*\{", self.ideas))
        expected_ideas = {f"ROC_pw_ending_{key}" for key in ENDINGS.values()} | {
            "ROC_pw_timed_investment", "ROC_pw_timed_rural_recovery",
            "ROC_pw_timed_research", "ROC_pw_timed_administration",
        }
        self.assertEqual(expected_ideas, idea_ids)
        vanilla_ideas = ROOT.parent.parent / "common/ideas"
        vanilla_source = "\n".join(path.read_text(encoding="utf-8-sig", errors="replace")
                                      for path in vanilla_ideas.rglob("*.txt"))
        idea_modifiers = re.findall(r"(?m)^\s*([A-Za-z][A-Za-z0-9_]+)\s*=\s*-?0?\.\d+", self.ideas)
        for modifier in idea_modifiers:
            self.assertRegex(vanilla_source, rf"(?m)^\s*{re.escape(modifier)}\s*=", modifier)
        picture_names = set(re.findall(r"(?m)^\s*picture\s*=\s*(\S+)", self.ideas))
        gfx_source = "\n".join(path.read_text(encoding="utf-8-sig", errors="replace")
                                   for path in (ROOT / "interface").rglob("*.gfx"))
        gfx_names = set(re.findall(r'name\s*=\s*"([^"]+)"', gfx_source))
        for picture in picture_names:
            self.assertIn(f"GFX_idea_{picture}", gfx_names, f"undefined idea picture: {picture}")
        for idea_id in idea_ids:
            self.assertIn(idea_id, localised)
            self.assertIn(f"{idea_id}_desc", localised)

    def test_local_build_rewards_only_use_owned_controlled_core_slots_with_fallback(self):
        for key, building in (("regional_development", "infrastructure"), ("employment", "industrial_complex")):
            reward = one_scope(self.by_id[f"ROC_pw_{key}"], "completion_reward")
            self.assertRegex(reward, r"any_owned_state\s*=\s*\{[\s\S]*?is_core_of\s*=\s*ROOT")
            self.assertRegex(reward, r"is_controlled_by\s*=\s*ROOT")
            self.assertRegex(reward, rf"free_building_slots\s*=\s*\{{[\s\S]*?building\s*=\s*{building}[\s\S]*?size\s*>\s*0")
            self.assertRegex(reward, rf"type\s*=\s*{building}[\s\S]*?level\s*=\s*1[\s\S]*?instant_build\s*=\s*yes")
            self.assertRegex(reward, r"else\s*=\s*\{[\s\S]*?add_political_power\s*=")

    def test_temporary_ideas_refresh_by_shared_id_and_use_limited_durations(self):
        shared = {
            "ROC_pw_timed_investment": {"individual_investment", "private_investment"},
            "ROC_pw_timed_rural_recovery": {"farm_associations", "tenancy"},
            "ROC_pw_timed_research": {"school_education", "student_branches"},
            "ROC_pw_timed_administration": {"association_permits", "simplify_administration"},
        }
        for idea_id, focus_keys in shared.items():
            self.assertEqual(1, len(re.findall(rf"(?m)^\s*{idea_id}\s*=\s*\{{", self.ideas)))
            for key in focus_keys:
                reward = one_scope(self.by_id[f"ROC_pw_{key}"], "completion_reward")
                self.assertRegex(reward, rf"add_timed_idea\s*=\s*\{{[\s\S]*?idea\s*=\s*{idea_id}[\s\S]*?days\s*=\s*(?:180|270|365)")

    def test_demobilization_rewards_civilian_reintegration(self):
        reward = one_scope(self.by_id["ROC_pw_demobilization"], "completion_reward")
        self.assertIn("add_stability", reward)
        self.assertNotIn("add_war_support", reward)
        self.assertNotIn("delete_unit", reward)


if __name__ == "__main__":
    unittest.main()
