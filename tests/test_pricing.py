import unittest

import pandas as pd

from charts import generate_pricing_scenario_charts
from database import fetch_master_recipes
from pricing import (
    _product_options,
    build_default_pricing_inputs,
    recommend_pricing_scenarios,
    scenario_tables,
    validate_pricing_inputs,
)


class PricingScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_inputs = build_default_pricing_inputs()

    def run_scenarios(self, inputs, goal="Maximize daily profit", target=None, trays=12):
        return recommend_pricing_scenarios(
            input_data=inputs,
            objective=goal,
            target_profit=target,
            max_oven_trays=trays,
        )

    def test_scenarios_respect_locked_price_and_demand(self):
        inputs = self.default_inputs.iloc[[0]].copy()
        inputs.loc[:, "Lock Price"] = True
        inputs.loc[:, "Lock Demand"] = True
        result = self.run_scenarios(inputs)

        for scenario in result["scenarios"]:
            item, option = scenario["selected"][0]
            self.assertEqual(option["price"], item["current_price"])
            self.assertEqual(option["demand"], item["base_demand"])

    def test_locked_markup_sets_price_from_cost(self):
        inputs = self.default_inputs.iloc[[0]].copy()
        inputs.loc[:, "Target Markup (%)"] = 20.0
        inputs.loc[:, "Lock Markup"] = True
        result = self.run_scenarios(inputs)

        for scenario in result["scenarios"]:
            item, option = scenario["selected"][0]
            self.assertAlmostEqual(
                (option["price"] - item["unit_cost"]) / item["unit_cost"] * 100,
                20.0,
                places=0,
            )

    def test_higher_price_reduces_demand_for_negative_elasticity(self):
        inputs = self.default_inputs.iloc[[0]].copy()
        item = validate_pricing_inputs(inputs)[0]
        recipes = fetch_master_recipes()
        options = _product_options(item, recipes[item["Product"]])
        price_demand = {option["price"]: option["demand"] for option in options}
        higher_prices = [
            price for price in price_demand
            if price > item["current_price"]
        ]
        self.assertTrue(higher_prices)
        self.assertLess(
            price_demand[min(higher_prices)],
            price_demand[item["current_price"]],
        )

    def test_target_profit_unreachable_is_reported_without_faking_success(self):
        inputs = self.default_inputs.iloc[[0]].copy()
        result = self.run_scenarios(
            inputs,
            goal="Reach target profit",
            target=1_000_000,
        )
        self.assertFalse(result["goal_reached"])
        self.assertLess(result["scenarios"][0]["net_profit"], 1_000_000)

    def test_scenarios_respect_oven_capacity_and_have_comparison_tables(self):
        inputs = self.default_inputs.iloc[[0]].copy()
        inputs.loc[:, "Base Demand (units/day)"] = 90
        result = self.run_scenarios(inputs, trays=4)
        self.assertTrue(all(scenario["trays"] <= 4 for scenario in result["scenarios"]))
        summary, comparison = scenario_tables(result)
        self.assertIn("Net Profit (PHP)", summary.columns)
        self.assertIn("Input Price (PHP)", comparison.columns)
        self.assertIn("Suggested Price (PHP)", comparison.columns)
        profit_chart, price_chart = generate_pricing_scenario_charts(result)
        self.assertIsNotNone(profit_chart)
        self.assertIsNotNone(price_chart)

    def test_blank_competitor_price_is_optional(self):
        inputs = self.default_inputs.iloc[[0]].copy()
        inputs.loc[:, "Competitor Price (PHP)"] = float("nan")
        normalized = validate_pricing_inputs(inputs)
        self.assertIsNone(normalized[0]["competitor_price"])

    def test_invalid_positive_elasticity_is_rejected(self):
        inputs = self.default_inputs.iloc[[0]].copy()
        inputs.loc[:, "Price Elasticity"] = 0.5
        with self.assertRaisesRegex(ValueError, "between -5 and 0"):
            validate_pricing_inputs(inputs)

    def test_demand_uplift_scenarios_require_a_promotion_budget(self):
        inputs = self.default_inputs.iloc[[0]].copy()
        recipes = fetch_master_recipes()
        item = validate_pricing_inputs(inputs)[0]
        options_without_budget = _product_options(item, recipes[item["Product"]])
        self.assertEqual({option["uplift"] for option in options_without_budget}, {0.0})

        inputs.loc[:, "Promotion Budget (PHP/day)"] = 50.0
        item_with_budget = validate_pricing_inputs(inputs)[0]
        options_with_budget = _product_options(
            item_with_budget,
            recipes[item_with_budget["Product"]],
        )
        paid_options = [option for option in options_with_budget if option["uplift"] > 0]
        self.assertTrue(paid_options)
        self.assertTrue(all(option["promotion_cost"] == 50.0 for option in paid_options))


if __name__ == "__main__":
    unittest.main()
