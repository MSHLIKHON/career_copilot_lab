import streamlit as st
import pandas as pd
from datetime import datetime
from core import storage

def render_profile(uid, user, history, profile):
    st.caption("PRIVATE PROFILE AND ACTIVITY")
    st.title(profile["name"])
    contact, progress_col = st.columns([1.25, 1], gap="large")
    with contact:
        st.write(f"**Username:** @{profile['username']}")
        st.write(f"**Email:** {profile['email'] or 'Not provided'}")
        st.write(f"**Phone:** {profile['phone'] or 'Not provided'}")
        st.write(f"**Member since:** {datetime.fromtimestamp(profile['joined']).strftime('%d %B %Y')}")
    with progress_col:
        passed = {a["task_id"] for a in history if a["result"]["status"] == "passed"}
        st.metric("Practice attempts", len(history))
        st.metric("Tasks passed", len(passed))

    with st.form("profile_details"):
        location = st.text_input("Location", value=profile["location"], max_chars=120)
        education = st.text_area("Education", value=profile["education"], max_chars=500, height=90)
        about = st.text_area("About me", value=profile["about"], max_chars=2000, height=120)
        save_details = st.form_submit_button("Save profile details", type="primary")
    if save_details:
        storage.save_profile(uid, profile["claims"], profile["target"], location, education,
                             about, profile["cv_text"])
        st.success("Profile details saved.")
        st.rerun()

    st.subheader("Saved CV")
    if profile["cv_text"]:
        st.text_area("Saved CV text", value=profile["cv_text"], height=180, disabled=True)
        st.caption("Update this CV from My skills & CV. The saved text is private to this local account.")
    else:
        st.info("No CV saved yet. Open My skills & CV to paste or upload one.")

    st.subheader("Complete activity history")
    activity_rows = storage.activity(uid)
    if activity_rows:
        activity_table = [{"When": datetime.fromtimestamp(row["created"]).strftime("%Y-%m-%d %H:%M:%S"),
                           "Activity": row["event"].replace("_", " ").title(),
                           "Details": row["details"]} for row in activity_rows]
        st.dataframe(pd.DataFrame(activity_table), hide_index=True, width="stretch")
    else:
        st.info("No activity recorded yet.")
