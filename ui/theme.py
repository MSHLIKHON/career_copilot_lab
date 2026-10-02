import streamlit as st

def apply_theme():
    st.markdown('''<style>
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
.stAppDeployButton {display: none !important;}
[data-testid="stHeaderActionElements"] {display: none !important;}
header {background: transparent !important;}
.stApp {background:linear-gradient(145deg,#F8FAFE 0%,#F3F6FC 50%,#F8FAFE 100%)}
.block-container {max-width:1160px;padding-top:3.5rem;padding-bottom:4rem}
h1,h2,h3 {letter-spacing:-.035em}
[data-testid="stSidebar"] {border-right:1px solid #DDE5F1;background:#F7F9FD}
[data-testid="stSidebar"] [data-testid="stRadio"] label {padding:7px 9px;border-radius:9px}
[data-testid="stMetric"] {background:#fff;border:1px solid #DEE6F1;border-radius:16px;padding:18px;
box-shadow:0 7px 24px rgba(23,52,91,.055)}
[data-testid="stForm"] {background:#fff;border:1px solid #DEE6F1;border-radius:16px;padding:18px;
box-shadow:0 8px 26px rgba(23,52,91,.045)}
[data-testid="stDataFrame"] {border:1px solid #DEE6F1;border-radius:14px;overflow:hidden}
.stButton button,.stDownloadButton button,.stLinkButton a {border-radius:10px;font-weight:650}
.intro {background:linear-gradient(135deg,#172B50,#244A83);color:#fff;padding:30px 32px;
border-radius:20px;margin-bottom:16px;box-shadow:0 14px 35px rgba(23,52,91,.16)}
.intro h2 {color:#fff;margin:0 0 8px;font-size:30px}.intro p {margin:0;color:#DCE7FA;line-height:1.6}
.feature-grid {display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:0 0 18px}
.feature-card {background:#fff;border:1px solid #DEE6F1;border-radius:13px;padding:14px;color:#263A58;
font-size:13px;line-height:1.45}.feature-card b {display:block;color:#17345B;margin-bottom:4px;font-size:14px}
.eyebrow {display:inline-flex;align-items:center;margin-bottom:10px;padding:6px 11px;
border:1px solid #C8D6F4;border-radius:999px;background:#EAF0FC;color:#274D9B;
font-size:12px;line-height:1.2;letter-spacing:.09em;font-weight:750}
.auth-heading {font-size:20px;font-weight:750;color:#17243D;line-height:1.25;margin:12px 0 4px}
.auth-subheading {font-size:14px;color:#52627E;line-height:1.5;margin:0 0 18px}
.profile-strip {display:flex;justify-content:space-between;align-items:center;gap:18px;
padding:14px 18px;margin:0 0 22px;border:1px solid #D4E0F0;border-radius:14px;
background:linear-gradient(100deg,#FFFFFF,#F1F6FE);color:#17243D;box-shadow:0 6px 20px rgba(23,52,91,.05)}
.profile-strip strong {font-size:17px}
.profile-strip span {color:#60708A;font-size:13px;text-align:right}
@media (max-width:760px) {.block-container {padding-top:3.5rem}.eyebrow {font-size:10px}
.feature-grid {grid-template-columns:1fr}.profile-strip {align-items:flex-start;flex-direction:column;gap:3px}
.profile-strip span {text-align:left}.intro {padding:24px}.intro h2 {font-size:25px}}
</style>''', unsafe_allow_html=True)
