# 🥖 PanaderyaOptimizer: Intelligent Batch-Yield, Perishable Decay & Margin Sentinel for Filipino Bakeries
> *Developed for CSSprint 2026: Rooted in Innovation*  
> *University of Santo Tomas — College of Information and Computing Sciences*

---

## 📌 1. Problem Statement & Target Persona

### The Target Persona
Independent community bakeries (*panaderias*), neighborhood pastry shops, and micro-scale bread entrepreneurs across the Philippines who operate on thin margins, fixed-capacity deck ovens, and same-day perishable inventories.

### The Core Pain Point
Over 40,000 neighborhood *panaderias* sustain daily Filipino breakfast and merienda culture. Yet, over 85% of micro-bakers price their products through *gaya-gaya* (unverified neighbor copying) and bake static batch volumes by gut feel. This leads to two compounding operational failures:

1. **The "Plancha" (Sheet Pan) Discrete Batch Bottleneck:**  
   Bakers do not produce units individually; they bake in discrete baking trays (*planchas* of 24–30 pieces). If daily demand is 75 pieces, baking 2 trays (60 pcs) leaves money on the table, while baking 3 trays (90 pcs) creates 15 unsold pieces. Because traditional breads turn stale within 8 to 12 hours, surplus inventory is either discarded or salvaged at a heavy loss, directly bleeding working capital.
2. **Invisible Cost Distortion & Volatile Commodity Spikes:**  
   When the cost of a 25kg flour sack, refined sugar, margarine, or 11kg commercial LPG spikes at the local wet market, bakers maintain static retail prices (e.g., ₱3.00 *pan de sal*). Because their pricing models fail to account for continuous oven preheating fuel, packaging, and the baker's own manual labor, they enter **"profitless volume"**—selling out their trays daily while quietly operating at an unrecovered net loss.

### Sustainable Development Goals (SDG) Alignment
* **SDG 8 (Target 8.3) — Decent Work & Economic Growth:** Promoting formalization and economic viability of micro-food enterprises by equipping unbanked bakers with true unit-cost accounting and viable gross/net margin visibility.
* **SDG 12 (Target 12.3) — Responsible Consumption & Production:** Slashing commercial retail food waste by dynamically equilibrating daily oven tray allocation against expected demand and scheduling afternoon salvage clearance pricing.

---

## 💡 2. Proposed Solution & System Innovation

**PanaderyaOptimizer** replaces static spreadsheets and manual notebooks with an interactive **Batch-Yield & Pricing Intelligence Engine**. It acts as a digital bakery manager that balances perishable shelf-life decay, discrete oven sheet capacities, ingredient price inflation, and user-specified operational objectives.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SYSTEM ARCHITECTURE                             │
├───────────────────────────────────┬────────────────────────────────────┤
│ 🗣️ 1. Conversational Objective    │ 🧮 2. Deterministic Optimization   │
│    Compiler (Gemini API)          │    Engine (Pure Python / logic.py) │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Ingests natural Taglish voice/  │ • Discrete tray-batch ceiling math │
│   text targets from the baker.    │   and oven sheet allocations.      │
│ • Validates inputs and extracts   │ • True Unit Cost calculation       │
│   structured JSON constraints.    │   (Ingredients + LPG + Labor).     │
│ • Fully compliant with Rule C.4.c │ • Margin optimization & afternoon  │
│   (No arithmetic hallucination).  │   clearance markdown schedules.    │
└───────────────────────────────────┴────────────────────────────────────┘
```

### Key Technical Capabilities (MVP)
1. **Conversational Target Compiler:** Non-technical bakers express operational goals in everyday Taglish (e.g., *"Gusto ko maubos ang Spanish bread bago mag-4 PM kahit breakeven lang, pero dapat umabot sa ₱1,200 ang net profit gamit ang Ensaymada at Cheese Bread"*). The AI extracts explicit mathematical constraints without touching arithmetic calculations.
2. **Discrete Tray-Yield Allocator:** Calculates optimal *plancha* production quotas based on maximum deck oven capacity, preventing partial-tray fuel waste.
3. **True Unit-Cost & Shrinkflation Sentinel:** Computes the true baseline cost floor per piece by aggregating raw flour mixes, fat ratios, continuous LPG burn rates, and labor time.
4. **Perishable Decay & Clearance Markdown Engine:** For items with excess supply over expected morning demand, the engine calculates a dynamic afternoon discount tier to liquidate stock above variable cost, eliminating total food waste.

---

## 🤖 3. Artificial Intelligence Justification (Rule C.4.c Compliance)

Section C.4.c of the CSSprint 2026 Handbook strictly penalizes solutions integrating AI without clear necessity. **PanaderyaOptimizer isolates AI strictly to semantic translation and data ingestion:**

* **Why Traditional Code Fails for Input:** Filipino micro-bakers do not formulate business goals as linear programming constraint formulas ($Ax \le b$). Forcing them into rigid numerical parameter sheets creates immediate usability drop-off.
* **Why AI is Necessary:** Natural Language Processing (via Google Gemini) parses conversational, code-switched Taglish inputs, unstructured ingredient delivery notes, and multi-objective business intentions into strict, validated JSON schema representations.
* **Why Deterministic Logic Handles Computation:** Large Language Models are prone to arithmetic hallucination. All batch ceiling calculations, breakeven formulas, margin percentages, and tray distributions are executed exclusively by deterministic Python algorithms in `logic.py`, ensuring 100% mathematical accuracy and defensibility during the Day 3 Technical Q&A.

---

## 🧮 4. Mathematical Model & Optimization Logic

### A. True Unit Cost ($C_i$)
$$\text{Batch Cost}_i = \sum (\text{Ingredient Quantity}_j \times \text{Unit Cost}_j) + \text{Packaging}_i$$
$$C_i = \frac{\text{Batch Cost}_i + \left(\frac{\text{LPG Hourly Rate} \times \text{Bake Time}_i + \text{Labor Alloc}_i}{\text{Total Batches}}\right)}{\text{Units Per Batch}_i}$$

### B. Discrete Tray-Batch Ceiling
$$\text{Trays Required}_i = \left\lceil \frac{\text{Projected Demand}_i}{\text{Tray Capacity}_i} \right\rceil$$
$$\text{Total Production Supply}_i = \text{Trays Required}_i \times \text{Tray Capacity}_i$$

### C. Objective Profit Optimization
$$\text{Max Profit} = \sum_{i} \left[ \min(\text{Supply}_i, \text{Demand}_i) \cdot P_i + \text{Surplus}_i \cdot P_{\text{clearance}, i} \right] - \sum_{i} (\text{Supply}_i \cdot C_i) - \text{Fixed Overhead}$$
$$\text{Subject to: } \sum_{i} \text{Trays Required}_i \le \text{Total Oven Deck Capacity}$$

---

## 🛠️ 5. Technical Architecture & Tech Stack

* **Language:** Python 3.10+
* **Frontend UI Framework:** Gradio Blocks (Clean, responsive web-based operational dashboard with real-time reactive updates)
* **Mathematical Core & Optimization:** Pure Python standard library & Pandas (Deterministic constraint validation and array calculations)
* **Language Intelligence:** Google GenAI SDK (`google-genai` / Gemini 1.5 Flash) with Pydantic structured output schema enforcement
* **Persistence & Baseline Storage:** SQLite3 (Local, lightweight, zero-cloud dependency storing bread master recipes and wet-market commodity cost histories)

---

## ⚙️ 6. Installation & Local Execution

Ensure Python 3.10 or higher is installed on your local machine.

```bash
# 1. Clone the repository
git clone https://github.com/[YOUR-ORGANIZATION-OR-USERNAME]/panaderya-optimizer.git
cd panaderya-optimizer

# 2. Create and activate a clean virtual environment
python -m venv .venv

# Windows (Command Prompt / PowerShell)
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
# Create a .env file and add your Google Gemini API Key:
echo "GEMINI_API_KEY=your_actual_api_key_here" > .env

# 5. Run the application
python app.py
```
Access the application dashboard by opening your browser to `http://127.0.0.1:7860`.

---

## 📈 7. Feasibility, Scalability & Sustainability

* **Deployment Feasibility:** Zero expensive hardware installations required. The application runs seamlessly on entry-level Android smartphones, tablets, or existing shop PCs through standard web browsers.
* **Offline Resilience:** If venue internet connectivity or cellular data drops, the application falls back automatically to local heuristic rule-matching and preset goal dropdowns in `logic.py`, ensuring uninterrupted bakery operations.
* **Commercial Sustainability Model:**
  * **Free Core Tier:** Single-deck community bakeries access daily batch and pricing tools completely free of charge.
  * **Supplier Restock Integration:** Future monetization derives from a modest 1.5% referral commission paid by wholesale flour and lard distributors when bakeries trigger consolidated ingredient restock manifests directly from their production summaries.

---

## 📚 8. Third-Party Resources & Compliance (Rule C.8 Attribution)

In accordance with Section C.8 and C.9 of the CSSprint 2026 Participant Handbook, all third-party libraries and assets are declared below:

* **Gradio:** UI composition framework (Apache-2.0 License)
* **Google GenAI SDK:** AI API interface client (Apache-2.0 License)
* **Pydantic:** Data validation and JSON schema enforcement (MIT License)
* **Pandas:** Tabular data processing and summary structures (BSD-3-Clause License)
* **Python-Dotenv:** Environment key isolation (BSD-3-Clause License)
* **Matplotlib:** Analytical margin visualization charts (PSF / BSD compatible)

---

## 👥 9. Team Composition

* **Earl Cedric C. Relunia** — *Lead Backend Architect & Optimization Logic Engineer*
* **[Member 2 Name]** — *UI/UX Frontend Engineer & System Integrator*
* **[Member 3 Name]** — *Product Strategist & Technical Documentation Lead*
* **[Member 4 Name]** — *Pitch Architect & Video Demonstration Director*
