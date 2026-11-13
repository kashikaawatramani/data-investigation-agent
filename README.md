# Data Investigation Agent

A local sales analytics assistant built with Python, SQLite, Streamlit, and Ollama. Ask a sales question in plain English. The model selects an analysis tool, Python checks the data and calculates the result, and the app displays the explanation alongside the calculation and evidence ID.

The demo uses synthetic data covering May–October 2026, with 10,140 orders and 20,339 order items.

## Run locally

From the project folder, with Ollama running and `qwen2.5:0.5b` installed:

```bash
source .venv/bin/activate
python3 -m pip install streamlit
python3 -m streamlit run app.py
```

These commands assume you have already created `.venv` and built `sales_demo.db`. Open the Local URL printed in the terminal.

## Try the demo

Ask: “Which product categories contributed to the revenue drop from August to September 2026? Use previous_start 2026-08-01, current_start 2026-09-01, and current_end 2026-10-01.”

Expected: Electronics fell by INR 55,614,000 and Furniture fell by INR 9,696,000, for a total decline of INR 65,310,000. Open **Calculation and evidence** to see the tool output and evidence ID.

## Run the tests

```bash
python3 -m unittest -v test_investigation test_data_quality test_runner
```

## Current scope

The agent handles one tool call per question. It supports sales metrics for a single period and category comparisons between adjacent periods. Explicit dates can help if the local model misreads a period. Requests for incomplete dates are blocked. Check the model’s explanation against the calculated result.