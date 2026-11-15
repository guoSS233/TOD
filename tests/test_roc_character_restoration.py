"""Script-level tests for the ROC uprising's initially unavailable roster.

The small visibility model here is not a replacement for the HOI4 engine.
"""

from collections import Counter
import unittest

from test_ming_inheritance import children, event, one, parse_file, walk


FLAG = "ROC_guangzhou_uprising_available"
OLD_FLAG = "guangzhouqiyi_flag"
PEOPLE = set("""
    ROC_anjiaju ROC_caishenxi ROC_caoyuan ROC_caozhongyuan ROC_changqiankun
    ROC_chengbiguang ROC_chengeng ROC_chenjiliang ROC_chenmingshu ROC_chenshaokuan
    ROC_dengkeng ROC_dengyanda ROC_duandechang ROC_duxigui ROC_duyuming
    ROC_guanlinzheng ROC_helong ROC_huangguangrui ROC_huangqixiang ROC_huangzaixin
    ROC_jiangxianyun ROC_jinfozhuang ROC_lijishen ROC_limingrui ROC_linjianzhang
    ROC_linzun ROC_lishijia ROC_liuchouxi ROC_liufuji ROC_lizhangda ROC_lizhilong
    ROC_ludeming ROC_tangrongbing ROC_wangbi ROC_wangerzhuo ROC_wangyaowu
    ROC_wuzhixin ROC_xueyue ROC_xufengzao ROC_xuguangda ROC_xujishen
    ROC_yangshuzhuang ROC_yangxianyi ROC_yuzuobai ROC_zhangfakui ROC_zhangshaozeng
    ROC_zhangxiaozhun ROC_zhaosheng ROC_zhoushidi ROC_zhuyunqing
""".split())
ROLES = {"advisor", "corps_commander", "field_marshal", "navy_leader"}


def roster():
    return one(parse_file("common/characters/ROC.txt"), "characters")


def uprising():
    return one(event("events/ROC.txt", "ROC_start.2"), "option")


def visible_in_country(role, name, country_characters, roc_flags):
    """Evaluate the flag-based alternatives in these role visibility scripts."""
    if name not in country_characters:
        return False
    for key, value in one(one(role, "visible"), "OR"):
        if key == "has_character_flag":
            if value in country_characters.get(name, set()):
                return True
        elif key == name:
            if name in country_characters and all(
                check == "has_character_flag" and flag in country_characters[name]
                for check, flag in value
            ):
                return True
        elif key == "ROC":
            if all(check == "has_country_flag" and flag in roc_flags for check, flag in value):
                return True
        else:
            raise AssertionError(f"unsupported visibility check: {key}")
    return False


class RocCharacterRestorationTests(unittest.TestCase):
    def test_uprising_roster_is_recruited_but_not_retired_in_history(self):
        history = parse_file("history/countries/ROC - guangdong.txt")
        recruited = Counter(children(history, "recruit_character"))
        retired = set(children(history, "retire_character"))
        self.assertEqual(len(PEOPLE), 50)
        for name in PEOPLE:
            with self.subTest(name=name):
                self.assertEqual(recruited[name], 1)
                self.assertNotIn(name, retired)
        self.assertIn("ROC_characters_huananjiaofusi", retired)

    def test_event_enables_exactly_the_intended_recruited_characters(self):
        flagged = [key for _, key, value in walk(uprising()) if key in PEOPLE
                   and isinstance(value, list) and ("set_character_flag", FLAG) in value]
        self.assertEqual(Counter(flagged), Counter(PEOPLE))
        for name in ("ROC_fengru", "ROC_wangganchang", "ROC_wuyouxun"):
            self.assertTrue(any(key == name and isinstance(value, list)
                                and ("set_nationality", "ROC") in value
                                for _, key, value in walk(uprising())))

    def test_all_original_roles_use_their_own_character_flag(self):
        characters = roster()
        counts = Counter()
        for name in PEOPLE:
            character = one(characters, name)
            for role_name, role in character:
                if role_name not in ROLES:
                    continue
                counts[role_name] += 1
                character_check = ((name, [("has_character_flag", FLAG)]) if role_name == "advisor"
                                   else ("has_character_flag", FLAG))
                self.assertEqual(one(role, "visible"), [("OR", [
                    character_check, ("ROC", [("has_country_flag", OLD_FLAG)])])],
                    (name, role_name))
                if role_name == "advisor":
                    self.assertIn(("original_tag", "ROC"), one(role, "allowed"))
        self.assertEqual(counts, {"advisor": 31, "corps_commander": 27,
                                  "field_marshal": 3, "navy_leader": 12})

    def test_roles_appear_after_event_and_remain_visible_after_transfer(self):
        characters = roster()
        roster_flags = {name: set() for name in PEOPLE}
        for name in PEOPLE:
            for role_name, role in one(characters, name):
                if role_name in ROLES:
                    self.assertFalse(visible_in_country(role, name, roster_flags, set()), (name, role_name))
                    self.assertTrue(visible_in_country(role, name, roster_flags, {OLD_FLAG}),
                                    (name, role_name, "old save after uprising"))
                    self.assertFalse(visible_in_country(role, name, {}, {OLD_FLAG}),
                                     (name, role_name, "old save with retired character"))

        for _, name, effects in walk(uprising()):
            if name in PEOPLE and isinstance(effects, list) and ("set_character_flag", FLAG) in effects:
                roster_flags[name].add(FLAG)

        for name in PEOPLE:
            for role_name, role in one(characters, name):
                if role_name in ROLES:
                    self.assertTrue(visible_in_country(role, name, roster_flags, set()), (name, role_name))
                    self.assertTrue(visible_in_country(role, name, {name: roster_flags[name]}, set()),
                                    (name, role_name, "after transfer"))


if __name__ == "__main__":
    unittest.main()
