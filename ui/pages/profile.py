import streamlit as st
import pandas as pd
from datetime import datetime
from core import storage

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
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.markdown("### Contact Info")
            st.markdown(f'''
            <div class="feature-card" style="margin-bottom: 20px;">
                <b>Email Address</b>
                {email}<br><br>
                <b>Phone Number</b>
                {phone}
            </div>
            ''', unsafe_allow_html=True)
            
        with col2:
            st.markdown("### Saved CV")
            if profile["cv_text"]:
                with st.expander("View Saved CV Text", expanded=False):
                    st.text_area("CV Content", value=profile["cv_text"], height=180, disabled=True, label_visibility="collapsed")
                    st.caption("Update this CV from My skills & CV. The saved text is private to this local account.")
            else:
                st.info("No CV saved yet. Open My skills & CV to paste or upload one.")

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
