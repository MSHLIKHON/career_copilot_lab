import streamlit as st
from core import storage
from core.tasks import TASK_BY_ID
from core.runner import run_tests
from core.model import load_model, predict
from core.adaptive import practice_progress, recommend, HINT_UNLOCKS, SOLUTION_UNLOCK
from ui.components import show_result, go_to_task

def render_practice(uid, history, profile):
    st.caption("CODING WORKSPACE")
    st.title("Deliberate Python practice")
    st.write("Solve precise programming contracts, learn from test evidence, and earn help through meaningful retries.")
    task_id = st.selectbox("Choose a task", list(TASK_BY_ID), format_func=lambda k: f"{k} · {TASK_BY_ID[k]['title']} / {TASK_BY_ID[k]['topic']} / Level {TASK_BY_ID[k]['level']}", key="task_select")
    task = TASK_BY_ID[task_id]
    current_attempts = [a for a in history if a["task_id"] == task_id]
    progress = practice_progress(history, task)
    st.subheader(task["title"])
    st.write(task["prompt"])
    difficulty = {1: "Foundation", 2: "Applied", 3: "Challenge"}[task["level"]]
    st.caption(f"{task['topic']} · Level {task['level']} ({difficulty}) · {len(task['tests'])} deterministic checks")
    contract, evidence, support = st.columns(3)
    contract.metric("Required function", task["starter"].splitlines()[0])
    evidence.metric("Best test evidence", f"{progress['best_passed']} / {progress['total_tests']}")
    support.metric("Distinct failed approaches", progress["distinct_failed"])
    with st.expander("Task contract and submission rules", expanded=True):
        st.markdown(f"""
- Keep the exact signature: `{task['starter'].splitlines()[0]}`
- Return the required value; do not use `input()` or `print()`.
- Handle every boundary stated in the task, not only the visible example.
- Your return type must match exactly; for example, `True` is different from `"True"`.
- Re-submitting identical failed code does not unlock help.
""")
    with st.expander("One public example", expanded=False):
        case = task["tests"][0]
        st.code(f"solve({', '.join(repr(x) for x in case['args'])}) → {case['expected']!r}", language="text")
        st.caption("Other checks include boundary and edge cases. Their inputs are revealed only in saved test evidence.")
    notice_key = f"practice_notice_{task_id}"
    if notice_key in st.session_state:
        st.info(st.session_state.pop(notice_key))
    editor_key = f"editor_{task_id}"
    if editor_key not in st.session_state:
        st.session_state[editor_key] = task["starter"]
    left, right = st.columns([2.1, 1], gap="large")
    with left:
        code = st.text_area("Your Python code", key=editor_key, height=300, max_chars=12000)
        if st.button("Run tests & save attempt", type="primary", width="stretch"):
            with st.spinner("Checking code and test evidence..."):
                result = run_tests(code, task)
                model, model_error = load_model()
                prediction = predict(code, result, model, model_error)
                storage.save_attempt(uid, task_id, code, result, prediction)
                previous_failures = {a["code"].strip() for a in current_attempts if a["result"]["status"] != "passed"}
                if result["status"] == "passed":
                    st.session_state[notice_key] = "All checks passed. Try the recommended task next without assistance."
                elif code.strip() in previous_failures:
                    st.session_state[notice_key] = "Saved, but identical failed code does not count as a new approach. Change your logic before retrying."
                else:
                    st.session_state[notice_key] = "New approach recorded. Use the failed cases to revise one specific part of your logic."
            st.rerun()
    with right:
        st.markdown("#### Earned support")
        help_used = storage.assistance(uid, task_id)
        st.caption("Hints unlock only after distinct failed approaches. Viewed help permanently marks later attempts on this task as assisted.")
        next_hint = help_used["hints"] + 1
        if next_hint <= len(HINT_UNLOCKS):
            required = HINT_UNLOCKS[next_hint - 1]
            remaining = max(0, required - progress["distinct_failed"])
            label = f"Show hint {next_hint}" if not remaining else f"Hint {next_hint}: {remaining} more approaches"
            if st.button(label, width="stretch", disabled=remaining > 0):
                storage.assistance(uid, task_id, hints=next_hint)
                st.rerun()
        else:
            st.success("All three hints have been unlocked.")
        for index, hint in enumerate(task["hints"][:help_used["hints"]], 1):
            st.info(f"Hint {index}: {hint}")
        solution_remaining = max(0, SOLUTION_UNLOCK - progress["distinct_failed"])
        solution_label = "Reveal reference solution" if not solution_remaining else f"Solution: {solution_remaining} more approaches"
        if st.button(solution_label, width="stretch", disabled=solution_remaining > 0):
            storage.assistance(uid, task_id, solution=True)
            st.rerun()
        if help_used["solution_seen"]:
            st.code(task["solution"], language="python")
            st.caption("Study the decisions, then solve a different task without help for independent evidence.")
        elif solution_remaining:
            st.caption(f"Reference solution unlocks after {SOLUTION_UNLOCK} distinct failed approaches.")
    if current_attempts:
        st.divider()
        st.subheader("Latest saved attempt for this task")
        show_result(current_attempts[-1], uid)
        st.caption("These results belong to the last submitted code, not unsaved editor changes.")
        next_task, reason = recommend(history, profile["target"])
        st.write(f"**Recommended next:** {next_task['title']}. {reason}")
        if st.button("Open next practice task"):
            go_to_task(next_task["id"])
