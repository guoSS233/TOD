"""Decision visibility and availability follow the current minister's completed route."""
import unittest

from test_roc_allied_parties import economic_decisions, one, read_script
from test_roc_central_economy import CentralState


SLUGS = ((1, "yu"), (2, "yan"), (3, "ruan"), (4, "chen"), (5, "xiao"))


def decision_map(path):
    return dict(economic_decisions())


def block_value(block, key, default=None):
    return next((value for name, value in block if name == key), default)


class RocEconomicDecisionUnlocks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.personal = decision_map("common/decisions/ROC.txt")
        cls.economy = decision_map("common/decisions/ROC.txt")
        cls.projects = decision_map("common/decisions/ROC.txt")
        cls.council = decision_map("common/decisions/ROC.txt")

    def state(self, profile, focuses=()):
        state = CentralState(
            ROC_ce_minister_profile_id=profile,
            ROC_ma_clock_owner=profile,
            ROC_ma_stage=3,
            ROC_econ_stage=3,
            ROC_ce_project_id=0,
        )
        state.flags.update({
            "ROC_ce_program_done",
            "ROC_ce_industry_unlocked",
            "ROC_ce_agriculture_unlocked",
            "ROC_ce_transport_unlocked",
        })
        state.focuses.update(focuses)
        return state

    def visible(self, state, decision):
        condition = block_value(decision, "visible")
        self.assertIsNotNone(condition, "decision must define its focus-aware visible gate")
        return condition is not None and state.passes(condition)

    def available(self, state, decision):
        condition = block_value(decision, "available")
        self.assertIsNotNone(condition, "decision must define an availability gate")
        return condition is not None and state.passes(condition)

    def availability_tooltips(self, decision):
        available = block_value(decision, "available")
        return [
            block_value(value, "tooltip")
            for key, value in available
            if key == "custom_trigger_tooltip"
        ]

    def assert_hidden_recheck(self, decision, tooltip):
        complete_effect = block_value(decision, "complete_effect")
        self.assertEqual(block_value(complete_effect, "custom_effect_tooltip"), tooltip)
        self.assertIsNone(block_value(complete_effect, "if"), "effect preview must not expose the recheck")
        hidden_effect = block_value(complete_effect, "hidden_effect")
        self.assertIsNotNone(hidden_effect)
        self.assertIsNotNone(block_value(hidden_effect, "if"), "real completion must recheck inside hidden_effect")

    def test_personal_decisions_unlock_at_the_matching_focus_and_hide_after_switch(self):
        for profile, slug in SLUGS:
            first = self.personal[f"ROC_ma_{slug}_1_decision"]
            second = self.personal[f"ROC_ma_{slug}_2_decision"]
            for decision in (first, second):
                self.assertEqual(
                    self.availability_tooltips(decision),
                    ["ROC_ma_decision_available_tt"],
                )
            state = self.state(profile)
            with self.subTest(profile=profile, route="before_focus"):
                self.assertFalse(self.visible(state, first))
                self.assertFalse(self.available(state, first))
                self.assertFalse(self.visible(state, second))
                self.assertFalse(self.available(state, second))

            state.focuses.add(f"ROC_ma_{slug}_1")
            with self.subTest(profile=profile, route="first_focus"):
                self.assertTrue(self.visible(state, first))
                self.assertTrue(self.available(state, first))
                self.assertFalse(self.visible(state, second))
                self.assertFalse(self.available(state, second))

            state.focuses.add(f"ROC_ma_{slug}_step2")
            state.vars["ROC_ma_stage"] = 2
            with self.subTest(profile=profile, route="step2_focus"):
                self.assertTrue(self.visible(state, second))
                self.assertTrue(self.available(state, second))

            state.vars["ROC_ce_minister_profile_id"] = profile % 5 + 1
            with self.subTest(profile=profile, route="after_switch"):
                self.assertFalse(self.visible(state, first))
                self.assertFalse(self.available(state, first))
                self.assertFalse(self.visible(state, second))
                self.assertFalse(self.available(state, second))

    def test_completed_second_focus_unlocks_while_cached_stage_lags_and_advances_safely(self):
        state = self.state(1, ("ROC_ma_yu_1", "ROC_ma_yu_step2"))
        state.ideas.add("ROC_idea_YuShude")
        state.vars.update(
            ROC_ma_stage=2,
            ROC_ma_yu_stage=2,
            ROC_ma_days_remaining=180,
            ROC_ma_yu_days=180,
        )
        state.flags.update({"ROC_ma_five_stage_migrated", "ROC_ma_six_stage_migrated"})
        state.missions["ROC_ma_current_action"] = 180
        decision = self.personal["ROC_ma_yu_2_decision"]
        self.assertTrue(self.visible(state, decision))
        self.assertTrue(self.available(state, decision))

        state.run(block_value(decision, "complete_effect"))
        self.assertEqual(state.vars["ROC_ma_day_credit"], 0)
        self.assertEqual(state.vars["ROC_ma_days_remaining"], 159)
        self.assertEqual(state.missions["ROC_ma_current_action"], 159)

    def test_retained_focus_history_and_legacy_flags_do_not_leak_personal_decisions(self):
        all_focuses = {
            f"ROC_ma_{slug}_{suffix}"
            for _, slug in SLUGS
            for suffix in ("1", "step2", "2", "step4", "3", "step6")
        }
        state = self.state(1, all_focuses)
        state.flags.update({
            "ROC_ce_industry_unlocked", "ROC_ce_agriculture_unlocked", "ROC_ce_transport_unlocked",
            "ROC_econ_yu_pilot_done", "ROC_econ_yan_expansion_done",
            *(f"ROC_bill_project_{project}_approved" for project in range(1, 11)),
        })
        personal_route_ids = {
            f"ROC_ma_{slug}_{number}_decision"
            for _, slug in SLUGS
            for number in (1, 2)
        }

        for profile, slug in SLUGS:
            state.vars["ROC_ce_minister_profile_id"] = profile
            shown = {
                decision_id
                for decision_id, decision in self.personal.items()
                if decision_id in personal_route_ids and self.visible(state, decision)
            }
            self.assertEqual(
                shown,
                {f"ROC_ma_{slug}_1_decision", f"ROC_ma_{slug}_2_decision"},
                f"profile {profile} must only show its own routes after reappointment",
            )

    def test_six_legacy_policies_require_a_current_route_and_recheck_adoption(self):
        route_cases = {
            "ROC_decision_bop_left_fcsyqy": ((1, "yu_1"), (5, "xiao_2")),
            "ROC_decision_bop_left_jqmysc": ((2, "yan_2"), (4, "chen_step4")),
            "ROC_decision_bop_left_clgq": ((5, "xiao_step4"),),
            "ROC_decision_bop_right_qhgh": ((4, "chen_1"),),
            "ROC_decision_bop_right_ssjm": ((3, "ruan_1"), (4, "chen_2")),
            "ROC_decision_bop_right_sqgyh": ((3, "ruan_2"), (4, "chen_2")),
        }
        for decision_id, routes in route_cases.items():
            decision = self.economy[decision_id]
            for profile, route in routes:
                with self.subTest(decision=decision_id, route=route):
                    valid = self.state(profile, (f"ROC_ma_{route}",))
                    self.assertTrue(self.visible(valid, decision))
                    self.assertTrue(self.available(valid, decision))

                    no_route = self.state(profile, ("kuodamincuhuifanwei", "qianghuagonghuiquanli"))
                    self.assertFalse(self.visible(no_route, decision))
                    self.assertFalse(self.available(no_route, decision))

                    if decision_id in {
                        "ROC_decision_bop_left_clgq",
                        "ROC_decision_bop_right_sqgyh",
                    }:
                        selected = (
                            "ROC_ma_policy_private_management"
                            if decision_id.endswith("left_clgq")
                            else "ROC_ma_policy_public_holding"
                        )
                        opposite = (
                            "ROC_ma_policy_public_holding"
                            if selected.endswith("private_management")
                            else "ROC_ma_policy_private_management"
                        )
                        valid.ideas.add(opposite)
                        self.assert_hidden_recheck(
                            decision,
                            "ROC_ma_adopt_private_management_tt"
                            if decision_id.endswith("left_clgq")
                            else "ROC_ma_adopt_public_holding_tt",
                        )
                        valid.focuses.discard(f"ROC_ma_{route}")
                        valid.run(block_value(decision, "complete_effect"))
                        self.assertNotIn(selected, valid.ideas)
                        self.assertIn(opposite, valid.ideas)

    def test_agriculture_policy_decisions_require_their_current_route(self):
        cases = (
            ("ROC_ma_agriculture_collectivized_decision", ((3, "ruan_step2"), (4, "chen_step2"))),
            ("ROC_ma_agriculture_household_decision", ((5, "xiao_step2"),)),
        )
        for decision_id, routes in cases:
            decision = self.personal[decision_id]
            self.assertEqual(
                self.availability_tooltips(decision),
                ["ROC_ma_adopt_agriculture_available_tt"],
            )
            for profile, route in routes:
                with self.subTest(decision=decision_id, route=route):
                    valid = self.state(profile, (f"ROC_ma_{route}",))
                    self.assertTrue(self.visible(valid, decision))
                    self.assertTrue(self.available(valid, decision))

                    lagging_stage = self.state(profile, (f"ROC_ma_{route}",))
                    lagging_stage.vars["ROC_ma_stage"] = 2
                    self.assertTrue(self.available(lagging_stage, decision))

                    locked = self.state(profile)
                    self.assertFalse(self.visible(locked, decision))
                    self.assertFalse(self.available(locked, decision))

                    valid.focuses.discard(f"ROC_ma_{route}")
                    valid.run(block_value(decision, "complete_effect"))
                    selected = (
                        "ROC_ma_policy_agriculture_collectivized"
                        if decision_id.endswith("collectivized_decision")
                        else "ROC_ma_policy_agriculture_household"
                    )
                    self.assertNotIn(selected, valid.ideas)

    def test_central_projects_require_the_current_route_at_visibility_availability_and_completion(self):
        route_cases = {
            "ROC_ce_industry_project": ((1, "yu_1"), (3, "ruan_1"), (4, "chen_1"), (2, "yan_2"), (5, "xiao_2")),
            "ROC_ce_agriculture_project": ((2, "yan_1"), (5, "xiao_1"), (1, "yu_2"), (3, "ruan_2"), (4, "chen_2")),
            "ROC_ce_transport_project": tuple((profile, f"{slug}_1") for profile, slug in SLUGS),
        }
        project_tooltips = {
            "ROC_ce_industry_project": "ROC_ce_industry_project_started_tt",
            "ROC_ce_agriculture_project": "ROC_ce_agriculture_project_started_tt",
            "ROC_ce_transport_project": "ROC_ce_transport_project_started_tt",
        }
        for decision_id, routes in route_cases.items():
            decision = self.projects[decision_id]
            self.assert_hidden_recheck(decision, project_tooltips[decision_id])
            project = decision_id.removeprefix("ROC_ce_").removesuffix("_project")
            for profile, route in routes:
                with self.subTest(decision=decision_id, route=route):
                    valid = self.state(profile, (f"ROC_ma_{route}",))
                    self.assertTrue(self.visible(valid, decision))
                    self.assertTrue(self.available(valid, decision))

                    valid.focuses.discard(f"ROC_ma_{route}")
                    valid.run(block_value(decision, "complete_effect"))
                    self.assertEqual(valid.vars.get("ROC_ce_project_id", 0), 0)

    def test_legacy_approvals_do_not_offer_new_actions_but_paid_work_still_settles(self):
        project_ids = {"yu": 1, "yan": 3, "ruan": 5, "chen": 7, "xiao": 9}
        for _, slug in SLUGS:
            state = self.state(1)
            for offset, suffix in enumerate(("pilot", "expansion")):
                decision_id = f"ROC_econ_{slug}_{suffix}"
                decision = self.council[decision_id]
                project_id = project_ids[slug] + offset
                state.flags.add(f"ROC_bill_project_{project_id}_approved")
                self.assertFalse(self.visible(state, decision))
                self.assertFalse(self.available(state, decision))

        paid_id = "ROC_econ_yu_pilot"
        paid = self.state(1)
        paid.decisions.add(paid_id)
        decision = self.council[paid_id]
        self.assertTrue(self.visible(paid, decision))
        self.assertFalse(self.available(paid, decision))
        paid.vars["ROC_ce_minister_profile_id"] = 2
        self.assertFalse(self.visible(paid, decision))
        paid.run(block_value(decision, "remove_effect"))
        self.assertIn("ROC_econ_yu_pilot_done", paid.flags)

    def test_stage_six_shows_focus_and_seven_hides_routine_without_disabling_timeout(self):
        decision = self.personal["ROC_ma_current_action"]
        state = self.state(1)
        state.vars.update(ROC_ma_clock_owner=1, ROC_ma_stage=6, ROC_ma_days_remaining=180)
        state.missions["ROC_ma_current_action"] = 180
        self.assertTrue(self.visible(state, decision))
        state.vars.update(ROC_ma_stage=7, ROC_ma_days_remaining=90)
        state.missions["ROC_ma_current_action"] = 90
        self.assertFalse(self.visible(state, decision))
        self.assertEqual(block_value(decision, "cancel_if_not_visible"), "no")
        self.assertTrue(state.passes(block_value(decision, "activation")))
        timeout = block_value(decision, "timeout_effect")
        self.assertEqual(block_value(timeout, "hidden_effect"), [("ROC_ma_timeout", "yes")])

    def test_term_review_is_only_visible_in_review_year_before_review(self):
        decision = self.council["ROC_econ_term_review"]
        state = self.state(1)
        state.vars["ROC_econ_stage"] = 2
        self.assertFalse(self.visible(state, decision))
        state.vars["ROC_econ_stage"] = 3
        self.assertTrue(self.visible(state, decision))
        self.assertTrue(self.available(state, decision))
        state.flags.add("ROC_econ_term_review_done")
        self.assertFalse(self.visible(state, decision))
        self.assertFalse(self.available(state, decision))

    def test_administration_cancel_tooltips_are_customized(self):
        decision_ids = (
            "ROC_decision_bop_left_fcsyqy", "ROC_decision_bop_left_jqmysc",
            "ROC_decision_bop_left_clgq", "ROC_decision_bop_right_qhgh",
            "ROC_decision_bop_right_ssjm", "ROC_decision_bop_right_sqgyh",
        )
        decision_ids += tuple(
            f"ROC_econ_{slug}_{suffix}"
            for _, slug in SLUGS
            for suffix in ("pilot", "expansion")
        )
        decisions = [
            (decision_id, self.economy.get(decision_id, self.council.get(decision_id)))
            for decision_id in decision_ids
        ]
        for decision_id, decision in decisions:
            cancel = block_value(decision, "cancel_trigger")
            with self.subTest(decision=decision_id):
                tooltip = next((value for key, value in cancel if key == "custom_trigger_tooltip"), None)
                self.assertIsNotNone(tooltip)
                if tooltip is not None:
                    self.assertEqual(block_value(tooltip, "tooltip"), "ROC_ce_administration_inactive_tt")


if __name__ == "__main__":
    unittest.main()
