import io
import html
import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from pypdf import PdfReader
from core import storage
from core.tasks import TASKS, TASK_BY_ID, TOPICS
from core.runner import run_tests
from core.model import load_metrics, load_model, predict, MODEL_DIR
from core.job_ml import analyze_job_match, generate_roadmap
from core.adaptive import (SKILLS, GOALS, HINT_UNLOCKS, SOLUTION_UNLOCK,
                           extract_claims, practice_progress, summarize, recommend, roadmap)

st.set_page_config(page_title="Career Copilot Lab", page_icon="🎓", layout="wide")
st.markdown('''<style>
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
storage.init_db()


def authenticate():
    st.markdown('<div class="eyebrow">TEAM NO AI · CAREER SKILLS PRACTICE LAB</div>', unsafe_allow_html=True)
    st.title("Career Copilot Lab")
    st.write("Show what you can do. Learn from each attempt.")
    login_tab, register_tab = st.tabs(["Sign in", "Create account"])
    with login_tab:
        left, right = st.columns([1.05, 1], gap="large")
        with left:
            st.markdown('<div class="intro"><h2>Practice with a next step.</h2><p>Small Python challenges, real test evidence and hints that help you move forward.</p></div>', unsafe_allow_html=True)
            st.markdown('''<div class="feature-grid">
<div class="feature-card"><b>20 focused tasks</b>Conditions, loops, functions and lists.</div>
<div class="feature-card"><b>Private progress</b>Assisted and independent evidence stays separate.</div>
<div class="feature-card"><b>Local feedback</b>A pilot model suggests likely mistake categories.</div>
</div>''', unsafe_allow_html=True)
            st.info("Local classroom prototype. No GPT/Gemini key required. Create your own account; there is no default password.")
        with right:
            st.markdown('<div class="auth-heading">Welcome back</div>'
                        '<p class="auth-subheading">Sign in to continue your practice.</p>',
                        unsafe_allow_html=True)
            with st.form("login"):
                username = st.text_input("Username", max_chars=24)
                password = st.text_input("Password", type="password", max_chars=128)
                submitted = st.form_submit_button("Sign in", type="primary", width="stretch")
            if submitted:
                try:
                    user = storage.login(username, password)
                    if user:
                        st.session_state.clear()
                        st.session_state.user = user
                        st.session_state.last_active = time.time()
                        st.rerun()
                    st.error("Username or password is incorrect.")
                except ValueError as error:
                    st.error(str(error))
    with register_tab:
        st.markdown('<div class="auth-heading">Create account</div>'
                    '<p class="auth-subheading">Your progress is saved on this computer.</p>',
                    unsafe_allow_html=True)
        with st.form("register"):
            details, security = st.columns(2, gap="large")
            with details:
                name = st.text_input("Your name", placeholder="Your display name", max_chars=80)
                username = st.text_input("Choose username", placeholder="3–24 letters, numbers or _", max_chars=24)
                email = st.text_input("Email address", placeholder="you@example.com", max_chars=254)
            with security:
                phone = st.text_input("Phone number", placeholder="+880 1XXX-XXXXXX", max_chars=24)
                password = st.text_input("Choose password", type="password", placeholder="8–128 characters", max_chars=128)
                confirm = st.text_input("Confirm password", type="password", placeholder="Repeat password", max_chars=128)
            consent = st.checkbox("Save my progress on this computer")
            form_message = st.empty()
            submitted = st.form_submit_button("Create account and start", type="primary", width="stretch")
        if submitted:
            if password != confirm:
                form_message.error("Passwords do not match. Re-enter the same password in both fields.")
            elif not consent:
                form_message.error("Please allow local storage to save your practice and profile.")
            else:
                try:
                    if not email.strip() or not phone.strip():
                        raise ValueError("Email address and phone number are required.")
                    storage.register(username, name, password, email, phone)
                    user = storage.login(username, password)
                    st.session_state.clear()
                    st.session_state.user = user
                    st.session_state.last_active = time.time()
                    st.rerun()
                except ValueError as error:
                    if "already taken" in str(error):
                        form_message.error("This username is already taken. Try adding a few numbers or choose another name.")
                    else:
                        form_message.error(str(error))

    st.divider()
    st.subheader("Technical information")
    model_tab, runner_tab = st.tabs(["Model lab", "Runner help"])
    with model_tab:
        st.write("The local pilot classifier suggests one of four likely programming-mistake categories.")
        metrics, metrics_error = load_metrics()
        if metrics_error:
            st.warning(metrics_error)
        else:
            st.warning(metrics["warning"])
            st.write("**Approach:** Character TF-IDF + Logistic Regression; Linear SVM is a comparison baseline.")
            summary = [{"Model": name, "Test accuracy": values["test"]["accuracy"],
                        "Macro F1": values["test"]["macro_f1"]}
                       for name, values in metrics["models"].items()]
            st.dataframe(pd.DataFrame(summary), hide_index=True, width="stretch")
            st.download_button("Download evaluation report", (MODEL_DIR / "metrics.json").read_bytes(),
                               "evaluation_metrics.json", "application/json")
    with runner_tab:
        st.write("Submitted code runs in a restricted AST interpreter; the app never calls eval or exec on it.")
        st.markdown("""
**Supported:** positional functions, return, conditions, loops, assignment, basic
arithmetic, comparisons, lists, tuples, strings, indexing and slicing.

**Allowed functions:** len, range, sum, min, max, abs, sorted, reversed, list, int,
str, bool, enumerate and round.

**Not supported:** imports, attributes/methods, files, network, input, print, classes,
dictionaries, sets, comprehensions, lambda, generators, decorators or top-level calls.
""")


if "user" not in st.session_state:
    authenticate()
    st.stop()
if time.time() - st.session_state.get("last_active", 0) > 1800:
    st.session_state.clear()
    st.rerun()
st.session_state.last_active = time.time()
user = st.session_state.user
uid = user["id"]
history = storage.attempts(uid)
profile = storage.profile(uid)

if "pending_page" in st.session_state:
    st.session_state.page = st.session_state.pop("pending_page")
if "pending_task" in st.session_state:
    st.session_state.task_select = st.session_state.pop("pending_task")

with st.sidebar:
    st.markdown("### Career Copilot\n**LAB / TEAM NO AI**")
    st.caption("Python skill verification & adaptive practice")
    st.divider()
    page = st.radio("Workspace", ["My profile", "Overview", "Practice", "My skills & CV", "Learning roadmap", "Job Match Analyzer", "History"], key="page")
    st.divider()
    st.write(user["name"])
    st.caption("Private account history · stored on this device")
    if st.button("Sign out", width="stretch"):
        st.session_state.clear()
        st.rerun()

st.markdown(
    f'<div class="profile-strip"><strong>{html.escape(profile["name"])}</strong>'
    f'<span>@{html.escape(profile["username"])} · {html.escape(profile["target"])}</span></div>',
    unsafe_allow_html=True,
)


def go_to_task(task_id):
    st.session_state.pending_task = task_id
    st.session_state.pending_page = "Practice"
    st.rerun()


def show_result(attempt):
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


if page == "Overview":
    st.caption("YOUR LEARNING WORKSPACE")
    st.title(f"Welcome, {user['name']}")
    st.write("Test a skill. Understand a mistake. Choose your next step.")
    done = {a["task_id"] for a in history if a["result"]["status"] == "passed"}
    independent = {a["task_id"] for a in history if a["result"]["status"] == "passed" and not a["hints"] and not a["solution_seen"]}
    cols = st.columns(4)
    for col, label, value in zip(cols, ["Attempts", "Tasks passed", "Independent passes", "Available tasks"], [len(history), len(done), len(independent), 20]):
        col.metric(label, value)
    st.progress(len(done) / 20, text=f"{len(done)} of 20 tasks have a passing attempt")
    st.subheader("Your next task")
    next_task, reason = recommend(history, profile["target"])
    st.write(f"**{next_task['title']}** · {next_task['topic']} · Level {next_task['level']}")
    st.write(reason)
    if st.button("Start recommended task", type="primary"):
        go_to_task(next_task["id"])
    st.subheader("Evidence by topic")
    st.dataframe(pd.DataFrame(summarize(history)), hide_index=True, width="stretch")
    st.caption("A passing task is limited evidence, not a certificate of expertise or job readiness.")

elif page == "Practice":
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
        show_result(current_attempts[-1])
        st.caption("These results belong to the last submitted code, not unsaved editor changes.")
        next_task, reason = recommend(history, profile["target"])
        st.write(f"**Recommended next:** {next_task['title']}. {reason}")
        if st.button("Open next practice task"):
            go_to_task(next_task["id"])

elif page == "My profile":
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

elif page == "My skills & CV":
    st.caption("CLAIMS AND EVIDENCE")
    st.title("My skills & CV")
    st.write("Paste CV text or upload a text-based PDF/TXT. Review the extracted keywords, then save the CV to your private profile.")
    st.caption("The parser recognises listed skill words, not proficiency, context or negation. SQL/React and other non-Python skills remain unassessed.")
    if "cv_text_draft" not in st.session_state:
        st.session_state.cv_text_draft = profile["cv_text"]
    cv_text = st.text_area("CV text (optional)", max_chars=50000, height=160, key="cv_text_draft",
                           on_change=lambda: st.session_state.pop("extracted_cv_text", None))
    uploaded = st.file_uploader("CV file (optional; maximum 2 MB)", type=["pdf", "txt"])
    if st.button("Extract skill keywords"):
        try:
            text = (cv_text or "").strip()
            if uploaded:
                if uploaded.size > 2 * 1024 * 1024:
                    raise ValueError("File must be at most 2 MB.")
                if uploaded.name.lower().endswith(".pdf"):
                    reader = PdfReader(io.BytesIO(uploaded.getvalue()))
                    if reader.is_encrypted:
                        raise ValueError("Use an unencrypted PDF.")
                    if len(reader.pages) > 10:
                        raise ValueError("Use a CV with at most 10 pages.")
                    extracted = "\n".join((p.extract_text() or "").strip()[:10000] for p in reader.pages)
                    text = f"{text}\n{extracted}".strip()
                else:
                    try:
                        decoded = uploaded.getvalue().decode("utf-8")
                    except UnicodeDecodeError:
                        decoded = uploaded.getvalue().decode("latin-1", errors="replace")
                    text = f"{text}\n{decoded}".strip()
            if not text:
                st.warning("Paste CV text or upload a CV file first.")
            else:
                found = extract_claims(text)
                st.session_state.extracted_cv_text = text[:50000]
                st.session_state.claim_choices = found
                if found:
                    st.success(f"{len(found)} keyword(s) extracted. Review the selected claims, then save.")
                else:
                    st.warning("No supported keywords found. Scanned PDFs need OCR; select skills manually below.")
        except Exception as error:
            st.error(f"Could not read CV: {error}")
    if "claim_choices" not in st.session_state:
        st.session_state.claim_choices = profile["claims"]
    claims = st.multiselect("Skills you claim (confirm manually)", SKILLS, key="claim_choices")
    target = st.selectbox("Learning goal", list(GOALS), index=list(GOALS).index(profile["target"]))
    save_cv = st.checkbox("Save this CV text in my private local profile", value=True)
    if st.button("Save skills & CV", type="primary"):
        stored_cv = st.session_state.get("extracted_cv_text", st.session_state.cv_text_draft) if save_cv else profile["cv_text"]
        storage.save_profile(uid, claims, target, profile["location"], profile["education"],
                             profile["about"], stored_cv)
        st.success("Skills, learning goal and CV text saved to your private profile.")
    st.subheader("Claimed vs assessed")
    rows = []
    for skill in claims:
        rows.append({"Skill": skill, "Claim": "Claimed by learner", "Evidence":
                     f"{len(history)} Python attempts recorded; see topic results" if skill == "Python" and history else "Not assessed"})
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    else:
        st.info("Add at least one skill claim to see its assessment status.")
    st.dataframe(pd.DataFrame(summarize(history)), hide_index=True, width="stretch")

elif page == "Learning roadmap":
    st.caption("A PLAN BASED ON YOUR ATTEMPTS")
    st.title("Learning roadmap")
    st.write(f"**Goal:** {profile['target']}")
    st.caption("These are educator-authored practice targets, not scraped job requirements or an ML hiring score. Career fit is outside this prototype.")
    st.dataframe(pd.DataFrame(roadmap(history, profile["target"])), hide_index=True, width="stretch")
    next_task, reason = recommend(history, profile["target"])
    st.info(reason)
    if st.button(f"Practise: {next_task['title']}", type="primary"):
        go_to_task(next_task["id"])
    st.subheader("Practice project suggestions")
    st.caption("Project briefs for extra learning. These are not automatically graded by the runner.")
    projects_by_goal = {
        "Python foundations": [
            ("Student result calculator", "Conditions + Functions", "Create functions for total, average and grade. Test exact grade boundaries and an empty mark list."),
            ("Daily expense summary", "Loops + Lists", "Total expenses, find the largest amount and remove duplicates. Test empty and single-item inputs."),
            ("Number practice toolkit", "Functions + Loops", "Combine prime checking, digit sum and GCD functions. Write a test table and explain failures."),
        ],
        "Python backend preparation": [
            ("Request validator", "Conditions + Functions", "Validate method, path and required fields for a small request dictionary."),
            ("Account rules", "Loops + Conditions", "Check password rules and locate a matching username without exposing stored passwords."),
            ("Batch input cleaner", "Lists + Functions", "Normalize a list of submitted values and reject invalid records before a mock insert."),
        ],
        "Data analysis foundations": [
            ("Tabular data cleaner", "Lists + Loops", "Clean rows, handle missing values and convert numeric text while recording rejected rows."),
            ("Summary statistics", "Functions + Lists", "Implement mean and median with explicit empty-input behaviour and boundary tests."),
            ("Category frequency report", "Loops + Conditions", "Count categories from records and return a deterministic, sorted summary."),
        ],
    }
    for title, topics, brief in projects_by_goal[profile["target"]]:
        with st.expander(title + " / " + topics):
            st.write(brief)

elif page == "Job Match Analyzer":
    st.caption("CAREER PREPARATION")
    st.title("Job Match Analyzer")
    st.write("Compare CV/profile text with a job description using local TF-IDF text similarity and a trained skill vocabulary.")
    st.caption("This is a learning aid, not a hiring score. Similar wording can raise the score, and extracted skills can be incomplete.")
    analyze_tab, saved_tab = st.tabs(["New analysis", "Saved roadmaps"])
    with analyze_tab:
        job_text = st.text_area("Job description", height=220, max_chars=50000)
        cv_text = st.text_area("CV text", value=profile["cv_text"], height=140, max_chars=50000,
                               help="Your saved profile CV is loaded automatically. If empty, saved skill claims are used.")
        if st.button("Analyze job match", type="primary"):
            if not job_text.strip():
                st.error("Paste a job description first.")
            else:
                score, missing_skills = analyze_job_match(cv_text, job_text, profile["claims"])
                st.session_state.job_analysis = {
                    "score": score, "missing_skills": missing_skills,
                    "roadmaps": generate_roadmap(missing_skills), "job_text": job_text,
                }
        analysis = st.session_state.get("job_analysis")
        if analysis:
            st.subheader("Analysis result")
            a, b = st.columns(2)
            a.metric("Text similarity", f"{analysis['score']}%")
            b.metric("Missing technical skills", len(analysis["missing_skills"]))
            if analysis["missing_skills"]:
                st.write("**Detected gaps:** " + ", ".join(analysis["missing_skills"]))
                st.subheader("Learning searches")
                for skill, resource in analysis["roadmaps"]:
                    with st.expander(skill):
                        st.write(resource["description"])
                        cols = st.columns(len(resource["links"]))
                        for col, (platform, url) in zip(cols, resource["links"].items()):
                            col.link_button(platform, url, width="stretch")
            else:
                st.success("No missing skill from the available vocabulary was detected.")
            with st.form("save_job_analysis"):
                title = st.text_input("Job title for this saved roadmap", max_chars=120)
                save_analysis = st.form_submit_button("Save analysis")
            if save_analysis:
                try:
                    storage.save_job_analysis(uid, title, analysis["job_text"], analysis["score"],
                                              analysis["missing_skills"], analysis["roadmaps"])
                    st.success("Analysis saved.")
                except ValueError as error:
                    st.error(str(error))
    with saved_tab:
        saved_jobs = storage.get_saved_jobs(uid)
        if not saved_jobs:
            st.info("No saved job analyses yet.")
        for saved in saved_jobs:
            with st.expander(f"{saved['title']} · {saved['score']:.1f}%"):
                try:
                    missing = json.loads(saved["missing_skills"])
                    roadmaps = json.loads(saved["roadmaps"])
                except (TypeError, json.JSONDecodeError):
                    st.error("This saved analysis is damaged and cannot be displayed.")
                    continue
                st.write("**Missing skills:** " + (", ".join(missing) if missing else "None detected"))
                for skill, resource in roadmaps:
                    st.write(f"**{skill}** — {resource['description']}")
                if st.button("Delete saved analysis", key=f"delete_job_{saved['id']}"):
                    storage.delete_saved_job(uid, saved["id"])
                    st.rerun()

elif page == "History":
    st.caption("YOUR SAVED EVIDENCE")
    st.title("Attempt history")
    if not history:
        st.info("No attempts yet. Open Practice to complete your first task.")
    else:
        table = [{"Attempt": a["id"], "Time (local)": datetime.fromtimestamp(a["created"]).strftime("%Y-%m-%d %H:%M"),
                  "Task": TASK_BY_ID[a["task_id"]]["title"], "Passed tests": f"{a['result']['passed']}/{a['result']['total']}",
                  "Status": a["result"]["status"], "Hint count": a["hints"], "Solution viewed": bool(a["solution_seen"])} for a in reversed(history)]
        st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
        selection = st.selectbox("Inspect attempt", list(reversed(range(len(history)))), format_func=lambda i: f"#{history[i]['id']} · {TASK_BY_ID[history[i]['task_id']]['title']}")
        st.code(history[selection]["code"], language="python")
        show_result(history[selection])
    st.download_button("Download my full progress (JSON)", json.dumps(storage.export_user(uid), indent=2),
                       file_name="career_copilot_progress.json", mime="application/json")
