"""Static contract checks for the restored ROC Great Practice branch."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_sichuan_red_opportunity import Comparison, parse_clausewitz


MAIN_FOCUS = ROOT / "common/national_focus/ROC.txt"
POSTWAR_FOCUS = ROOT / "common/national_focus/ROC_postwar.txt"
MAIN_LOCALIZATION = ROOT / "localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml"

RESTORED_LAYOUT = {
    "gaizaojingjidezhunbei": (6, 1),
    "weidashijiandekaishi": (6, 2),
    "tudigaige": (2, 3),
    "shanghuinongchanggaizhi": (1, 4),
    "luoshipingjundiquan": (3, 4),
    "zhengheyouxiuzhishifenzi": (6, 3),
    "gulixueshuziyou": (6, 5),
    "jieguanguanyinggongcheng": (10, 3),
    "lianheshanghuishili": (9, 4),
    "shijianjiezhiziben": (11, 4),
    "kuodamincuhuifanwei": (9, 5),
    "qianghuagonghuiquanli": (11, 5),
    "guoyingnongcyunongyegonghui": (1, 5),
    "tuidongnongyehezuoshefazhan": (3, 5),
    "tuidongxiangcunjiansheyundong": (2, 6),
    "luoshisishichengongzuozhi": (10, 6),
    "kuojianguangzhoudaxue": (6, 7),
    "huaxiafazhanzhanlue": (6, 9),
}
REMOVED_FOCI = {
    "ROC_ce_national_accounts", "ROC_ce_joint_program", "ROC_ce_industrial_delivery",
    "ROC_ce_agricultural_delivery", "ROC_ce_transport_delivery", "ROC_ce_acceptance_rules",
    "ROC_ce_mining_development", "ROC_ce_commercial_circulation",
    "ROC_pw_ce_national_accounts", "ROC_pw_ce_joint_program", "ROC_pw_ce_industrial_delivery",
    "ROC_pw_ce_agricultural_delivery", "ROC_pw_ce_transport_delivery", "ROC_pw_ce_acceptance_rules",
    "ROC_pw_ce_mining_development", "ROC_pw_ce_commercial_circulation",
}
MANUAL_AXIS_SHIFTS = {
    "kuodamincuhuifanwei": "ROC_ma_manual_market_015",
    "qianghuagonghuiquanli": "ROC_ma_manual_public_015",
    "guoyingnongcyunongyegonghui": "ROC_ma_manual_market_010",
    "tuidongnongyehezuoshefazhan": "ROC_ma_manual_public_010",
}


def read_script(path: Path):
    return parse_clausewitz(path.read_text(encoding="utf-8-sig"), path.as_posix())


def one(entries, key):
    values = [value for name, value in entries if name == key]
    if len(values) != 1:
        raise AssertionError(f"expected one {key}, found {len(values)}")
    return values[0]


def scalar(entries, key):
    value = one(entries, key)
    if isinstance(value, list):
        raise AssertionError(f"expected scalar {key}, got a scope")
    return value


def descendants(entries):
    for key, value in entries:
        yield key, value
        if isinstance(value, list):
            yield from descendants(value)


def focus_blocks(path: Path):
    trees = [value for key, value in read_script(path) if key == "focus_tree"]
    if not trees:
        raise AssertionError(f"expected at least one focus_tree in {path}")
    return [value for tree in trees for key, value in tree if key == "focus"]


def focus_trees(path: Path):
    return [
        [value for key, value in tree if key == "focus"]
        for key, tree in read_script(path) if key == "focus_tree"
    ]


def focus_map(path: Path):
    blocks = focus_blocks(path)
    result = {scalar(block, "id"): block for block in blocks}
    if len(result) != len(blocks):
        raise AssertionError(f"duplicate focus IDs in {path}")
    return result


def focus_references(expression):
    return [value for key, value in descendants(expression) if key == "focus" and isinstance(value, str)]


def prerequisites(block):
    return [focus_references(value) for key, value in block if key == "prerequisite"]


class RocGreatPracticeContract(unittest.TestCase):
    def test_removed_delivery_and_acceptance_nodes_are_absent(self):
        for path in (MAIN_FOCUS, POSTWAR_FOCUS):
            with self.subTest(tree=path.name):
                self.assertTrue(REMOVED_FOCI.isdisjoint(focus_map(path)))

    def test_restored_practice_branch_coordinates_and_dependencies(self):
        by_id = focus_map(MAIN_FOCUS)
        for focus_id, expected_position in RESTORED_LAYOUT.items():
            with self.subTest(focus=focus_id):
                self.assertIn(focus_id, by_id)
                block = by_id[focus_id]
                self.assertEqual((int(scalar(block, "x")), int(scalar(block, "y"))), expected_position)

        for focus_id, expected in {
            "gaizaojingjidezhunbei": [["guangzhouqiyi"]],
            "weidashijiandekaishi": [["gaizaojingjidezhunbei"]],
            "tudigaige": [["weidashijiandekaishi"]],
            "shanghuinongchanggaizhi": [["tudigaige"]],
            "luoshipingjundiquan": [["tudigaige"]],
            "zhengheyouxiuzhishifenzi": [["weidashijiandekaishi"]],
            "gulixueshuziyou": [["zhengheyouxiuzhishifenzi"]],
            "guoyingnongcyunongyegonghui": [["shanghuinongchanggaizhi"]],
            "tuidongnongyehezuoshefazhan": [["luoshipingjundiquan"]],
            "tuidongxiangcunjiansheyundong": [["tuidongnongyehezuoshefazhan", "guoyingnongcyunongyegonghui"]],
            "jieguanguanyinggongcheng": [["weidashijiandekaishi"]],
            "lianheshanghuishili": [["jieguanguanyinggongcheng"]],
            "shijianjiezhiziben": [["jieguanguanyinggongcheng"]],
            "kuodamincuhuifanwei": [["lianheshanghuishili"]],
            "qianghuagonghuiquanli": [["shijianjiezhiziben"]],
            "luoshisishichengongzuozhi": [["qianghuagonghuiquanli", "kuodamincuhuifanwei"]],
            "kuojianguangzhoudaxue": [
                ["tuidongxiangcunjiansheyundong"], ["gulixueshuziyou"], ["luoshisishichengongzuozhi"],
            ],
            "huaxiafazhanzhanlue": [["kuojianguangzhoudaxue"]],
        }.items():
            with self.subTest(prerequisite=focus_id):
                self.assertEqual(prerequisites(by_id[focus_id]), expected)

    def test_nearby_focus_reanchors_preserve_existing_dependencies(self):
        by_id = focus_map(MAIN_FOCUS)
        expected_positions = {
            "sunwendexinnian": (22, 8),
            "banbugonghelinshixianfa": (22, 10),
            "tongyizhonghua": (22, 11),
            "bashuzhiguo": (18, 12),
            "dongbeiwenti": (22, 12),
            "jisuiyuxi": (26, 12),
            "gemingdetongzhi": (21, 13),
            "yueguoshanhaiguan": (23, 13),
            "hengsaoxinan": (20, 14),
            "jiefangmobei": (22, 14),
            "xibeigongfa": (26, 14),
            "zhonghuayongyuangonghe": (22, 15),
        }
        for focus_id, expected in expected_positions.items():
            with self.subTest(focus=focus_id):
                self.assertEqual(
                    (int(scalar(by_id[focus_id], "x")), int(scalar(by_id[focus_id], "y"))),
                    expected,
                )
        self.assertEqual(prerequisites(by_id["hengsaoxinan"]), [["bashuzhiguo"]])
        self.assertEqual(prerequisites(by_id["banbugonghelinshixianfa"]), [])
        self.assertEqual(
            scalar(by_id["banbugonghelinshixianfa"], "x"),
            scalar(by_id["tongyizhonghua"], "x"),
        )
        self.assertEqual(prerequisites(by_id["tongyizhonghua"]), [["banbugonghelinshixianfa"]])

    def test_restored_focus_rewards_shift_only_the_independent_structure_axis(self):
        by_id = focus_map(MAIN_FOCUS)
        for focus_id, effect in MANUAL_AXIS_SHIFTS.items():
            with self.subTest(focus=focus_id):
                reward = one(by_id[focus_id], "completion_reward")
                entries = list(descendants(reward))
                self.assertIn((effect, "yes"), entries)
                self.assertNotIn("add_power_balance_value", {key for key, _ in entries})
                self.assertNotIn(("ROC_ce_focus_contribution", "yes"), entries)

    def test_manual_branch_keeps_original_four_hour_working_day_description(self):
        source = MAIN_LOCALIZATION.read_text(encoding="utf-8-sig")
        self.assertRegex(
            source,
            r'(?m)^\s*luoshisishichengongzuozhi_desc:0\s+"[^"\n]*四时辰劳动，四时辰休息，还有四时辰属于自己！[^"\n]*"',
        )

    def test_focus_references_are_unique_acyclic_and_have_no_same_row_collisions(self):
        for path in (MAIN_FOCUS, POSTWAR_FOCUS):
            for blocks in focus_trees(path):
                by_id = {scalar(block, "id"): block for block in blocks}
                positions = {}
                graph = {}
                for block in blocks:
                    focus_id = scalar(block, "id")
                    prereqs = [ref for group in prerequisites(block) for ref in group]
                    self.assertTrue(set(prereqs) <= by_id.keys(), focus_id)
                    graph[focus_id] = prereqs
                    position = (int(scalar(block, "x")), int(scalar(block, "y")))
                    for other_id, other_position in positions.items():
                        if position[1] == other_position[1]:
                            self.assertGreaterEqual(abs(position[0] - other_position[0]), 2, f"{focus_id} crowds {other_id}")
                    positions[focus_id] = position

                visiting, visited = set(), set()

                def visit(focus_id):
                    self.assertNotIn(focus_id, visiting, f"prerequisite cycle through {focus_id} in {path.name}")
                    if focus_id in visited:
                        return
                    visiting.add(focus_id)
                    for parent in graph[focus_id]:
                        visit(parent)
                    visiting.remove(focus_id)
                    visited.add(focus_id)

                for focus_id in graph:
                    visit(focus_id)


if __name__ == "__main__":
    unittest.main()
