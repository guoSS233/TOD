"""Whole GPS content inventory; static checks do not execute the HOI4 engine."""
from collections import Counter
from pathlib import Path
import re
import unittest

from test_sichuan_red_opportunity import Comparison, parse_localization

ROOT = Path(__file__).resolve().parents[1]
LOC = ROOT / "localisation/simp_chinese/TOD_GPS_l_simp_chinese.yml"


def parse_audit_script(path):
    """Retain assignment blocks and bare lists, including legacy idea traits."""
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|#[^\n]*|[{}]|[=<>!]+|[^\s{}=<>!"#]+',
                        path.read_text(encoding="utf-8-sig"))
    tokens = [t for t in tokens if not t.startswith("#")]
    position = 0

    def group(nested=False):
        nonlocal position
        result = []
        while position < len(tokens):
            key = tokens[position]
            position += 1
            if key == "}":
                if not nested:
                    raise ValueError(f"Unexpected closing brace in {path}")
                return result
            if position < len(tokens) and tokens[position] in ("=", "<", ">", "<=", ">=", "!=", "=="):
                operator = tokens[position]
                position += 1
                value = tokens[position]
                position += 1
                value = group(True) if value == "{" else value.strip('"')
                result.append((key.strip('"'), value if operator == "=" else Comparison(operator, value)))
            else:
                result.append((key.strip('"'), None))
        if nested:
            raise ValueError(f"Unclosed block in {path}")
        return result

    return group()


def descendants(entries):
    for key, value in entries:
        yield key, value
        if isinstance(value, list):
            yield from descendants(value)


def first(entries, key, default=None):
    return next((v for k, v in entries if k == key), default)


def inventory():
    scripts = {p.relative_to(ROOT).as_posix(): parse_audit_script(p)
               for folder in ("common", "events", "interface")
               for p in (ROOT / folder).rglob("*GPS*")
               if p.is_file() and p.suffix in (".txt", ".gui")}
    loc, duplicates = parse_localization(LOC.read_bytes())
    focus_script = scripts["common/national_focus/GPS.txt"]
    focuses = [v for k, v in focus_script if k == "shared_focus" and isinstance(v, list)]
    focuses += [v for k, v in first(focus_script, "focus_tree") if k == "focus"]
    decisions = [(k, v) for _, category in scripts["common/decisions/GPS.txt"]
                 for k, v in category if isinstance(v, list)]
    events = [v for k, v in scripts["events/GPS.txt"] if k == "country_event"]
    ideas = [(k, v) for _, categories in scripts["common/ideas/GPS_idea.txt"]
             for _, values in categories for k, v in values if isinstance(v, list)]
    return scripts, loc, duplicates, focuses, decisions, events, ideas


class GpsFullContent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scripts, cls.loc, cls.duplicates, cls.focuses, cls.decisions, cls.events, cls.ideas = inventory()

    def assert_localized(self, keys):
        self.assertEqual(sorted(k for k in set(keys) if not self.loc.get(k, "").strip()), [])

    def test_all_focus_names_descriptions_and_rewards(self):
        self.assertEqual(len(self.focuses), 105)
        keys = [first(f, "id") for f in self.focuses]
        self.assertEqual(len(keys), len(set(keys)))
        self.assert_localized(keys + [k + "_desc" for k in keys])
        for focus in self.focuses:
            self.assertTrue(first(focus, "completion_reward"), first(focus, "id"))
            self.assertLessEqual(len(self.loc[first(focus, "id") + "_desc"]), 203)

    def test_all_decision_names_and_descriptions(self):
        self.assertEqual(len(self.decisions), 37)
        keys = [k for k, _ in self.decisions]
        self.assertEqual(len(keys), len(set(keys)))
        self.assert_localized(keys + [k + "_desc" for k in keys])
        for key, decision in self.decisions:
            self.assertTrue(any(first(decision, field) for field in
                                ("complete_effect", "remove_effect", "timeout_effect", "modifier")), key)

    def test_all_events_have_titles_descriptions_options_and_unique_ids(self):
        self.assertEqual(len(self.events), 97)
        ids = [first(e, "id") for e in self.events]
        self.assertEqual(len(ids), len(set(ids)))
        keys = []
        for event in self.events:
            keys.append(first(event, "title"))
            description = first(event, "desc")
            keys.extend([description] if isinstance(description, str) else
                        [v for k, v in descendants(description) if k == "text"])
            options = [v for k, v in event if k == "option"]
            self.assertTrue(options, first(event, "id"))
            keys.extend(first(option, "name") for option in options)
        self.assert_localized(keys)

    def test_explicit_gps_text_references_resolve(self):
        fields = {"title", "desc", "text", "localization_key", "custom_effect_tooltip", "tooltip",
                  "custom_cost_text", "unlock_decision_category_tooltip"}
        keys = [v for script in self.scripts.values() for k, v in descendants(script)
                if k in fields and isinstance(v, str) and
                v.startswith(("GPS", "GPSevents", "POLITICS_GPS"))]
        # These explicit fallbacks suppress optional records and receipt sentences.
        empty_fallbacks = {
            "GPS_gov_demob_record_none", "GPS_gov_archive_line_none", "GPS_gov_archive_none",
            "GPS_gov_overview_GetGPSGovOrdersPromise_none", "GPS_gov_overview_GetGPSGovCoalPromise_none",
            "GPS_gov_overview_GetGPSGovRestartPromise_none", "GPS_gov_overview_tang_register_none",
            "GPS_gov_overview_committee_table_none", "GPS_gov_overview_grain_none",
            "GPS_gov_overview_demobilization_none",
        }
        for key in empty_fallbacks:
            self.assertIn(key, self.loc)
            self.assertEqual(self.loc[key], "")
        self.assert_localized(k for k in keys if k not in empty_fallbacks)
        self.assertEqual(self.duplicates, [])

    def test_power_balance_categories_dynamic_modifiers_and_visible_names(self):
        keys = []
        for path in ("common/decisions/categories/GPS.txt", "common/dynamic_modifiers/TOD_GPS_modifiers.txt"):
            keys.extend(k for k, _ in self.scripts[path])
        for k, v in descendants(self.scripts["common/bop/GPS_bop.txt"]):
            if k == "id" and isinstance(v, str) and v.startswith("GPS_"):
                keys.append(v)
        for path in ("common/characters/GPS.txt", "common/ideas/GPS_idea.txt",
                     "common/military_industrial_organization/organizations/GPS_organization.txt"):
            keys.extend(v for k, v in descendants(self.scripts[path])
                        if k == "name" and isinstance(v, str) and v.startswith("GPS"))
        keys.extend(k for k, _ in self.ideas if k.startswith("GPS"))
        self.assert_localized(keys)

    def test_old_focus_tooltips_use_the_real_reward_and_units(self):
        expected = {
            "GPS_fenhuadangdijiangling_xiaoguo": ("生活消费品", "-10.0%"),
            "GPS_fangshouyibo_xiaoguo": ("+20.0%",),
            "GPS_dongbeianminling_xiaoguo": ("每日政治点数", "+0.15"),
            "GPS_jiakongtangdudu_xiaoguo": ("每日政治点数", "-0.10"),
            "GPS_kuodawuqichanneng_xiaoguo": ("每日政治点数", "-0.15"),
            "GPS_zhongquanchuji_xiaoguo": ("每日政治点数", "-0.10"),
            "GPS_jianglingjitilingdao_xiaoguo": ("堑壕上限", "+0.05"),
            "GPS_fuyuguotietequan_xiaoguo": ("补给中心范围", "+0.10"),
        }
        for key, fragments in expected.items():
            for fragment in fragments:
                self.assertIn(fragment, self.loc[key], key)
        self.assertNotIn("经费", self.loc["GPS_jiajinguanneilianluo_xiaoguo"])

    def test_militarized_rifle_production_has_a_real_bonus_and_safe_migration(self):
        from test_gps_governance_runtime import GPSState
        from test_gps_reported_events import focus_reward
        reward = focus_reward("GPS_shengchanjunshihua")
        state = GPSState()
        state.run(reward)
        self.assertIn("GPS_shengchanjunshihua_policy", state.ideas)
        self.assertAlmostEqual(state.stability, .45)
        policy = first(first(self.scripts["common/ideas/GPS_idea.txt"], "ideas"), "country")
        bonus = first(first(first(policy, "GPS_shengchanjunshihua_policy"), "equipment_bonus"), "infantry_equipment")
        self.assertEqual(first(bonus, "build_cost_ic"), "-0.15")
        self.assertEqual(first(bonus, "instant"), "yes")
        daily = first(first(self.scripts["common/on_actions/GPS_on_actions.txt"], "on_actions"), "on_daily")
        scope = first(first(first(daily, "effect"), "if"), "GPS")
        migration = [(k, v) for k, v in scope if k == "if" and
                     ("has_completed_focus", "GPS_shengchanjunshihua") in first(v, "limit", [])]
        self.assertEqual(len(migration), 1)
        for complete, legacy, expected in ((True, -.15, True), (False, -.15, False), (True, 0, False)):
            state = GPSState()
            if complete:
                state.focuses.add("GPS_shengchanjunshihua")
            state.vars["GPS_kaifuyitongsansi_buqiang"] = legacy
            state.run(migration)
            state.run(migration)
            self.assertEqual("GPS_shengchanjunshihua_policy" in state.ideas, expected)
            if expected:
                self.assertEqual(state.vars["GPS_kaifuyitongsansi_buqiang"], 0)
        state = GPSState()
        state.run(reward)
        state.focuses.add("GPS_shengchanjunshihua")
        state.run(migration)
        self.assertEqual(state.ideas.count("GPS_shengchanjunshihua_policy") if isinstance(state.ideas, list)
                         else len(state.ideas & {"GPS_shengchanjunshihua_policy"}), 1)

    def test_all_queued_gps_events_exist_once_in_the_repository(self):
        definitions = Counter()
        for path in (ROOT / "events").glob("*.txt"):
            text = path.read_text(encoding="utf-8-sig")
            text = re.sub(r"#[^\n]*", "", text)
            definitions.update(re.findall(r"(?:country|news)_event\s*=\s*\{\s*id\s*=\s*([\w.]+)\s+(?:title|hidden)\s*=", text))
        calls = set()
        for script in self.scripts.values():
            for k, v in descendants(script):
                if k in ("country_event", "news_event") and isinstance(v, list) and first(v, "id"):
                    if not first(v, "title"):
                        calls.add(first(v, "id"))
        self.assertEqual({event: definitions[event] for event in calls if definitions[event] != 1}, {})

    def test_repression_focus_queues_its_matching_existing_story(self):
        from test_gps_reported_events import focus_reward
        reward = focus_reward("GPS_zhongquanchuji")
        self.assertEqual(first(first(reward, "country_event"), "id"), "GPSevents.34")

    def test_all_focus_prerequisites_exist_and_visible_flags_are_localized(self):
        ids = {first(focus, "id") for focus in self.focuses}
        references = {v for focus in self.focuses for k, v in descendants(focus)
                      if k == "focus" and isinstance(v, str)}
        self.assertEqual(references - ids, set())
        visible_flags = {"GPS_chaoxianzhichi", "GPS_huijianjiaotongxi", "GPS_liaoyangqiyi",
                         "GPS_pingluanshengli", "GPS_xiayizhichi"}
        self.assert_localized(visible_flags)

    def test_scripted_text_functions_and_nested_localization_resolve(self):
        functions = {first(v, "name") for k, v in self.scripts["common/scripted_localisation/GPS_scripted_localisation.txt"]
                     if k == "defined_text"}
        calls = {name for value in self.loc.values() for name in re.findall(r"\[(GetGPSGov\w+)\]", value)}
        self.assertEqual(calls - functions, set())
        # GPS-owned substitutions must resolve even when their source is an alias.
        aliases = {key for value in self.loc.values() for key in re.findall(r"\$(GPS[\w.]+)\$", value)}
        self.assert_localized(aliases)

    def test_all_player_spirits_have_names_and_descriptions(self):
        # Former design-company/advisor entries also appear in the legacy ideas file.
        country = first(first(self.scripts["common/ideas/GPS_idea.txt"], "ideas"), "country")
        keys = [k for k, _ in country]
        self.assert_localized(keys + [k + "_desc" for k in keys])


if __name__ == "__main__":
    unittest.main()
