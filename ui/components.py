import pandas as pd
import streamlit as st
from core import storage

def show_result(attempt, uid):
    result, prediction = attempt["result"], attempt["prediction"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Tests passed", f"{result['passed']} / {result['total']}")
    c2.metric("Hints viewed", attempt["hints"])
    c3.metric("Attempt type", "Assisted" if attempt["hints"] or attempt["solution_seen"] else "Independent")
    if result["status"] == "passed":
        st.success("All task tests passed. Evidence saved to your account.")
    elif result["message"]:
        st.error(result["message"])
    else:
        st.warning("Some tests failed. Compare the expected and actual results below.")
    st.markdown("**Feedback:** " + prediction["label"].replace("_", " ").title())
    st.write(prediction["message"])
    if prediction.get("score") is not None:
        st.caption(f"Model score: {prediction['score']:.2f}. This is not a validated probability that the diagnosis is correct.")
    if result["cases"]:
        rows = [{"Case": c["note"], "Input": repr(c["args"]), "Expected": repr(c["expected"]),
                 "Actual": repr(c["actual"]), "Result": "PASS" if c["passed"] else "FAIL", "Error": c["error"]} for c in result["cases"]]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    with st.expander("Report an incorrect prediction"):
        st.caption("Reports are stored for review, not automatically used as training labels.")
        with st.form(f"feedback_{attempt['id']}"):
            comment = st.text_area("What seems wrong?", max_chars=1000)
            sent = st.form_submit_button("Save feedback")
        if sent:
            try:
                storage.report_prediction(uid, attempt["id"], comment)
                st.success("Feedback saved. Include your account export when sharing it with the team.")
            except ValueError as error:
                st.error(str(error))

def go_to_task(task_id):
    st.session_state.pending_task = task_id
    st.session_state.pending_page = "Practice"
    st.rerun()
