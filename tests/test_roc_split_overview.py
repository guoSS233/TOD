"""Regression checks for the separate ROC economy and committee overviews."""

from pathlib import Path
import unittest

from test_roc_allied_parties import named_event, read_event, economic_decisions
from test_roc_central_economy import CentralState, read_script
from test_roc_central_economy_gui import one, scalar, descendants
from test_sichuan_red_opportunity import parse_clausewitz


ROOT = Path(__file__).resolve().parents[1]
CATEGORY_FILE = ROOT / "common/decisions/categories/ROC.txt"
DECISION_FILE = ROOT / "common/decisions/ROC.txt"
SCRIPTED_GUI_FILE = ROOT / "common/scripted_guis/ROC_central_economy.txt"


def parse(path):
    return parse_clausewitz(path.read_text(encoding="utf-8-sig"), path.as_posix())


def top_block(path, name):
    return one(parse(path), name)


class RocSplitOverview(unittest.TestCase):
    def test_category_entries_are_separate_and_follow_live_system_flags(self):
        categories = parse(CATEGORY_FILE)
        economy = one(categories, "ROC_economic_administration")
        committee = one(categories, "ROC_focus_sanpai")
        self.assertEqual(scalar(economy, "scripted_gui"), "ROC_central_economy_window")
        self.assertEqual(scalar(committee, "scripted_gui"), "ROC_economic_council_window")
        self.assertIn(("ROC_ce_administration_active", "yes"), list(descendants(one(economy, "visible"))))
        self.assertIn(("ROC_has_gemingweiyuanhui", "yes"), list(descendants(one(committee, "visible"))))
        self.assertNotIn(("ROC_has_gemingweiyuanhui", "yes"), list(descendants(one(economy, "visible"))))
        self.assertNotIn(("ROC_ce_administration_active", "yes"), list(descendants(one(committee, "visible"))))

    def test_committee_missions_and_delays_are_moved_without_losing_other_decisions(self):
        decisions = parse(DECISION_FILE)
        economy = economic_decisions()
        committee = one(decisions, "ROC_focus_sanpai")
        economy_ids = {key for key, _ in economy}
        committee_ids = {key for key, _ in committee}
        expected_committee = {
            "ROC_decision_zuopai", "ROC_decision_zhongpai", "ROC_decision_youpai",
            "ROC_decision_zuoxiantuoxie", "ROC_decision_youxiantuoxie",
        }
        self.assertEqual(committee_ids, expected_committee)
        self.assertEqual(economy_ids & expected_committee, set())
        # The merged country file also contains other economic categories' decisions.
        council_economy_ids = {key for key in economy_ids if key.startswith("ROC_econ_")} | {
            key for key in economy_ids if key in {
                "ROC_decision_nongcunjianshe", "ROC_decision_minshengjianshe",
                "ROC_decision_junshijianshe", "ROC_decision_kuojiangangkou",
            }
        }
        self.assertEqual(len(council_economy_ids) + len(committee_ids), 20)
        all_ids = council_economy_ids | committee_ids
        self.assertEqual(len(all_ids), 20)

    def test_real_initialization_and_ruan_appointment_reveal_economy_rows(self):
        state = CentralState()
        state.ideas.add("ROC_idea_YuShude")
        state.missions.pop("ROC_decision_bop_jingjidahui", None)
        state.initialize()
        state.effect("ROC_econ_refresh")
        self.assertIn("ROC_ce_initialized", state.flags)
        self.assertIn("ROC_ma_favors_initialized", state.flags)
        self.assertNotIn("ROC_ce_minister_profiles_initialized", state.flags)

        meeting = read_event("ROC_pingheng.9997")
        state.run(one(meeting, "immediate"))
        option = next(
            body for key, body in meeting
            if key == "option" and scalar(body, "name") == "ROC_pingheng.9997.e"
        )
        state.run([(key, value) for key, value in option if key not in {"name", "trigger"}])
        self.assertIn("ROC_idea_RuanXiaoxian", state.ideas)
        self.assertIn("ROC_econ_term_active", state.flags)
        self.assertIn("ROC_ma_favors_initialized", state.flags)

        scripted_gui = one(parse(SCRIPTED_GUI_FILE), "scripted_gui")
        registration = one(scripted_gui, "ROC_central_economy_window")
        triggers = one(registration, "triggers")
        economy_rows = {
            key for key, _ in triggers
            if key.startswith("ROC_ce_gui_") and key.endswith("_visible")
        }
        self.assertTrue(economy_rows)
        for row in economy_rows:
            self.assertTrue(state.passes(one(triggers, row)), row)


if __name__ == "__main__":
    unittest.main()
