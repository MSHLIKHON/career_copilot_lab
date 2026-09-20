"""Practice workspace page (code editor, tests runner, hints, feedback)."""

import pandas as pd
import streamlit as st

from core import storage
from core.adaptive import recommend
from core.model import load_model, predict
from core.runner import run_tests
from core.tasks import TASK_BY_ID


def show_result(attempt: dict, uid: int) -> None:
    result, prediction = attempt["result"], attempt["prediction"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Tests passed", f"{result['passed']} / {result['total']}")
    c2.metric("Hints viewed", attempt["hints"])
    c3.metric(
        "Attempt type",
        "Assisted" if attempt["hints"] or attempt["solution_seen"] else "Independent",
    )
    if result["status"] == "passed":
        st.success("All task tests passed. Evidence saved to your account.")
    elif result["message"]:
        st.error(result["message"])
    else:
        st.warning("Some tests failed. Compare the expected and actual results below.")
    st.markdown("**Feedback:** " + prediction["label"].replace("_", " ").title())
    st.write(prediction["message"])
    if prediction.get("score") is not None:
        st.caption(
            f"Model score: {prediction['score']:.2f}. This is not a validated probability that the diagnosis is correct."
        )
    if result["cases"]:
        rows = [
            {
                "Case": c["note"],
                "Input": repr(c["args"]),
                "Expected": repr(c["expected"]),
                "Actual": repr(c["actual"]),
                "Result": "PASS" if c["passed"] else "FAIL",
                "Error": c["error"],
            }
            for c in result["cases"]
        ]
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


def render_practice(user: dict, history: list, profile: dict, go_to_task_cb) -> None:
    uid = user["id"]
    st.caption("CODING WORKSPACE")
    st.title("Practice Python")
    st.write("Write a function named solve. Return your answer; do not use input() or print().")
    task_id = st.selectbox(
        "Choose a task",
        list(TASK_BY_ID),
        format_func=lambda k: f"{k} · {TASK_BY_ID[k]['title']} / {TASK_BY_ID[k]['topic']} / Level {TASK_BY_ID[k]['level']}",
        key="task_select",
    )
    task = TASK_BY_ID[task_id]
    st.subheader(task["title"])
    st.write(task["prompt"])
    st.caption(f"Topic: {task['topic']} · Level {task['level']} · {len(task['tests'])} deterministic tests")
    with st.expander("Example inputs and outputs", expanded=False):
        for case in task["tests"][:2]:
            st.code(
                f"solve({', '.join(repr(x) for x in case['args'])}) → {case['expected']!r}",
                language="text",
            )
    editor_key = f"editor_{task_id}"
    if editor_key not in st.session_state:
        st.session_state[editor_key] = task["starter"]
    left, right = st.columns([2.1, 1], gap="large")
    with left:
        if task_id == "L1" and st.button(
            "Load a buggy example",
            help="Replaces this task's editor with an intentional off-by-one example.",
        ):
            st.session_state[editor_key] = (
                "def solve(n):\n    total = 0\n    for i in range(1, n):\n        total += i\n    return total\n"
            )
        code = st.text_area("Your Python code", key=editor_key, height=300, max_chars=12000)
        if st.button("Run tests & save attempt", type="primary", width="stretch"):
            with st.spinner("Checking code and test evidence..."):
                result = run_tests(code, task)
                model, model_error = load_model()
                prediction = predict(code, result, model)
                storage.save_attempt(uid, task_id, code, result, prediction)
            st.rerun()
    with right:
        st.markdown("#### Hint ladder")
        help_used = storage.assistance(uid, task_id)
        st.caption(
            "Hints are saved with your task history. Viewed solutions always mark later attempts on this task as assisted."
        )
        if help_used["hints"] < 3 and st.button("Show next hint", width="stretch"):
            help_used = storage.assistance(uid, task_id, hints=help_used["hints"] + 1)
        for index, hint in enumerate(task["hints"][: help_used["hints"]], 1):
            st.info(f"Hint {index}: {hint}")
        if st.button("Reveal reference solution", width="stretch"):
            help_used = storage.assistance(uid, task_id, solution=True)
        if help_used["solution_seen"]:
            st.code(task["solution"], language="python")
            st.caption("Copy it to practise, but use a new task for independent evidence.")
    current_attempts = [a for a in history if a["task_id"] == task_id]
    if current_attempts:
        st.divider()
        st.subheader("Latest saved attempt for this task")
        show_result(current_attempts[-1], uid)
        st.caption("These results belong to the last submitted code, not unsaved editor changes.")
        next_task, reason = recommend(history, profile["target"])
        st.write(f"**Recommended next:** {next_task['title']}. {reason}")
        if st.button("Open next practice task"):
            go_to_task_cb(next_task["id"])
