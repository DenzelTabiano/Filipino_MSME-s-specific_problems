import matplotlib.pyplot as plt
import pandas as pd
from typing import List
from schema import ItemBatchYieldMetrics, BakeryOptimizationSummary

# Set clean aesthetic style for Matplotlib charts
plt.style.use("ggplot")


def generate_revenue_breakdown_chart(summary: BakeryOptimizationSummary) -> plt.Figure:
    """
    Generates a grouped horizontal bar chart comparing Expected Gross Revenue
    vs. Total Variable Costs per baked item.
    """
    items: List[ItemBatchYieldMetrics] = summary.items

    names = [item.item_name for item in items]
    revenues = [item.expected_revenue for item in items]
    costs = [item.total_variable_cost for item in items]

    df = pd.DataFrame({
        "Item": names,
        "Gross Revenue (₱)": revenues,
        "Variable Cost (₱)": costs
    })

    fig, ax = plt.subplots(figsize=(7, 3.5), dpi=100)

    y_positions = range(len(names))
    bar_height = 0.35

    ax.barh(
        [y - bar_height / 2 for y in y_positions],
        df["Gross Revenue (₱)"],
        height=bar_height,
        label="Gross Revenue (₱)",
        color="#2e7d32"
    )
    ax.barh(
        [y + bar_height / 2 for y in y_positions],
        df["Variable Cost (₱)"],
        height=bar_height,
        label="Variable Cost (₱)",
        color="#c62828"
    )

    ax.set_yticks(list(y_positions))
    ax.set_yticklabels(names, fontweight="bold")
    ax.set_xlabel("Amount in PHP (₱)", fontsize=9)
    ax.set_title("Revenue vs. Variable Cost Breakdown per Product", fontsize=11, fontweight="bold", pad=10)
    ax.legend(loc="lower right")
    ax.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    return fig


def generate_tray_allocation_pie_chart(summary: BakeryOptimizationSummary) -> plt.Figure:
    """
    Generates a pie chart displaying the distribution of deck oven trays (*planchas*)
    allocated across baked goods.
    """
    items: List[ItemBatchYieldMetrics] = summary.items

    names = [item.item_name for item in items if item.trays_required > 0]
    trays = [item.trays_required for item in items if item.trays_required > 0]

    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=100)

    if not trays or sum(trays) == 0:
        ax.text(0.5, 0.5, "No Trays Allocated", horizontalalignment='center', verticalalignment='center')
        ax.axis('off')
        return fig

    colors = ["#f57c00", "#1976d2", "#388e3c", "#7b1fa2", "#d32f2f"]

    wedges, texts, autotexts = ax.pie(
        trays,
        labels=names,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors[:len(trays)],
        textprops=dict(color="black")
    )

    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_weight("bold")

    ax.set_title("Deck Oven Tray Allocation Breakdown", fontsize=11, fontweight="bold", pad=10)
    plt.tight_layout()
    return fig


def generate_pricing_scenario_charts(results: dict) -> tuple[plt.Figure, plt.Figure]:
    """Compare scenario profit and current versus recommended prices."""
    scenarios = results["scenarios"]
    profit_fig, profit_ax = plt.subplots(figsize=(8, 3.5), dpi=100)
    labels = [scenario["label"] for scenario in scenarios]
    profits = [scenario["net_profit"] for scenario in scenarios]
    colors = ["#2e7d32" if profit >= 0 else "#c62828" for profit in profits]
    profit_ax.barh(labels, profits, color=colors)
    profit_ax.axvline(0, color="#333333", linewidth=0.8)
    profit_ax.set_xlabel("Estimated daily net profit (PHP)")
    profit_ax.set_title("Estimated net profit by scenario")
    profit_ax.grid(axis="x", linestyle="--", alpha=0.4)
    profit_fig.tight_layout()

    goal_scenario = scenarios[0]
    products = [item["Product"] for item, _ in goal_scenario["selected"]]
    current_prices = [item["current_price"] for item, _ in goal_scenario["selected"]]
    suggested_prices = [option["price"] for _, option in goal_scenario["selected"]]
    price_fig, price_ax = plt.subplots(figsize=(8, 3.5), dpi=100)
    positions = list(range(len(products)))
    bar_height = 0.36
    price_ax.barh(
        [position - bar_height / 2 for position in positions],
        current_prices,
        height=bar_height,
        label="Input price",
        color="#1976d2",
    )
    price_ax.barh(
        [position + bar_height / 2 for position in positions],
        suggested_prices,
        height=bar_height,
        label="Goal recommendation",
        color="#f57c00",
    )
    price_ax.set_yticks(positions)
    price_ax.set_yticklabels(products)
    price_ax.set_xlabel("Price (PHP)")
    price_ax.set_title("Input price versus suggested price")
    price_ax.legend()
    price_ax.grid(axis="x", linestyle="--", alpha=0.4)
    price_fig.tight_layout()
    return profit_fig, price_fig


if __name__ == "__main__":
    # Internal visual sanity check using mock optimization output
    mock_summary = BakeryOptimizationSummary(
        total_trays_allocated=10,
        deck_capacity_utilized_pct=83.3,
        gross_revenue=2150.0,
        total_variable_costs=980.0,
        fixed_overhead=300.0,
        net_profit=870.0,
        target_profit_met=False,
        items=[
            ItemBatchYieldMetrics(
                item_name="Pan de Sal",
                true_unit_cost=1.12,
                retail_price=3.00,
                clearance_price=1.80,
                projected_demand_units=180,
                trays_required=6,
                total_supply_units=180,
                morning_expected_sales_units=180,
                surplus_clearance_units=0,
                expected_revenue=540.0,
                total_variable_cost=201.6,
                net_margin_contribution=338.4
            ),
            ItemBatchYieldMetrics(
                item_name="Spanish Bread",
                true_unit_cost=2.45,
                retail_price=7.00,
                clearance_price=4.20,
                projected_demand_units=90,
                trays_required=4,
                total_supply_units=96,
                morning_expected_sales_units=90,
                surplus_clearance_units=6,
                expected_revenue=655.2,
                total_variable_cost=235.2,
                net_margin_contribution=420.0
            )
        ]
    )

    fig1 = generate_revenue_breakdown_chart(mock_summary)
    fig2 = generate_tray_allocation_pie_chart(mock_summary)
    print("Charts generated successfully.")
