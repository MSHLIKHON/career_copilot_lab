import io
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
from core.adaptive import SKILLS, GOALS, extract_claims, summarize, recommend, roadmap

st.set_page_config(page_title="Career Copilot Lab", page_icon="🎓", layout="wide")
st.markdown('''<style>
.block-container {max-width:1160px;padding-top:2rem;padding-bottom:3rem}
h1,h2,h3 {letter-spacing:-.035em}
[data-testid="stSidebar"] {border-right:1px solid #E5EAF4}
[data-testid="stMetric"] {background:white;border:1px solid #E5EAF4;border-radius:14px;padding:18px}
.intro {background:#182849;color:#fff;padding:28px 32px;border-radius:18px;margin-bottom:24px}
.intro h2 {color:#fff;margin:0 0 8px}.intro p {margin:0;color:#d8e2fb}
.eyebrow {font-size:12px;letter-spacing:.12em;color:#6684c6;font-weight:700}
</style>''', unsafe_allow_html=True)
storage.init_db()


def authenticate():
    st.markdown('<div class="eyebrow">TEAM NO AI · AI LAB PROTOTYPE</div>', unsafe_allow_html=True)
    st.title("Career Copilot Lab")
    st.write("Show what you can do. Learn from each attempt.")
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown('<div class="intro"><h2>Practice with a next step.</h2><p>Small Python challenges, real test evidence and hints that help you move forward.</p></div>', unsafe_allow_html=True)
        st.write("**20 tasks** across Conditions, Loops, Functions and Lists.")
        st.write("**Your own progress** saved locally, with assisted and independent attempts separated.")
        st.write("**A trained pilot model** suggests mistake categories. Predictions can be wrong.")
        st.info("Local classroom prototype. No GPT/Gemini key required. Create your own account; there is no default password.")
    with right:
        login_tab, register_tab = st.tabs(["Sign in", "Create account"])
        with login_tab:
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
            with st.form("register"):
                name = st.text_input("Your name", max_chars=80)
                username = st.text_input("Choose username", help="3-24 letters, digits or underscores", max_chars=24)
                password = st.text_input("Choose password", type="password", max_chars=128)
                confirm = st.text_input("Confirm password", type="password", max_chars=128)
                consent = st.checkbox("I understand my attempts and profile will be stored on this computer.")
                submitted = st.form_submit_button("Create account", width="stretch")
            if submitted:
                if password != confirm:
                    st.error("Passwords do not match.")
                elif not consent:
                    st.error("Please confirm local storage consent.")
                else:
                    try:
                        storage.register(username, name, password)
                        st.success("Account created. Open Sign in and use your new username and password.")
                    except ValueError as error:
                        st.error(str(error))


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
    page = st.radio("Workspace", ["Overview", "Practice", "My skills & CV", "Learning roadmap", "History", "Model lab", "Runner help"], key="page")
    st.divider()
    st.write(user["name"])
    st.caption("Private account history · stored on this device")
    if st.button("Sign out", width="stretch"):
        st.session_state.clear()
        st.rerun()


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
    st.title("Practice Python")
    st.write("Write a function named solve. Return your answer; do not use input() or print().")
    task_id = st.selectbox("Choose a task", list(TASK_BY_ID), format_func=lambda k: f"{k} · {TASK_BY_ID[k]['title']} / {TASK_BY_ID[k]['topic']} / Level {TASK_BY_ID[k]['level']}", key="task_select")
    task = TASK_BY_ID[task_id]
    st.subheader(task["title"])
    st.write(task["prompt"])
    st.caption(f"Topic: {task['topic']} · Level {task['level']} · {len(task['tests'])} deterministic tests")
    with st.expander("Example inputs and outputs", expanded=False):
        for case in task["tests"][:2]:
            st.code(f"solve({', '.join(repr(x) for x in case['args'])}) → {case['expected']!r}", language="text")
    editor_key = f"editor_{task_id}"
    if editor_key not in st.session_state:
        st.session_state[editor_key] = task["starter"]
    left, right = st.columns([2.1, 1], gap="large")
    with left:
        if task_id == "L1" and st.button("Load a buggy example", help="Replaces this task's editor with an intentional off-by-one example."):
            st.session_state[editor_key] = "def solve(n):\n    total = 0\n    for i in range(1, n):\n        total += i\n    return total\n"
        code = st.text_area("Your Python code", key=editor_key, height=300, max_chars=12000)
        if st.button("Run tests & save attempt", type="primary", width="stretch"):
            with st.spinner("Checking code and test evidence..."):
                result = run_tests(code, task)
                model, model_error = load_model()
                prediction = predict(code, result, model, model_error)
                storage.save_attempt(uid, task_id, code, result, prediction)
            st.rerun()
    with right:
        st.markdown("#### Hint ladder")
        help_used = storage.assistance(uid, task_id)
        st.caption("Hints are saved with your task history. Viewed solutions always mark later attempts on this task as assisted.")
        if help_used["hints"] < 3 and st.button("Show next hint", width="stretch"):
            help_used = storage.assistance(uid, task_id, hints=help_used["hints"] + 1)
        for index, hint in enumerate(task["hints"][:help_used["hints"]], 1):
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
        show_result(current_attempts[-1])
        st.caption("These results belong to the last submitted code, not unsaved editor changes.")
        next_task, reason = recommend(history, profile["target"])
        st.write(f"**Recommended next:** {next_task['title']}. {reason}")
        if st.button("Open next practice task"):
            go_to_task(next_task["id"])

elif page == "My skills & CV":
    st.caption("CLAIMS AND EVIDENCE")
    st.title("My skills & CV")
    st.write("Paste CV text or upload a text-based PDF/TXT. Review the extracted keywords before saving.")
    st.caption("The parser recognises listed skill words, not proficiency, context or negation. SQL/React and other non-Python skills remain unassessed.")
    cv_text = st.text_area("CV text (optional)", max_chars=50000, height=120)
    uploaded = st.file_uploader("CV file (optional; maximum 2 MB)", type=["pdf", "txt"])
    if st.button("Extract skill keywords"):
        try:
            text = cv_text
            if uploaded:
                if uploaded.size > 2 * 1024 * 1024:
                    raise ValueError("File must be at most 2 MB.")
                if uploaded.name.lower().endswith(".pdf"):
                    reader = PdfReader(io.BytesIO(uploaded.getvalue()))
                    if reader.is_encrypted:
                        raise ValueError("Use an unencrypted PDF.")
                    if len(reader.pages) > 10:
                        raise ValueError("Use a CV with at most 10 pages.")
                    text += "\n" + "\n".join((p.extract_text() or "")[:10000] for p in reader.pages)
                else:
                    text += "\n" + uploaded.getvalue().decode("utf-8")
            found = extract_claims(text)
            st.session_state.claim_choices = found
            if found:
                st.success("Keywords extracted. Review the selected claims, then save.")
            else:
                st.warning("No supported keywords found. Scanned PDFs need OCR; select skills manually below.")
        except Exception as error:
            st.error(f"Could not read CV: {error}")
    if "claim_choices" not in st.session_state:
        st.session_state.claim_choices = profile["claims"]
    claims = st.multiselect("Skills you claim (confirm manually)", SKILLS, key="claim_choices")
    target = st.selectbox("Learning goal", list(GOALS), index=list(GOALS).index(profile["target"]))
    if st.button("Save skill profile", type="primary"):
        storage.save_profile(uid, claims, target)
        st.success("Profile saved. Raw CV text/file is not written to the database.")
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
    for title, topics, brief in [
        ("Student result calculator", "Conditions + Functions", "Create functions for total, average and grade. Test the exact grade boundaries and an empty mark list."),
        ("Daily expense summary", "Loops + Lists", "Write functions to total expenses, find the largest amount and remove duplicates. Test empty and single-item inputs."),
        ("Number practice toolkit", "Functions + Loops", "Combine prime checking, digit sum and GCD functions. Write your own test table and explain failed cases.")]:
        with st.expander(title + " / " + topics):
            st.write(brief)

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

elif page == "Model lab":
    st.caption("TRAINING AND EVALUATION")
    st.title("Our trained mistake classifier")
    path = MODEL_DIR / "metrics.json"
    metrics, metrics_error = load_metrics()
    if metrics_error:
        st.warning(metrics_error)
    else:
        st.warning(metrics["warning"])
        st.write("**Approach:** Character TF-IDF + Logistic Regression. Linear SVM is a comparison baseline.")
        st.write("**Training input:** Submitted code and runtime error types. **Output:** One of four likely logic-mistake categories.")
        st.write("**Syntax errors:** Deterministic parser feedback, not a trained AI category.")
        st.write(metrics["split_policy"])
        a, b, c = st.columns(3)
        a.metric("Generated samples", metrics["dataset_size"])
        b.metric("Source families", metrics["family_count"])
        c.metric("Human-reviewed real samples", 0)
        rows = [{"Model": name, "Partition": split, "Accuracy": data["accuracy"], "Macro F1": data["macro_f1"], "Macro recall": data["macro_recall"]}
                for name, results in metrics["models"].items() for split, data in results.items()]
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        st.subheader("Test confusion matrix: Logistic Regression")
        st.caption("Rows = actual mutation label. Columns = predicted label.")
        st.dataframe(pd.DataFrame(metrics["models"]["logistic_regression"]["test"]["confusion_matrix"], index=metrics["labels"], columns=metrics["labels"]), width="stretch")
        st.write(metrics["deployment_reason"])
        st.caption("Low model scores (<0.45) produce an uncertain result. Unseen/multiple mistakes may be misclassified. Independent human-reviewed data is required before claiming generalisation.")
        st.download_button("Download evaluation report", path.read_bytes(), "evaluation_metrics.json", "application/json")
    st.subheader("Reproduce training")
    st.code("python train.py\npython -m unittest discover -s tests -v", language="bash")
    st.write("Training writes data/pilot_dataset.json, models/classifier.joblib and models/metrics.json. Never load model files from unknown sources.")

elif page == "Runner help":
    st.title("Runner help & project limits")
    st.write("This app interprets a restricted Python subset. It never calls eval or exec on submitted code.")
    st.markdown("""
**Supported:** function definitions with positional parameters; return; if/elif/else;
for/while; break/continue; assignment; +=, -=, *=; integer and decimal arithmetic;
comparison; and/or/not; lists, tuples, strings; indexing and slicing.

**Allowed functions:** len, range, sum, min, max, abs, sorted, reversed, list, int,
str, bool, enumerate and round. Your own helper functions are allowed.

**Not supported:** imports, attributes/methods such as .append(), files, network,
input(), print(), classes, dictionaries, sets, comprehensions, lambda, generators,
power operator (**), decorators, keyword/default parameters or top-level calls.
Use `result = result + [value]` instead of append.

**Limits:** 12,000 source characters, 1,800 AST nodes, 15,000 interpreter steps per
test, 1,500 items per collection, nesting depth 12, call depth 30, numeric magnitude 10^15.
Each test uses a fresh interpreter and a copy of its input. Types matter: return
True/False for boolean tasks, not strings such as "True".

**Privacy:** salted PBKDF2 password hashes; no plaintext passwords. Profile and
attempt data stay in data/career.db on this computer. Raw CV uploads are not saved
to the database. Any person with access to this machine's files can read its data.

**Scope:** local educational prototype only; Python foundations, generated pilot
model, rule-based adaptation, keyword-based CV mapping. It is not a hiring tool,
full Python execution service or audited internet-facing sandbox. Do not expose
the server publicly. Chatbot integration, OCR, SQL/React execution, cloud sync,
password reset by email and production deployment are not part of this build.

**Team NO AI:** MD Shyed Hasan Likhon (0112330688), Rahat (112330518),
112330546, 112330621, 112330396. Add the three missing names before submission.
""")
