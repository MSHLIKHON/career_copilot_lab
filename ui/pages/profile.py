import html
import streamlit as st
import pandas as pd
from datetime import datetime
from core import storage

if hasattr(st, "dialog"):
    @st.dialog("Saved CV Document", width="large")
    def _show_full_cv_modal(cv_text, word_count, char_count):
        st.caption(f"Full Document View &bull; {word_count:,} words &bull; {char_count:,} characters &bull; Private local data")
        escaped_cv = html.escape(cv_text)
        st.markdown(
            f'''<div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:10px; padding:22px 24px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size:13.5px; line-height:1.7; color:#0F172A; opacity:1 !important; white-space:pre-wrap; word-break:break-word; max-height:65vh; overflow-y:auto; box-shadow:inset 0 1px 3px rgba(0,0,0,0.03);">{escaped_cv}</div>''',
            unsafe_allow_html=True
        )
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        col_dl, col_close = st.columns([1, 1])
        with col_dl:
            st.download_button(
                "Download CV (.txt)",
                data=cv_text,
                file_name="saved_cv.txt",
                mime="text/plain",
                use_container_width=True,
                key="modal_cv_download_btn"
            )
        with col_close:
            if st.button("Close Viewer", use_container_width=True, key="modal_cv_close_btn"):
                st.rerun()

def render_profile(uid, user, history, profile):
    st.caption("PRIVATE PROFILE AND ACTIVITY")
    st.title(profile["name"])
    
    joined_date = datetime.fromtimestamp(profile['joined']).strftime('%d %B %Y')
    email = profile['email'] or 'Not provided'
    phone = profile['phone'] or 'Not provided'
    
    st.write(f"**@{profile['username']}** &middot; Member since {joined_date}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    overview_tab, edit_tab = st.tabs(["Overview & Activity", "Edit Profile Details"])
    
    with overview_tab:
        col1, col2 = st.columns([0.85, 1.15], gap="large")
        with col1:
            st.markdown("### Profile & Contact")
            location_val = profile.get("location") or "Not provided"
            education_val = profile.get("education") or "Not provided"
            target_goal = profile.get("target") or "Python foundations"
            claims_count = len(profile.get("claims", []))
            
            st.markdown(f'''
            <div class="feature-card" style="margin-bottom: 14px;">
                <b>Email Address</b>
                <span style="color:#1E293B;">{html.escape(email)}</span><br><br>
                <b>Phone Number</b>
                <span style="color:#1E293B;">{html.escape(phone)}</span><br><br>
                <b>Location</b>
                <span style="color:#1E293B;">{html.escape(location_val)}</span><br><br>
                <b>Learning Goal</b>
                <span style="color:#1E293B;">{html.escape(target_goal)}</span><br><br>
                <b>Verified Skills</b>
                <span style="color:#1E293B;">{claims_count} skill(s) claimed</span>
            </div>
            ''', unsafe_allow_html=True)
            
            if education_val != "Not provided":
                st.markdown(f'''
                <div class="feature-card" style="margin-bottom: 14px;">
                    <b>Education</b>
                    <span style="color:#1E293B;">{html.escape(education_val)}</span>
                </div>
                ''', unsafe_allow_html=True)
            
        with col2:
            st.markdown("### Saved CV")
            cv_text = (profile.get("cv_text") or "").strip()
            if cv_text:
                word_count = len(cv_text.split())
                char_count = len(cv_text)
                
                # Metadata badges row
                st.markdown(f'''
                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:10px;">
                    <span style="background:#EBF2FE; color:#1E40AF; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:600;">{word_count:,} words</span>
                    <span style="background:#F1F5F9; color:#475569; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:500;">{char_count:,} chars</span>
                    <span style="background:#ECFDF5; color:#065F46; padding:3px 10px; border-radius:999px; font-size:12px; font-weight:500;">Private (Local)</span>
                </div>
                ''', unsafe_allow_html=True)
                
                # Controls & actions
                ctrl_col1, ctrl_col2 = st.columns([1, 1], gap="small")
                with ctrl_col1:
                    if hasattr(st, "dialog"):
                        if st.button("Full Screen View", use_container_width=True, key="btn_open_cv_modal", help="Open CV in an expanded modal reader"):
                            _show_full_cv_modal(cv_text, word_count, char_count)
                with ctrl_col2:
                    st.download_button(
                        "Download (.txt)",
                        data=cv_text,
                        file_name="saved_cv.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key="btn_download_cv_profile"
                    )

                # Document preview box with high contrast and crisp typography
                escaped_text = html.escape(cv_text)
                
                st.markdown(f'''
                <div style="background:#FFFFFF; border:1px solid #CBD5E1; border-radius:12px; box-shadow:0 3px 14px rgba(15,23,42,0.06); margin-top:4px; overflow:hidden;">
                    <div style="background:#F8FAFC; border-bottom:1px solid #E2E8F0; padding:8px 14px; display:flex; justify-content:space-between; align-items:center; font-size:11.5px; color:#64748B;">
                        <span><strong>DOCUMENT PREVIEW</strong></span>
                        <span>High contrast &bull; 100% opacity</span>
                    </div>
                    <div style="padding:16px 18px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; font-size:13.5px; line-height:1.68; color:#0F172A; opacity:1 !important; white-space:pre-wrap; word-break:break-word; user-select:text; max-height:360px; overflow-y:auto;">
{escaped_text}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                st.caption("Need to update or re-upload your CV? Go to **My skills & CV**.")
            else:
                st.info("No CV saved yet. Upload a PDF or paste your CV text in **My skills & CV** to enable ATS matching.")
                if st.button("Go to My skills & CV", key="btn_goto_skills_cv"):
                    st.session_state.pending_page = "My skills & CV"
                    st.rerun()

        st.divider()
        st.markdown("### Complete Activity History")
        activity_rows = storage.activity(uid)
        if activity_rows:
            activity_table = [{"When": datetime.fromtimestamp(row["created"]).strftime("%Y-%m-%d %H:%M:%S"),
                               "Activity": row["event"].replace("_", " ").title(),
                               "Details": row["details"]} for row in activity_rows]
            st.dataframe(pd.DataFrame(activity_table), hide_index=True, width="stretch")
        else:
            st.info("No activity recorded yet.")

    with edit_tab:
        st.markdown("### Update Your Information")
        with st.form("profile_details"):
            col_personal, col_prof = st.columns(2, gap="large")
            
            with col_personal:
                st.markdown("**Personal Information**")
                new_name = st.text_input("Display name", value=profile["name"], max_chars=80)
                new_email = st.text_input("Email address", value=profile["email"], max_chars=254)
                new_phone = st.text_input("Phone number", value=profile["phone"], max_chars=24)
                new_password = st.text_input("New password", type="password", placeholder="Leave blank to keep current password", max_chars=128)
                
            with col_prof:
                st.markdown("**Professional Details**")
                location = st.text_input("Location", value=profile["location"], max_chars=120)
                education = st.text_area("Education", value=profile["education"], max_chars=500, height=100)
                about = st.text_area("About me", value=profile["about"], max_chars=2000, height=140)
                
            st.markdown("<br>", unsafe_allow_html=True)
            save_details = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
            
        if save_details:
            try:
                # Update account (users table)
                storage.update_account_details(
                    user_id=uid,
                    name=new_name,
                    email=new_email,
                    phone=new_phone,
                    new_password=new_password if new_password else None
                )
                
                # Update profile (profiles table)
                storage.save_profile(uid, profile["claims"], profile["target"], location, education,
                                     about, profile["cv_text"])
                
                # Update session state with new details
                st.session_state.user["name"] = new_name
                st.session_state.user["email"] = new_email
                st.session_state.user["phone"] = new_phone
                
                st.success("Profile details saved successfully!")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
