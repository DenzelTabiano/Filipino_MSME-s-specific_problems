# PanaderyaOptimizer

A local web app prototype for Filipino bakeries to compare product prices, cost-based
markups, demand assumptions, and daily production plans. The dashboard separates the
editable assumptions from the calculated scenario results.

## What it currently does

- Starts with sample recipes and prices for Pan de Sal, Spanish Bread, and Ensaymada
  stored in a local SQLite database.
- Lets a user edit unit cost, current selling price, markup, competitor reference price,
  daily base demand, and price elasticity in the **Inputs** tab.
- Supports locking price, markup, or demand for each product. A price and markup lock
  cannot both be selected for the same product.
- Calculates scenarios for maximizing daily profit, breaking even, reaching a net
  profit target, or maximizing units sold.
- Observes the oven tray limit, estimates discrete tray production, and compares input
  assumptions with recommended scenario values. The optional natural-language goal can
  be interpreted by AI; the form also supports selecting the goal directly.
- Shows summary and product-level tables, price/profit charts, and an optional AI
  explanation when a Gemini API key is configured.

## Important: how to interpret recommendations

This is a scenario calculator, not a demand-forecasting system. It does not have bakery
sales history, competitor behavior, or locally measured price sensitivity. Each product
starts with a price elasticity of `-1.0`, which is an editable assumption: a 1% price
increase implies about a 1% demand decrease in the model. Estimated demand is calculated
as:

```text
base demand × (scenario price / current price) ^ price elasticity
            × (1 + assumed demand uplift)
```

For unlocked demand, the scenario search tests demand uplift assumptions of 0%, 20%,
50%, and 100% **only when a positive daily promotion budget is entered**; the full
entered budget is charged to every scenario that assumes an uplift. An uplift is still
a hypothetical outcome that might require promotion, distribution, or other action;
the software cannot make it happen or guarantee it. Competitor price is used as a
comparison and candidate price point only. The app does not infer market share or
competitor responses.

Markup is measured on cost: `(price - unit cost) / unit cost`. For example, a 20%
markup means `price = cost × 1.20`; this is not the same as a 20% gross margin.
The **Target Markup (%)** field defines a cost-based candidate markup. Locking markup
keeps that percentage and calculates the corresponding price from unit cost. Locking
price keeps the current price fixed. Locking demand prevents the model from changing
estimated demand.

Production is rounded to whole trays and limited by the oven capacity entered for the
day. Daily net profit subtracts variable product costs, configured fixed overhead, and
the promotion budget when a scenario assumes demand uplift. The starter database values
are examples and should be replaced with each bakery's
actual recipe quantities, ingredient costs, prices, demand, and overhead before relying
on the results. Competitor prices and user-entered business data are not saved by the
app; recipes, starter costs, prices, and overhead are stored locally in SQLite.

Gemini is used only to parse a natural-language goal and explain calculated scenarios.
The deterministic calculator is the source of scenario figures. When a Gemini API key
is configured, the natural-language goal and scenario summary are sent to Google's
Gemini API for those functions. Without a key, the app can still calculate scenarios
and shows a notice that the AI explanation is unavailable; the local heuristic parser
can extract some simple goals.

## Requirements

- Python 3.10 or later
- Internet access and a Google Gemini API key for AI interpretation/explanation
  (scenario calculation itself runs locally)

## Run locally

### Windows PowerShell

```powershell
git clone https://github.com/DenzelTabiano/PanaderyaOptimizer_TeamPowerhouse.git
cd PanaderyaOptimizer_TeamPowerhouse
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

To enable Gemini, create a `.env` file in the project folder:

```text
GEMINI_API_KEY=your_actual_api_key_here
```

Keep the key private and do not commit `.env`. Start the web app:

```powershell
python app.py
```

Open [http://127.0.0.1:7860](http://127.0.0.1:7860). Press **Ctrl+C** in the terminal
to stop it.

### macOS / Linux

```bash
git clone https://github.com/DenzelTabiano/PanaderyaOptimizer_TeamPowerhouse.git
cd PanaderyaOptimizer_TeamPowerhouse
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create the same `.env` file if using Gemini, then run `python app.py` and visit
`http://127.0.0.1:7860`.

## Current scope and planned validation

The product list and recipe model are currently limited to products present in the
SQLite database. The app does not yet learn elasticity from actual sales, manage
historical competitor prices, persist user-edited daily assumptions, or execute
marketing actions. Treat recommendations as decision-support scenarios and verify
inputs and outputs with the bakery's own records.
