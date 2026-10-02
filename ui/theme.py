import streamlit as st

def apply_theme():
    st.markdown('''<style>
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
.stAppDeployButton {display: none !important;}
[data-testid="stHeaderActionElements"] {display: none !important;}
header[data-testid="stHeader"] {background: transparent !important; height: 1.5rem !important; min-height: 1.5rem !important; overflow: visible !important;}
header {background: transparent !important;}
.stApp {background-color: #F8FAFC !important;}
.block-container {max-width: 1140px !important; padding-top: 1.25rem !important; padding-bottom: 3.5rem !important; padding-left: 2rem !important; padding-right: 2rem !important; margin: 0 auto !important;}
h1, h2, h3, h4 {letter-spacing: -0.025em; color: #0F172A;}
h1 {font-size: 2.1rem !important; font-weight: 750 !important; margin-bottom: 0.25rem !important;}
[data-testid="stSidebar"] {border-right: 1px solid #DDE5F1; background-color: #F7F9FD !important;}
[data-testid="stSidebar"] [data-testid="stRadio"] label {padding: 7px 9px; border-radius: 9px;}
[data-testid="stMetric"] {background-color: #FFFFFF !important; border: 1px solid #DEE6F1; border-radius: 14px; padding: 18px; box-shadow: 0 4px 16px rgba(23, 52, 91, 0.04);}
[data-testid="stForm"] {background-color: #FFFFFF !important; border: 1px solid #DEE6F1 !important; border-radius: 14px !important; padding: 18px 20px !important; box-shadow: 0 2px 10px rgba(23, 52, 91, 0.04) !important;}
[data-testid="stDataFrame"] {border: 1px solid #DEE6F1; border-radius: 14px; overflow: hidden;}
.stButton button, .stDownloadButton button, .stLinkButton a {border-radius: 8px !important; font-weight: 600 !important; font-size: 13.5px !important;}
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"] {background-color: #172B50 !important; color: #FFFFFF !important; border: 1px solid #172B50 !important; border-radius: 8px !important; padding: 9px 16px !important; font-weight: 600 !important; font-size: 13.5px !important; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05) !important;}
.stButton button[kind="primary"]:hover, .stFormSubmitButton button[kind="primary"]:hover {background-color: #101E38 !important; border-color: #101E38 !important;}
[data-testid="stTextInput"] input {border-radius: 8px !important; border: 1px solid #CBD5E1 !important; padding: 8px 12px !important; font-size: 13.5px !important; color: #0F172A !important; background-color: #FFFFFF !important;}
[data-testid="stTextInput"] input:focus {border-color: #1E40AF !important; box-shadow: 0 0 0 2px rgba(30, 64, 175, 0.12) !important;}
[data-baseweb="tab-list"] {gap: 6px !important; border-bottom: 1px solid #DEE6F1 !important; margin-bottom: 14px !important;}
[data-baseweb="tab"] {padding: 8px 16px !important; font-weight: 600 !important; font-size: 13.5px !important; color: #52627E !important; border: none !important; border-bottom: none !important; background: transparent !important;}
[data-baseweb="tab"][aria-selected="true"] {color: #17243D !important; border: none !important; border-bottom: none !important;}
[data-testid="stExpander"] {background-color: #FFFFFF !important; border: 1px solid #DEE6F1 !important; border-radius: 12px !important; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03) !important;}
[data-testid="stExpander"] summary {font-weight: 600 !important; color: #17243D !important; font-size: 13.5px !important; padding: 10px 14px !important;}
.intro {background-color: #172B50 !important; color: #FFFFFF !important; padding: 24px 26px !important; border-radius: 14px !important; border: 1px solid #233D6B !important; margin-bottom: 12px !important; box-shadow: 0 4px 14px rgba(23, 43, 80, 0.1) !important;}
.intro h2 {color: #FFFFFF !important; margin: 0 0 8px 0 !important; font-size: 21px !important; font-weight: 700 !important;}
.intro p {margin: 0 !important; color: #D6E4F7 !important; font-size: 13.5px !important; line-height: 1.6 !important;}
.feature-grid {display: flex !important; flex-direction: column !important; gap: 9px !important; margin: 0 0 12px !important;}
.feature-card {background-color: #FFFFFF !important; border: 1px solid #DEE6F1 !important; border-radius: 12px !important; padding: 12px 15px !important; color: #334155 !important; font-size: 13px !important; line-height: 1.45 !important; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03) !important;}
.feature-card b {display: block !important; color: #17345B !important; margin-bottom: 3px !important; font-size: 13.5px !important; font-weight: 700 !important;}
.privacy-badge {display: flex !important; align-items: center !important; gap: 8px !important; padding: 9px 13px !important; background-color: #F1F5F9 !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; font-size: 12px !important; color: #475569 !important; font-weight: 500 !important;}
.privacy-badge-dot {width: 7px !important; height: 7px !important; background-color: #10B981 !important; border-radius: 50% !important; flex-shrink: 0 !important;}
.eyebrow {display: inline-flex; align-items: center; margin-bottom: 8px; padding: 4px 11px; border: 1px solid #CDDEFB; border-radius: 999px; background-color: #EBF2FE; color: #1E40AF; font-size: 11px; line-height: 1.2; letter-spacing: 0.08em; font-weight: 700;}
.hero-subtitle {font-size: 15px; color: #475569; line-height: 1.5; margin: 0 0 20px 0;}
.auth-heading {font-size: 18px; font-weight: 700; color: #17243D; line-height: 1.25; margin: 4px 0 2px;}
.auth-subheading {font-size: 13.5px; color: #52627E; line-height: 1.4; margin: 0 0 14px;}
.specs-header {margin: 28px 0 14px; padding-top: 20px; border-top: 1px solid #DEE6F1;}
.specs-tag {display: inline-block; font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #52627E; margin-bottom: 2px;}
.specs-header h4 {margin: 0; font-size: 16px; font-weight: 700; color: #17243D;}
.profile-strip {display: flex; justify-content: space-between; align-items: center; gap: 18px; padding: 14px 18px; margin: 0 0 22px; border: 1px solid #D4E0F0; border-radius: 14px; background-color: #FFFFFF !important; color: #17243D; box-shadow: 0 2px 8px rgba(23, 52, 91, 0.04);}
.profile-strip strong {font-size: 17px;}
.profile-strip span {color: #60708A; font-size: 13px; text-align: right;}
@media (max-width: 768px) {
    .block-container {padding-top: 1rem !important; padding-left: 1rem !important; padding-right: 1rem !important;}
    .eyebrow {font-size: 10px;}
    .profile-strip {align-items: flex-start; flex-direction: column; gap: 3px;}
    .profile-strip span {text-align: left;}
    .intro {padding: 18px !important;}
    .intro h2 {font-size: 19px !important;}
}
</style>''', unsafe_allow_html=True)
