import subprocess
import sys
from pathlib import Path

import streamlit as st


PROJECT_FOLDER = Path(__file__).resolve().parent
AGENT_FILE = PROJECT_FOLDER / "agent_metrics.py"
EXPLANATION_MARKER = "Model explanation — check against the tool result:"


st.set_page_config(page_title="Data Investigation Agent")
st.title("Data Investigation Agent")
st.caption("Ask about sales metrics or compare revenue across categories.")

with st.form("sales_question"):
    question = st.text_area(
        "Sales question",
        placeholder="Which categories contributed to the revenue drop "
        "from August to September 2026?",
    )
    submitted = st.form_submit_button("Investigate")

if submitted:
    question = question.strip()

    if not question:
        st.warning("Enter a sales question first.")
        st.stop()

    try:
        with st.spinner("Running the investigation..."):
            run = subprocess.run(
                [sys.executable, str(AGENT_FILE)],
                input=question + "\n",
                text=True,
                capture_output=True,
                cwd=PROJECT_FOLDER,
                timeout=270,
            )
    except subprocess.TimeoutExpired:
        st.error("The investigation timed out. Check Ollama and try again.")
        st.stop()

    details, marker, explanation = run.stdout.partition(EXPLANATION_MARKER)

    if run.returncode != 0:
        st.error("The investigation stopped. See the details below.")
    elif marker:
        st.subheader("Model explanation")
        st.markdown(explanation.strip())
    else:
        st.warning("The agent did not return a completed investigation.")

    with st.expander("Calculation and evidence", expanded=not bool(marker)):
        diagnostic_output = "\n".join(
            part.strip() for part in (details, run.stderr) if part.strip()
        )
        st.code(diagnostic_output or "No details returned.", language="text")