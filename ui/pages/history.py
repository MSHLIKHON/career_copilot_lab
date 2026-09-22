"""Attempt history and data export page."""

import json
from datetime import datetime
import pandas as pd
import streamlit as st

from core import storage
from core.tasks import TASK_BY_ID
from ui.pages.practice import show_result


def render_history(user: dict, history: list) -> None:
    uid = user["id"]
    st.caption("YOUR SAVED EVIDENCE")
    st.title("Attempt history")
    if not history:
        st.info("No attempts yet. Open Practice to complete your first task.")
    else:
        table = [
            {
                "Attempt": a["id"],
                "Time (local)": datetime.fromtimestamp(a["created"]).strftime("%Y-%m-%d %H:%M"),
                "Task": TASK_BY_ID[a["task_id"]]["title"],
                "Passed tests": f"{a['result']['passed']}/{a['result']['total']}",
                "Status": a["result"]["status"],
                "Hint count": a["hints"],
            }
            for a in reversed(history)
        ]
        st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
        selection = st.selectbox(
            "Inspect attempt",
            list(reversed(range(len(history)))),
            format_func=lambda i: f"#{history[i]['id']} · {TASK_BY_ID[history[i]['task_id']]['title']}",
        )
        st.code(history[selection]["code"], language="python")
        show_result(history[selection], uid)
    st.download_button(
        "Download my full progress (JSON)",
        json.dumps(storage.export_user(uid), indent=2),
        file_name="career_copilot_progress.json",
        mime="application/json",
    )
