import json
import pandas as pd
import streamlit as st
from datetime import datetime
from core import storage
from core.tasks import TASK_BY_ID
from ui.components import show_result

def render_history(uid, history):
    st.caption("YOUR SAVED EVIDENCE")
    st.title("Attempt history")
    if not history:
        st.info("No attempts yet. Open Practice to complete your first task.")
    else:
        passed_count = sum(1 for a in history if a["result"]["status"] == "passed")
        failed_count = len(history) - passed_count
        status_labels = {
            "All": f"All ({len(history)})",
            "Passed": f"Passed ({passed_count})",
            "Failed": f"Failed ({failed_count})",
        }

        attempted_task_ids = [tid for tid in TASK_BY_ID if any(a["task_id"] == tid for a in history)]
        extra_tids = sorted({a["task_id"] for a in history if a["task_id"] not in TASK_BY_ID})
        attempted_task_ids.extend(extra_tids)

        def format_task(tid):
            if tid == "All":
                return f"All tasks ({len(history)})"
            count = sum(1 for a in history if a["task_id"] == tid)
            title = TASK_BY_ID.get(tid, {}).get("title", tid)
            return f"{tid} · {title} ({count})"

        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox(
                "Filter by status",
                ["All", "Passed", "Failed"],
                format_func=lambda s: status_labels.get(s, s),
                key="history_status_filter",
            )
        with col2:
            task_filter = st.selectbox(
                "Filter by task",
                ["All"] + attempted_task_ids,
                format_func=format_task,
                key="history_task_filter",
            )

        filtered = history
        if status_filter == "Passed":
            filtered = [a for a in filtered if a["result"]["status"] == "passed"]
        elif status_filter == "Failed":
            filtered = [a for a in filtered if a["result"]["status"] != "passed"]

        if task_filter != "All":
            filtered = [a for a in filtered if a["task_id"] == task_filter]

        if not filtered:
            st.info("No attempts match the selected filters.")
        else:
            if len(filtered) < len(history):
                st.caption(f"Showing {len(filtered)} of {len(history)} attempts")

            table = [
                {
                    "Attempt": a["id"],
                    "Time (local)": datetime.fromtimestamp(a["created"]).strftime("%Y-%m-%d %H:%M"),
                    "Task": TASK_BY_ID.get(a["task_id"], {}).get("title", a["task_id"]),
                    "Passed tests": f"{a['result']['passed']}/{a['result']['total']}",
                    "Status": a["result"]["status"],
                    "Hint count": a["hints"],
                    "Solution viewed": bool(a["solution_seen"]),
                }
                for a in reversed(filtered)
            ]
            st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")

            attempt_by_id = {a["id"]: a for a in filtered}
            attempt_ids = [a["id"] for a in reversed(filtered)]
            selection_id = st.selectbox(
                "Inspect attempt",
                attempt_ids,
                format_func=lambda aid: f"#{aid} · {TASK_BY_ID.get(attempt_by_id[aid]['task_id'], {}).get('title', attempt_by_id[aid]['task_id'])}",
                key="history_inspect_select",
            )
            selected_attempt = attempt_by_id[selection_id]
            st.code(selected_attempt["code"], language="python")
            show_result(selected_attempt, uid)

    st.download_button(
        "Download my full progress (JSON)",
        json.dumps(storage.export_user(uid), indent=2),
        file_name="career_copilot_progress.json",
        mime="application/json",
    )
