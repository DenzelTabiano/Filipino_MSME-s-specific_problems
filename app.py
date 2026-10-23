import json
import math
import os
import sys
from typing import Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import gradio as gr
import pandas as pd
from dotenv import load_dotenv

from ai_compiler import compile_taglish_intent, explain_pricing_scenarios
from charts import generate_pricing_scenario_charts
from database import fetch_overhead_config, init_db
from pricing import (
    apply_ai_constraints,
    build_default_pricing_inputs,
    recommend_pricing_scenarios,
    scenario_tables,
)

load_dotenv()
init_db()


def _display_float(value: Any) -> Optional[float]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        parsed_value = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Target daily net profit must be a number.") from error
    if not math.isfinite(parsed_value):
        raise ValueError("Target daily net profit must be finite.")
    return parsed_value


def _resolve_business_goal(selected_goal: str, prompt: str, parsed_target: Any) -> str:
    """Use explicit natural-language objectives when the user selects prompt mode."""
    if selected_goal != "Interpret goal from prompt":
        return selected_goal
    if parsed_target and parsed_target.target_net_profit is not None:
        return "Reach target profit"
    normalized = prompt.lower()
    if any(term in normalized for term in (
        "break even", "break-even", "breakeven", "bawi puhunan", "no profit no loss",
    )):
        return "Break even"
    if any(term in normalized for term in (
        "maximize units", "sell more", "higher demand", "increase demand",
        "maximize sales", "maraming mabenta",
    )):
        return "Maximize units sold"
    return "Maximize daily profit"


def run_optimizer(
    business_goal: str,
    target_profit: Any,
    max_oven_trays: Any,
    product_inputs: Any,
    ai_prompt: str,
):
    """Run deterministic scenarios and, when configured, ask Gemini to explain them."""
    try:
        effective_inputs = pd.DataFrame(product_inputs).copy()
        parsed_target = None
        notices = []

        if ai_prompt and ai_prompt.strip():
            parsed_target = compile_taglish_intent(ai_prompt.strip())
            effective_inputs = apply_ai_constraints(effective_inputs, parsed_target)
            if parsed_target.max_oven_capacity_trays is not None:
                max_oven_trays = parsed_target.max_oven_capacity_trays
                notices.append(
                    f"Using the AI-parsed oven limit: {max_oven_trays} trays."
                )

        resolved_goal = _resolve_business_goal(
            business_goal,
            ai_prompt.strip() if ai_prompt else "",
            parsed_target,
        )
        if business_goal == "Interpret goal from prompt":
            notices.append(f"Interpreted business goal: {resolved_goal}.")

        target = _display_float(target_profit)
        if resolved_goal == "Reach target profit" and target is None and parsed_target:
            target = parsed_target.target_net_profit
        if resolved_goal == "Reach target profit" and target is None:
            raise ValueError(
                "Enter a target profit, or include one in the natural-language goal."
            )

        results = recommend_pricing_scenarios(
            input_data=effective_inputs,
            objective=resolved_goal,
            target_profit=target,
            max_oven_trays=int(max_oven_trays),
            fixed_overhead=fetch_overhead_config().fixed_daily_overhead_php,
        )
        summary_table, comparison_table = scenario_tables(results)
        profit_chart, price_chart = generate_pricing_scenario_charts(results)

        if resolved_goal == "Reach target profit":
            goal_status = (
                f"Target of ₱{target:,.2f} reached."
                if results["goal_reached"]
                else f"Target of ₱{target:,.2f} is not reachable with these inputs and limits. "
                     "Showing the best feasible profit scenario."
            )
        elif resolved_goal == "Break even":
            goal_status = (
                "A non-negative net-profit scenario is available."
                if results["goal_reached"]
                else "Every feasible scenario is below break-even; showing the least-loss option."
            )
        elif resolved_goal == "Maximize units sold" and not results["goal_reached"]:
            goal_status = (
                "No non-loss-making scenario is available; showing the highest-profit option."
            )
        else:
            goal_status = "The listed scenarios satisfy the selected goal."

        scenario_payload = [
            {
                "name": scenario["label"],
                "net_profit_php": scenario["net_profit"],
                "revenue_php": scenario["revenue"],
                "promotion_cost_php": scenario["promotion_cost"],
                "units_sold_estimate": scenario["units_sold"],
                "trays": scenario["trays"],
                "products": [
                    {
                        "product": item["Product"],
                        "input_price_php": item["current_price"],
                        "suggested_price_php": option["price"],
                        "input_demand_units": item["base_demand"],
                        "estimated_demand_units": option["demand"],
                        "assumed_demand_uplift_pct": round(option["uplift"] * 100, 1),
                        "promotion_cost_php": option["promotion_cost"],
                        "trays": option["trays"],
                    }
                    for item, option in scenario["selected"]
                ],
            }
            for scenario in results["scenarios"]
        ]
        ai_explanation = explain_pricing_scenarios(
            user_goal=ai_prompt.strip() if ai_prompt else resolved_goal,
            scenarios=scenario_payload,
        )

        extracted = (
            json.dumps(parsed_target.model_dump(mode="json"), indent=2, ensure_ascii=False)
            if parsed_target is not None
            else "No natural-language goal was entered."
        )
        if notices:
            goal_status = " ".join(notices) + " " + goal_status
        return (
            goal_status,
            summary_table,
            comparison_table,
            effective_inputs,
            profit_chart,
            price_chart,
            ai_explanation,
            extracted,
        )
    except Exception as error:
        message = f"Could not calculate recommendations: {error}"
        return (
            message,
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            None,
            None,
            message,
            "",
        )


default_inputs = build_default_pricing_inputs()
default_tray_limit = fetch_overhead_config().max_deck_tray_capacity

with gr.Blocks(title="PanaderyaOptimizer | Pricing Scenarios") as demo:
    gr.Markdown(
        """
# PanaderyaOptimizer
### Bakery pricing and production scenarios
Edit the **inputs**, choose which assumptions must stay fixed, then compare them with
several calculated **outputs**. Estimates are scenarios, not guaranteed sales forecasts.
"""
    )

    with gr.Tabs():
        with gr.Tab("1 · Inputs"):
            gr.Markdown(
                "### Business goal\n"
                "Choose what to optimize. Target profit means **daily net profit after "
                "variable costs and fixed overhead**."
            )
            with gr.Row():
                business_goal = gr.Dropdown(
                    choices=[
                        "Interpret goal from prompt",
                        "Maximize daily profit",
                        "Break even",
                        "Reach target profit",
                        "Maximize units sold",
                    ],
                    value="Interpret goal from prompt",
                    label="What result do you want?",
                )
                target_profit = gr.Number(
                    label="Target daily net profit (PHP)",
                    value=None,
                    precision=2,
                    minimum=0,
                )
                max_oven_trays = gr.Number(
                    label="Maximum oven trays per day",
                    value=default_tray_limit,
                    precision=0,
                    minimum=1,
                )

            gr.Markdown(
                """
### Product assumptions — edit the cells
Costs, prices, competitor references, demand, and elasticity are editable. Elasticity
must be zero or negative: **-1.0** means a 1% price increase implies about a 1%
demand decrease in this simplified model. Demand-uplift options are hypothetical and
only included when a positive promotion budget is entered; that full budget is charged
to each uplift scenario. The app cannot guarantee the assumed uplift will happen.

- **Lock Price**: keep the current price fixed.
- **Target Markup (%)**: a candidate target; when **Lock Markup** is checked, suggested
  price adjusts with unit cost to preserve that percentage. Choose this *or* Lock Price,
  not both.
- **Lock Demand**: use the entered demand even when price changes.
- Competitor price is a reference and candidate price point; it does not predict
  competitor response or market share.
"""
            )
            product_inputs = gr.Dataframe(
                value=default_inputs,
                headers=[
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
                ],
                datatype=[
                    "str", "number", "number", "number", "number", "number",
                    "number", "number", "bool", "bool", "bool",
                ],
                type="pandas",
                interactive=True,
                label="Editable pricing and demand inputs",
                static_columns=[0],
                column_widths=[
                    "12%", "9%", "10%", "8%", "10%", "11%",
                    "8%", "10%", "7%", "7%", "8%",
                ],
            )

            ai_prompt = gr.Textbox(
                label="Optional AI goal in plain language",
                placeholder=(
                    "Example: Break even today, keep Pan de Sal markup fixed, "
                    "and use no more than 8 trays."
                ),
                lines=2,
            )
            gr.Markdown(
                "AI can extract a stated profit target, demand, and oven limit, then "
                "explain the computed choices. It does not calculate prices or promise demand."
            )
            run_button = gr.Button("Calculate and compare scenarios", variant="primary")

        with gr.Tab("2 · Outputs"):
            status_output = gr.Markdown(
                "Submit the input form to see recommendations and comparisons."
            )
            gr.Markdown("### Scenario comparison")
            summary_output = gr.Dataframe(
                interactive=False,
                label="Daily outcome by scenario",
                wrap=True,
            )
            gr.Markdown(
                "### Input vs. suggested values\n"
                "The input price, markup, and demand are shown beside each scenario's "
                "suggested values. Estimated demand is driven by the entered elasticity "
                "and explicitly assumed demand uplift."
            )
            comparison_output = gr.Dataframe(
                interactive=False,
                label="Product-level comparison",
                wrap=True,
            )
            with gr.Row():
                profit_chart_output = gr.Plot(label="Estimated profit scenarios")
                price_chart_output = gr.Plot(label="Input versus suggested prices")
            input_snapshot_output = gr.Dataframe(
                interactive=False,
                label="Inputs used for these results",
                wrap=True,
            )
            with gr.Accordion("AI explanation and extracted constraints", open=True):
                ai_explanation_output = gr.Markdown()
                extracted_output = gr.Code(language="json", label="Parsed goal")

    run_button.click(
        fn=run_optimizer,
        inputs=[
            business_goal,
            target_profit,
            max_oven_trays,
            product_inputs,
            ai_prompt,
        ],
        outputs=[
            status_output,
            summary_output,
            comparison_output,
            input_snapshot_output,
            profit_chart_output,
            price_chart_output,
            ai_explanation_output,
            extracted_output,
        ],
    )


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", share=False)
