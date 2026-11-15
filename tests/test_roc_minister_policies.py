"""Run ROC policy adoption through the shipped decisions and effects."""
import unittest

from test_roc_allied_parties import ROOT, one, read_script, economic_decisions
from test_roc_central_economy import CentralState


POLICIES = {
    "ROC_ma_policy_agriculture_collectivized": "ROC_ma_policy_agriculture_household",
    "ROC_ma_policy_agriculture_household": "ROC_ma_policy_agriculture_collectivized",
    "ROC_ma_policy_cooperative_procurement": "ROC_ma_policy_market_distribution",
    "ROC_ma_policy_market_distribution": "ROC_ma_policy_cooperative_procurement",
    "ROC_ma_policy_private_management": "ROC_ma_policy_public_holding",
    "ROC_ma_policy_public_holding": "ROC_ma_policy_private_management",
}


class RocMinisterPolicies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.minister_decisions = dict(economic_decisions())
        cls.economy_decisions = dict(economic_decisions())

    def state(self, profile):
        state = CentralState(
            ROC_ce_minister_profile_id=profile,
            ROC_ma_clock_owner=profile,
            ROC_ma_stage=3,
            ROC_ma_days_remaining=98,
        )
        state.focuses.add("gaizaojingjidezhunbei")
        if profile in range(1, 6):
            slug = ("yu", "yan", "ruan", "chen", "xiao")[profile - 1]
            state.focuses.update({f"ROC_ma_{slug}_{suffix}" for suffix in ("1", "step2", "2", "step4", "3")})
        return state

    def complete(self, state, decisions, decision_id):
        decision = decisions.get(decision_id)
        self.assertIsNotNone(decision, f"missing actual decision {decision_id}")
        self.assertTrue(state.passes(one(decision, "available")), f"{decision_id} should be available")
        complete_effect = next((value for key, value in decision if key == "complete_effect"), None)
        self.assertIsNotNone(complete_effect, f"{decision_id} must adopt its policy in complete_effect")
        state.decisions.add(decision_id)
        state.run(complete_effect)

    def test_six_successful_decision_paths_apply_the_selected_policy_and_remove_its_opposite(self):
        cases = (
            ("ROC_ma_agriculture_collectivized_decision", 3, "ROC_ma_policy_agriculture_collectivized", "minister"),
            ("ROC_ma_agriculture_household_decision", 5, "ROC_ma_policy_agriculture_household", "minister"),
            ("ROC_ma_yu_2_decision", 1, "ROC_ma_policy_cooperative_procurement", "minister"),
            ("ROC_ma_xiao_2_decision", 5, "ROC_ma_policy_market_distribution", "minister"),
            ("ROC_decision_bop_left_clgq", 5, "ROC_ma_policy_private_management", "economy"),
            ("ROC_decision_bop_right_sqgyh", 3, "ROC_ma_policy_public_holding", "economy"),
        )
        for decision_id, profile, selected, source in cases:
            with self.subTest(decision=decision_id):
                state = self.state(profile)
                opposite = POLICIES[selected]
                state.ideas.update({opposite, "ROC_ce_structure_mixed"})
                if decision_id == "ROC_decision_bop_left_clgq":
                    state.ideas.add("ROC_idea_XiaoZheng")
                elif decision_id == "ROC_decision_bop_right_sqgyh":
                    state.ideas.add("ROC_idea_RuanXiaoxian")
                if source == "minister":
                    self.complete(state, self.minister_decisions, decision_id)
                else:
                    self.complete(state, self.economy_decisions, decision_id)
                self.assertIn(selected, state.ideas)
                self.assertNotIn(opposite, state.ideas)
                self.assertIn("ROC_ce_structure_mixed", state.ideas)

    def test_agriculture_choices_reject_wrong_minister_term_focus_and_repeated_policy(self):
        for decision_id, profile, selected, opposing_profile, required_focus in (
            ("ROC_ma_agriculture_collectivized_decision", 3, "ROC_ma_policy_agriculture_collectivized", 5, "ROC_ma_ruan_step2"),
            ("ROC_ma_agriculture_household_decision", 5, "ROC_ma_policy_agriculture_household", 3, "ROC_ma_xiao_step2"),
        ):
            with self.subTest(decision=decision_id):
                valid = self.state(profile)
                decision = self.minister_decisions.get(decision_id)
                self.assertIsNotNone(decision, f"missing actual decision {decision_id}")
                valid.ideas.add(selected)
                self.assertFalse(valid.passes(one(decision, "available")))

                lagging_stage = self.state(profile)
                lagging_stage.vars["ROC_ma_stage"] = 2
                self.assertTrue(lagging_stage.passes(one(decision, "available")))

                invalid_states = []
                wrong_minister = self.state(opposing_profile)
                invalid_states.append(wrong_minister)
                missing_focus = self.state(profile)
                missing_focus.focuses.discard(required_focus)
                invalid_states.append(missing_focus)
                conference = self.state(profile)
                conference.flags.add("ROC_econ_conference_pending")
                invalid_states.append(conference)
                resignation = self.state(profile)
                resignation.flags.add("ROC_econ_resignation_pending")
                invalid_states.append(resignation)
                expired = self.state(profile)
                expired.flags.add("ROC_ma_timeout_pending")
                invalid_states.append(expired)
                no_term = self.state(profile)
                no_term.missions.clear()
                invalid_states.append(no_term)

                complete_effect = next((value for key, value in decision if key == "complete_effect"), None)
                self.assertIsNotNone(complete_effect, f"{decision_id} must recheck its safety gates")
                for state in invalid_states:
                    state.ideas.add(POLICIES[selected])
                    self.assertFalse(state.passes(one(decision, "available")))
                    before = set(state.ideas)
                    state.run(complete_effect)
                    self.assertEqual(state.ideas, before)

    def test_policy_effects_are_idempotent_and_independent_across_groups(self):
        adoptions = (
            ("ROC_ma_policy_adopt_agriculture_collectivized", "ROC_ma_policy_agriculture_collectivized", "ROC_ma_policy_agriculture_household"),
            ("ROC_ma_policy_adopt_agriculture_household", "ROC_ma_policy_agriculture_household", "ROC_ma_policy_agriculture_collectivized"),
            ("ROC_ma_policy_adopt_cooperative_procurement", "ROC_ma_policy_cooperative_procurement", "ROC_ma_policy_market_distribution"),
            ("ROC_ma_policy_adopt_market_distribution", "ROC_ma_policy_market_distribution", "ROC_ma_policy_cooperative_procurement"),
            ("ROC_ma_policy_adopt_private_management", "ROC_ma_policy_private_management", "ROC_ma_policy_public_holding"),
            ("ROC_ma_policy_adopt_public_holding", "ROC_ma_policy_public_holding", "ROC_ma_policy_private_management"),
        )
        for effect, selected, opposite in adoptions:
            with self.subTest(effect=effect):
                state = self.state(3)
                state.ideas.update({opposite, "ROC_ce_structure_mixed"})
                self.assertIn(effect, state.effects, f"missing actual adoption effect {effect}")
                if effect not in state.effects:
                    continue
                state.effect(effect)
                state.effect(effect)
                self.assertIn(selected, state.ideas)
                self.assertNotIn(opposite, state.ideas)
                self.assertIn("ROC_ce_structure_mixed", state.ideas)

        state = self.state(3)
        for effect in (
            "ROC_ma_policy_adopt_agriculture_household",
            "ROC_ma_policy_adopt_cooperative_procurement",
            "ROC_ma_policy_adopt_public_holding",
        ):
            state.effect(effect)
        self.assertTrue({
            "ROC_ma_policy_agriculture_household",
            "ROC_ma_policy_cooperative_procurement",
            "ROC_ma_policy_public_holding",
        }.issubset(state.ideas))
        self.assertEqual(sum(idea in state.ideas for idea in POLICIES.values()), 3)

    def test_daily_refresh_reappointment_and_legacy_focus_rewards_do_not_restore_a_replaced_policy(self):
        state = self.state(3)
        state.ideas.add("ROC_idea_RuanXiaoxian")
        if "ROC_ma_policy_adopt_agriculture_household" not in state.effects:
            self.fail("missing actual adoption effect ROC_ma_policy_adopt_agriculture_household")
            return
        state.effect("ROC_ma_policy_adopt_agriculture_household")
        state.effect("ROC_ma_select_ruan_policy")
        state.effect("ROC_ma_daily")
        state.effect("ROC_ce_daily")
        state.run([("complete_national_focus", "ROC_ma_ruan_2")])
        self.assertIn("ROC_ma_policy_agriculture_household", state.ideas)
        self.assertNotIn("ROC_ma_policy_agriculture_collectivized", state.ideas)

    def test_agriculture_decisions_only_change_the_policy_ideas(self):
        for decision_id, profile, selected in (
            ("ROC_ma_agriculture_collectivized_decision", 3, "ROC_ma_policy_agriculture_collectivized"),
            ("ROC_ma_agriculture_household_decision", 5, "ROC_ma_policy_agriculture_household"),
        ):
            with self.subTest(decision=decision_id):
                state = self.state(profile)
                decision = self.minister_decisions[decision_id]
                state.decisions.add(decision_id)
                before = (dict(state.vars), dict(state.missions), state.pp, state.stability, state.axis,
                          list(state.events), set(state.flags), set(state.decisions))
                state.run(one(decision, "complete_effect"))
                after = (dict(state.vars), dict(state.missions), state.pp, state.stability, state.axis,
                         list(state.events), set(state.flags), set(state.decisions))
                self.assertEqual(after, before)
                self.assertEqual(state.ideas, {selected})

    def test_policy_ideas_have_real_modifiers_and_chinese_tooltips(self):
        from test_sichuan_red_opportunity import parse_localization

        path = ROOT / "common/ideas/ROC_minister_policies.txt"
        if not path.exists():
            self.fail("missing real ROC minister policy idea definitions")
            return
        for script in (
            path,
            ROOT / "common/scripted_effects/ROC_scripted_effects.txt",
            ROOT / "common/decisions/ROC.txt",
            ROOT / "common/decisions/ROC.txt",
        ):
            self.assertFalse(script.read_bytes().startswith(b"\xef\xbb\xbf"), f"{script.name} must be UTF-8 without BOM")
        ideas = one(read_script("common/ideas/ROC_minister_policies.txt"), "ideas")
        country_ideas = dict(one(ideas, "country"))
        expected_modifiers = {
            "ROC_ma_policy_agriculture_collectivized": {"production_speed_infrastructure_factor": "0.06", "consumer_goods_factor": "0.01"},
            "ROC_ma_policy_agriculture_household": {"consumer_goods_factor": "-0.02", "production_speed_infrastructure_factor": "-0.02"},
            "ROC_ma_policy_cooperative_procurement": {"consumer_goods_factor": "-0.01", "trade_opinion_factor": "0.05"},
            "ROC_ma_policy_market_distribution": {"production_speed_industrial_complex_factor": "0.03", "trade_opinion_factor": "0.10"},
            "ROC_ma_policy_private_management": {"production_speed_industrial_complex_factor": "0.05"},
            "ROC_ma_policy_public_holding": {"industrial_capacity_factory": "0.04"},
        }
        for idea_id, modifiers in expected_modifiers.items():
            modifier = dict(one(country_ideas[idea_id], "modifier"))
            self.assertEqual(modifier, modifiers)
        self.assertTrue(path.exists())

        loc_path = ROOT / "localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml"
        data = loc_path.read_bytes()
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"), "new Chinese localisation must use UTF-8 BOM")
        entries, errors = parse_localization(data)
        self.assertEqual([key for key in errors if key.startswith("ROC_ma_")], [])
        for idea_id in expected_modifiers:
            self.assertIn(idea_id, entries)
            self.assertIn(f"{idea_id}_desc", entries)
        for tooltip in (
            "ROC_ma_adopt_agriculture_collectivized_tt",
            "ROC_ma_adopt_agriculture_household_tt",
            "ROC_ma_adopt_cooperative_procurement_tt",
            "ROC_ma_adopt_market_distribution_tt",
            "ROC_ma_adopt_private_management_tt",
            "ROC_ma_adopt_public_holding_tt",
        ):
            self.assertIn(tooltip, entries)

        agenda_loc = ROOT / "localisation/simp_chinese/TOD_ROC_l_simp_chinese.yml"
        agenda_entries, agenda_errors = parse_localization(agenda_loc.read_bytes())
        self.assertEqual([key for key in agenda_errors if key.startswith("ROC_ma_")], [])
        for key in (
            "ROC_ma_agriculture_collectivized_decision",
            "ROC_ma_agriculture_collectivized_decision_desc",
            "ROC_ma_agriculture_household_decision",
            "ROC_ma_agriculture_household_decision_desc",
        ):
            self.assertIn(key, agenda_entries)

    def test_corporate_policy_complete_effect_rechecks_minister_focus_and_administration(self):
        cases = (
            ("ROC_decision_bop_left_clgq", 5, "ROC_idea_XiaoZheng", "ROC_ma_xiao_step4", "ROC_ma_policy_private_management"),
            ("ROC_decision_bop_right_sqgyh", 3, "ROC_idea_RuanXiaoxian", "ROC_ma_ruan_2", "ROC_ma_policy_public_holding"),
        )
        for decision_id, profile, minister_idea, route_focus, selected in cases:
            decision = self.economy_decisions[decision_id]
            complete_effect = one(decision, "complete_effect")
            for invalidated in ("minister", "policy_focus", "administration"):
                with self.subTest(decision=decision_id, invalidated=invalidated):
                    state = self.state(profile)
                    state.ideas.update({minister_idea, POLICIES[selected]})
                    self.assertTrue(state.passes(one(decision, "available")))
                    state.decisions.add(decision_id)
                    if invalidated == "minister":
                        state.vars["ROC_ce_minister_profile_id"] = 0
                    elif invalidated == "policy_focus":
                        state.focuses.discard(route_focus)
                    else:
                        state.focuses.discard("gaizaojingjidezhunbei")
                    state.run(complete_effect)
                    self.assertNotIn(selected, state.ideas)
                    self.assertIn(POLICIES[selected], state.ideas)


if __name__ == "__main__":
    unittest.main()
