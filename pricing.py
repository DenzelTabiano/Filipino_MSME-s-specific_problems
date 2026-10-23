"""Transparent scenario-based bakery pricing and production recommendations."""

import math
from itertools import product
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from database import fetch_master_recipes, fetch_overhead_config
from logic import calculate_clearance_price, calculate_true_unit_cost
INPUT_COLUMNS = [
    "Product",
    "Unit Cost (PHP)",
    "Current Price (PHP)",
    "Target Markup (%)",
    "Competitor Price (PHP)",
    "Base Demand (units/day)",
    "Price Elasticity",
    "Promotion Budget (PHP/day)",
    "Lock Price",
    "Lock Markup",
    "Lock Demand",
]


def build_default_pricing_inputs() -> pd.DataFrame:
    """Build editable starting assumptions from the seeded recipe database."""
    recipes = fetch_master_recipes()
    overhead = fetch_overhead_config()
    rows = []
    for item_name, item_data in recipes.items():
        recipe = item_data["recipe"]
        unit_cost = calculate_true_unit_cost(
            batch_raw_ingredient_cost=item_data["batch_raw_ingredient_cost"],
            units_per_batch=recipe.units_per_batch,
            packaging_cost_per_unit=recipe.packaging_cost_per_unit,
            bake_time_minutes=recipe.bake_time_minutes,
            overhead_config=overhead,
        )
        rows.append({
            "Product": item_name,
            "Unit Cost (PHP)": unit_cost,
            "Current Price (PHP)": item_data["default_retail_price"],
            "Target Markup (%)": round(
                (item_data["default_retail_price"] - unit_cost) / unit_cost * 100,
                1,
            ) if unit_cost > 0 else 0.0,
            "Competitor Price (PHP)": item_data["default_retail_price"],
            "Base Demand (units/day)": {
                "pan de sal": 180,
                "spanish bread": 90,
                "ensaymada": 60,
            }.get(item_name.lower(), 60),
            "Price Elasticity": -1.0,
            "Promotion Budget (PHP/day)": 0.0,
            "Lock Price": False,
            "Lock Markup": False,
            "Lock Demand": False,
        })
    return pd.DataFrame(rows, columns=INPUT_COLUMNS)


def _as_bool(value: Any, column: str, product_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "yes", "1"):
            return True
        if normalized in ("false", "no", "0", ""):
            return False
    raise ValueError(f"{product_name}: {column} must be checked or unchecked.")


def validate_pricing_inputs(
    input_data: Any,
    recipes: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Validate editable table data and return normalized product inputs."""
    if isinstance(input_data, pd.DataFrame):
        rows = input_data.to_dict(orient="records")
    elif isinstance(input_data, list):
        rows = input_data
    else:
        raise ValueError("Product inputs must be an editable table.")

    available_recipes = recipes if recipes is not None else fetch_master_recipes()
    normalized_rows: List[Dict[str, Any]] = []
    seen_products = set()

    for row_number, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Row {row_number} is not a valid product row.")
        product_name = str(row.get("Product", "")).strip()
        if not product_name:
            raise ValueError(f"Row {row_number} needs a product name.")
        if product_name not in available_recipes:
            raise ValueError(
                f"'{product_name}' has no saved recipe. Use one of the available products."
            )
        if product_name in seen_products:
            raise ValueError(f"'{product_name}' appears more than once.")
        seen_products.add(product_name)

        values: Dict[str, Any] = {"Product": product_name}
        numeric_columns = {
            "Unit Cost (PHP)": "unit_cost",
            "Current Price (PHP)": "current_price",
            "Target Markup (%)": "target_markup_pct",
            "Competitor Price (PHP)": "competitor_price",
            "Base Demand (units/day)": "base_demand",
            "Price Elasticity": "price_elasticity",
            "Promotion Budget (PHP/day)": "promotion_budget",
        }
        for column, key in numeric_columns.items():
            raw_value = row.get(column)
            is_missing = raw_value is None or (
                isinstance(raw_value, str) and not raw_value.strip()
            )
            if not is_missing:
                try:
                    is_missing = bool(pd.isna(raw_value))
                except (TypeError, ValueError):
                    is_missing = False
            if is_missing:
                if key == "competitor_price":
                    values[key] = None
                    continue
                raise ValueError(f"{product_name}: {column} is required.")
            try:
                number = float(raw_value)
            except (TypeError, ValueError) as error:
                raise ValueError(f"{product_name}: {column} must be a number.") from error
            if number != number or number in (float("inf"), float("-inf")):
                raise ValueError(f"{product_name}: {column} must be finite.")
            values[key] = number

        if values["unit_cost"] < 0:
            raise ValueError(f"{product_name}: unit cost cannot be negative.")
        if values["unit_cost"] > 1_000_000:
            raise ValueError(f"{product_name}: unit cost is outside the supported range.")
        if values["current_price"] <= 0:
            raise ValueError(f"{product_name}: current price must be greater than zero.")
        if values["current_price"] > 1_000_000:
            raise ValueError(f"{product_name}: current price is outside the supported range.")
        if not -99.9 < values["target_markup_pct"] <= 10_000:
            raise ValueError(
                f"{product_name}: target markup must be greater than -99.9% "
                "and no more than 10,000%."
            )
        if values["competitor_price"] is not None and not (
            0 <= values["competitor_price"] <= 1_000_000
        ):
            raise ValueError(
                f"{product_name}: competitor price must be between 0 and 1,000,000 PHP."
            )
        if not 0 <= values["promotion_budget"] <= 10_000_000:
            raise ValueError(
                f"{product_name}: promotion budget must be between 0 and 10,000,000 PHP."
            )
        if values["base_demand"] < 0:
            raise ValueError(f"{product_name}: base demand cannot be negative.")
        if values["base_demand"] > 1_000_000:
            raise ValueError(f"{product_name}: base demand is outside the supported range.")
        if not values["base_demand"].is_integer():
            raise ValueError(f"{product_name}: base demand must be a whole number of units.")
        if values["price_elasticity"] < -5 or values["price_elasticity"] > 0:
            raise ValueError(
                f"{product_name}: price elasticity must be between -5 and 0 "
                "(for example, -1.0)."
            )
        for column, key in (
            ("Lock Price", "lock_price"),
            ("Lock Markup", "lock_markup"),
            ("Lock Demand", "lock_demand"),
        ):
            values[key] = _as_bool(row.get(column, False), column, product_name)
        if values["lock_price"] and values["lock_markup"]:
            raise ValueError(
                f"{product_name}: lock either price or markup, not both. "
                "When markup is locked, the Target Markup (%) input determines the price."
            )
        if values["lock_markup"] and values["unit_cost"] <= 0:
            raise ValueError(
                f"{product_name}: unit cost must be greater than zero to lock markup."
            )
        normalized_rows.append(values)

    if not normalized_rows:
        raise ValueError("Add at least one product to the input table.")
    return normalized_rows


def _product_options(
    item: Dict[str, Any],
    recipe_data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Enumerate price and demand-uplift assumptions for one product."""
    recipe = recipe_data["recipe"]
    current_price = item["current_price"]
    unit_cost = item["unit_cost"]

    if item["lock_price"]:
        prices = [current_price]
    elif item["lock_markup"]:
        prices = [round(unit_cost * (1.0 + item["target_markup_pct"] / 100.0), 2)]
    else:
        prices = [round(current_price * factor, 2) for factor in
                  (0.75, 0.85, 0.95, 1.0, 1.05, 1.15, 1.25)]
        prices.extend((
            round(unit_cost, 2),
            round(unit_cost * 1.2, 2),
            round(unit_cost * (1.0 + item["target_markup_pct"] / 100.0), 2),
        ))
        if item["competitor_price"] is not None and item["competitor_price"] > 0:
            prices.append(round(item["competitor_price"], 2))
    prices = sorted({price for price in prices if price > 0})

    uplifts = (
        (0.0, 0.2, 0.5, 1.0)
        if not item["lock_demand"] and item["promotion_budget"] > 0
        else (0.0,)
    )
    options = []
    for price, uplift in product(prices, uplifts):
        if item["lock_demand"]:
            demand = item["base_demand"]
        else:
            price_effect = (price / current_price) ** item["price_elasticity"]
            demand = item["base_demand"] * price_effect * (1.0 + uplift)
        demand_units = max(0, int(round(demand)))
        trays = (demand_units + recipe.tray_capacity - 1) // recipe.tray_capacity
        supply = trays * recipe.tray_capacity
        sold = min(supply, demand_units)
        surplus = max(0, supply - demand_units)
        clearance_price = calculate_clearance_price(unit_cost, price)
        revenue = sold * price + surplus * clearance_price
        variable_cost = supply * unit_cost
        options.append({
            "price": price,
            "demand": demand_units,
            "uplift": uplift,
            "trays": trays,
            "supply": supply,
            "sold": sold,
            "surplus": surplus,
            "clearance_price": clearance_price,
            "promotion_cost": item["promotion_budget"] if uplift > 0 else 0.0,
            "revenue": revenue,
            "variable_cost": variable_cost,
            "unit_cost": unit_cost,
        })
    return options


def _scenario_metrics(
    selected: Sequence[Tuple[Dict[str, Any], Dict[str, Any]]],
    fixed_overhead: float,
) -> Dict[str, Any]:
    revenue = sum(option["revenue"] for _, option in selected)
    variable_cost = sum(option["variable_cost"] for _, option in selected)
    promotion_cost = sum(option["promotion_cost"] for _, option in selected)
    trays = sum(option["trays"] for _, option in selected)
    units_sold = sum(option["sold"] for _, option in selected)
    expected_demand = sum(option["demand"] for _, option in selected)
    net_profit = revenue - variable_cost - fixed_overhead - promotion_cost
    return {
        "revenue": round(revenue, 2),
        "variable_cost": round(variable_cost, 2),
        "promotion_cost": round(promotion_cost, 2),
        "fixed_overhead": round(fixed_overhead, 2),
        "net_profit": round(net_profit, 2),
        "trays": trays,
        "units_sold": units_sold,
        "expected_demand": expected_demand,
        "selected": selected,
    }


def recommend_pricing_scenarios(
    input_data: Any,
    objective: str,
    max_oven_trays: int,
    target_profit: Optional[float] = None,
    fixed_overhead: Optional[float] = None,
    recipes: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Find feasible scenarios and return goal, profit, and sales alternatives."""
    if max_oven_trays <= 0:
        raise ValueError("Maximum oven trays must be greater than zero.")
    if int(max_oven_trays) != max_oven_trays:
        raise ValueError("Maximum oven trays must be a whole number.")
    if objective not in ("Maximize daily profit", "Break even", "Reach target profit", "Maximize units sold"):
        raise ValueError("Choose a valid business goal.")
    if objective == "Reach target profit" and target_profit is None:
        raise ValueError("Enter a target daily net profit.")

    available_recipes = recipes if recipes is not None else fetch_master_recipes()
    overhead_config = fetch_overhead_config()
    overhead_amount = (
        overhead_config.fixed_daily_overhead_php
        if fixed_overhead is None
        else float(fixed_overhead)
    )
    if not math.isfinite(overhead_amount) or overhead_amount < 0:
        raise ValueError("Fixed daily overhead must be a finite, non-negative amount.")
    if target_profit is not None and not math.isfinite(float(target_profit)):
        raise ValueError("Target daily net profit must be finite.")
    normalized = validate_pricing_inputs(input_data, available_recipes)
    option_lists = [
        (item, _product_options(item, available_recipes[item["Product"]]))
        for item in normalized
    ]
    combination_count = math.prod(len(options) for _, options in option_lists)
    if combination_count > 250_000:
        raise ValueError(
            "This scenario search is too large. Select fewer products or lock more variables."
        )

    feasible = []
    for combination in product(*(options for _, options in option_lists)):
        selected = [(option_lists[index][0], option) for index, option in enumerate(combination)]
        if sum(option["trays"] for option in combination) > max_oven_trays:
            continue
        scenario = _scenario_metrics(selected, overhead_amount)
        scenario["adjustment"] = sum(
            abs(option["price"] - item["current_price"]) / item["current_price"]
            + option["uplift"]
            for item, option in selected
        )
        feasible.append(scenario)

    if not feasible:
        raise ValueError(
            "No feasible production scenario fits the oven capacity. "
            "Reduce demand or increase the tray limit."
        )

    if objective == "Reach target profit":
        target = float(target_profit)
        passing = [scenario for scenario in feasible if scenario["net_profit"] >= target]
        goal_scenario = (
            min(passing, key=lambda scenario: (
                scenario["net_profit"] - target,
                -scenario["units_sold"],
                scenario["adjustment"],
            ))
            if passing
            else max(feasible, key=lambda scenario: (
                scenario["net_profit"],
                scenario["units_sold"],
                -scenario["adjustment"],
            ))
        )
        goal_reached = goal_scenario["net_profit"] >= target
    elif objective == "Break even":
        nonnegative = [scenario for scenario in feasible if scenario["net_profit"] >= 0]
        goal_scenario = (
            min(nonnegative, key=lambda scenario: (
                scenario["net_profit"],
                -scenario["units_sold"],
                scenario["adjustment"],
            ))
            if nonnegative
            else max(feasible, key=lambda scenario: scenario["net_profit"])
        )
        goal_reached = goal_scenario["net_profit"] >= 0
    elif objective == "Maximize units sold":
        profitable = [scenario for scenario in feasible if scenario["net_profit"] >= 0]
        goal_scenario = (
            max(profitable, key=lambda scenario: (
                scenario["units_sold"],
                scenario["net_profit"],
                -scenario["adjustment"],
            ))
            if profitable
            else max(feasible, key=lambda scenario: scenario["net_profit"])
        )
        goal_reached = bool(profitable)
    else:
        goal_scenario = max(feasible, key=lambda scenario: (
            scenario["net_profit"],
            scenario["units_sold"],
            -scenario["adjustment"],
        ))
        goal_reached = True

    max_profit = max(feasible, key=lambda scenario: (
        scenario["net_profit"],
        scenario["units_sold"],
        -scenario["adjustment"],
    ))
    profitable = [scenario for scenario in feasible if scenario["net_profit"] >= 0]
    max_sales = max(
        profitable or feasible,
        key=lambda scenario: (
            scenario["units_sold"],
            scenario["net_profit"],
            -scenario["adjustment"],
        ),
    )

    candidates = [
        ("Recommended for selected goal", goal_scenario),
        ("Highest projected profit", max_profit),
        ("Highest sales volume", max_sales),
    ]
    distinct = []
    seen = set()
    for label, scenario in candidates:
        key = tuple(
            (item["Product"], option["price"], option["demand"], option["trays"])
            for item, option in scenario["selected"]
        )
        if key in seen:
            continue
        seen.add(key)
        scenario_copy = dict(scenario)
        scenario_copy["label"] = label
        distinct.append(scenario_copy)

    return {
        "scenarios": distinct,
        "goal_reached": goal_reached,
        "feasible_count": len(feasible),
        "objective": objective,
        "target_profit": target_profit,
        "max_oven_trays": max_oven_trays,
    }


def scenario_tables(
    results: Dict[str, Any],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Format aggregate and per-item input/output comparisons for the UI."""
    summary_rows = []
    comparison_rows = []
    for scenario in results["scenarios"]:
        summary_rows.append({
            "Scenario": scenario["label"],
            "Net Profit (PHP)": scenario["net_profit"],
            "Revenue (PHP)": scenario["revenue"],
            "Variable Costs (PHP)": scenario["variable_cost"],
            "Promotion Budget (PHP)": scenario["promotion_cost"],
            "Units Sold (est.)": scenario["units_sold"],
            "Demand (est.)": scenario["expected_demand"],
            "Oven Trays": scenario["trays"],
        })
        for item, option in scenario["selected"]:
            current_markup = (
                (item["current_price"] - item["unit_cost"]) / item["unit_cost"] * 100
                if item["unit_cost"] > 0
                else 0.0
            )
            recommended_markup = (
                (option["price"] - option["unit_cost"]) / option["unit_cost"] * 100
                if option["unit_cost"] > 0
                else 0.0
            )
            comparison_rows.append({
                "Scenario": scenario["label"],
                "Product": item["Product"],
                "Input Price (PHP)": item["current_price"],
                "Suggested Price (PHP)": option["price"],
                "Input Markup (%)": round(current_markup, 2),
                "Target Markup (%)": item["target_markup_pct"],
                "Suggested Markup (%)": round(recommended_markup, 2),
                "Competitor Price (PHP)": item["competitor_price"],
                "Promotion Budget (PHP/day)": item["promotion_budget"],
                "Base Demand (units)": item["base_demand"],
                "Estimated Demand (units)": option["demand"],
                "Assumed Demand Uplift (%)": round(option["uplift"] * 100, 1),
                "Promotion Cost (PHP)": option["promotion_cost"],
                "Supply (units)": option["supply"],
                "Estimated Sales (units)": option["sold"],
                "Surplus (units)": option["surplus"],
                "Trays": option["trays"],
            })
    return pd.DataFrame(summary_rows), pd.DataFrame(comparison_rows)


def apply_ai_constraints(
    input_data: Any,
    parsed_target: Any,
) -> pd.DataFrame:
    """Apply explicitly parsed demand constraints to the displayed input snapshot."""
    frame = pd.DataFrame(input_data).copy()
    if frame.empty or not parsed_target.item_constraints:
        return frame
    demand_by_name = {
        constraint.item_name.lower(): constraint.target_demand_units
        for constraint in parsed_target.item_constraints
        if constraint.target_demand_units is not None
    }
    for index, row in frame.iterrows():
        demand = demand_by_name.get(str(row["Product"]).lower())
        if demand is not None:
            frame.at[index, "Base Demand (units/day)"] = demand
    return frame
