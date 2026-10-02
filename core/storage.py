import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from pathlib import Path

from core.catalog import GOALS, SKILLS
from core.tasks import TASK_BY_ID

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get("CAREER_COPILOT_DB", ROOT / "data" / "career.db"))


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL,
            created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            claims TEXT NOT NULL DEFAULT '[]', target TEXT NOT NULL DEFAULT 'Python foundations');
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
            task_id TEXT NOT NULL, code TEXT NOT NULL, result TEXT NOT NULL,
            prediction TEXT NOT NULL, hints INTEGER NOT NULL, solution_seen INTEGER NOT NULL,
            created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS assistance (
            user_id INTEGER NOT NULL REFERENCES users(id), task_id TEXT NOT NULL,
            hints INTEGER NOT NULL DEFAULT 0, solution_seen INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(user_id,task_id));
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
            attempt_id INTEGER NOT NULL REFERENCES attempts(id), comment TEXT NOT NULL,
            created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS login_limits (
            username TEXT PRIMARY KEY, failures INTEGER NOT NULL, locked_until REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS saved_jobs (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL, job_text TEXT NOT NULL, score REAL NOT NULL,
            missing_skills TEXT NOT NULL, roadmaps TEXT NOT NULL, created REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
            event TEXT NOT NULL, details TEXT NOT NULL DEFAULT '', created REAL NOT NULL);
        ''')

        # Additive migrations keep databases made by earlier project versions usable.
        user_columns = {row["name"] for row in db.execute("PRAGMA table_info(users)")}
        profile_columns = {row["name"] for row in db.execute("PRAGMA table_info(profiles)")}
        for column, definition in {
            "email": "TEXT NOT NULL DEFAULT ''",
            "phone": "TEXT NOT NULL DEFAULT ''",
        }.items():
            if column not in user_columns:
                db.execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")
        for column, definition in {
            "location": "TEXT NOT NULL DEFAULT ''",
            "education": "TEXT NOT NULL DEFAULT ''",
            "about": "TEXT NOT NULL DEFAULT ''",
            "cv_text": "TEXT NOT NULL DEFAULT ''",
        }.items():
            if column not in profile_columns:
                db.execute(f"ALTER TABLE profiles ADD COLUMN {column} {definition}")


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000).hex()


def _log(db, user_id, event, details=""):
    db.execute("INSERT INTO activity_log(user_id,event,details,created) VALUES(?,?,?,?)",
               (user_id, event, details[:500], time.time()))


def register(username, name, password, email="", phone=""):
    if not all(isinstance(value, str) for value in (username, name, password, email, phone)):
        raise ValueError("Account details must be text.")
    username = username.strip().lower()
    name = name.strip()
    email = email.strip().lower()
    phone = phone.strip()
    if not re.fullmatch(r"[a-z0-9_]{3,24}", username):
        raise ValueError("Username: 3-24 lowercase letters, digits or underscores.")
    if not 1 <= len(name) <= 80:
        raise ValueError("Enter a display name with 1-80 characters.")
    if not 8 <= len(password) <= 128:
        raise ValueError("Password must have 8-128 characters.")
    if email and (len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)):
        raise ValueError("Enter a valid email address.")
    if phone and (len(phone) > 24 or not re.fullmatch(r"\+?[0-9][0-9 ()-]{6,22}[0-9]", phone)):
        raise ValueError("Enter a valid phone number using digits and an optional country code.")
    salt = secrets.token_hex(16)
    digest = password_hash(password, salt)
    try:
        with connect() as db:
            cursor = db.execute("INSERT INTO users(username,name,email,phone,salt,password_hash,created) VALUES(?,?,?,?,?,?,?)",
                                (username, name, email, phone, salt, digest, time.time()))
            db.execute("INSERT INTO profiles(user_id) VALUES(?)", (cursor.lastrowid,))
            _log(db, cursor.lastrowid, "account_created", "Account and private profile created")
            # Failed sign-ins for a not-yet-created username must not lock a new account.
            db.execute("DELETE FROM login_limits WHERE username=?", (username,))
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("This username is already taken.") from None


def login(username, password):
    if not isinstance(username, str) or not isinstance(password, str):
        return None
    username = username.strip().lower()
    if not re.fullmatch(r"[a-z0-9_]{3,24}", username) or len(password) > 128:
        return None
    with connect() as db:
        limit = db.execute("SELECT * FROM login_limits WHERE username=?", (username,)).fetchone()
        if limit and limit["locked_until"] > time.time():
            raise ValueError("Too many attempts. Please wait five minutes.")
        row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        salt = row["salt"] if row else "00" * 16
        digest = password_hash(password, salt)
        if row and hmac.compare_digest(row["password_hash"], digest):
            db.execute("DELETE FROM login_limits WHERE username=?", (username,))
            _log(db, row["id"], "signed_in", "Successful sign in")
            return {"id": row["id"], "name": row["name"], "username": row["username"],
                    "email": row["email"], "phone": row["phone"]}
        failures = (limit["failures"] if limit else 0) + 1
        locked = time.time() + 300 if failures >= 5 else 0
        db.execute("INSERT OR REPLACE INTO login_limits VALUES(?,?,?)", (username, 0 if locked else failures, locked))
    return None


def profile(user_id):
    with connect() as db:
        row = db.execute("SELECT p.*,u.name,u.username,u.email,u.phone,u.created AS joined "
                         "FROM profiles p JOIN users u ON u.id=p.user_id WHERE p.user_id=?",
                         (user_id,)).fetchone()
    if row is None:
        raise ValueError("Profile not found.")
    try:
        claims = json.loads(row["claims"])
    except (TypeError, json.JSONDecodeError):
        claims = []
    if not isinstance(claims, list):
        claims = []
    claims = list(dict.fromkeys(claim for claim in claims if isinstance(claim, str) and len(claim) <= 100))
    target = row["target"] if row["target"] in GOALS else "Python foundations"
    return {"claims": claims, "target": target, "name": row["name"],
            "username": row["username"], "email": row["email"], "phone": row["phone"],
            "location": row["location"], "education": row["education"],
            "about": row["about"], "cv_text": row["cv_text"], "joined": row["joined"]}


def save_profile(user_id, claims, target, location="", education="", about="", cv_text=""):
    if (not isinstance(claims, list) or len(claims) > 5000 or
            any(not isinstance(claim, str) or len(claim) > 100 for claim in claims) or
            len(set(claims)) != len(claims)):
        raise ValueError("Skills must be unique strings under 100 characters.")
    if not isinstance(target, str) or target not in GOALS:
        raise ValueError("Choose a supported learning goal.")
    fields = (location, education, about, cv_text)
    if not all(isinstance(value, str) for value in fields):
        raise ValueError("Profile details and CV must be text.")
    location, education, about, cv_text = (value.strip() for value in fields)
    if len(location) > 120 or len(education) > 500 or len(about) > 2000 or len(cv_text) > 50000:
        raise ValueError("Profile details or CV exceed the allowed length.")
    with connect() as db:
        cursor = db.execute("UPDATE profiles SET claims=?,target=?,location=?,education=?,about=?,cv_text=? WHERE user_id=?",
                            (json.dumps(claims), target, location, education, about, cv_text, user_id))
        if cursor.rowcount != 1:
            raise ValueError("Profile not found.")
        _log(db, user_id, "profile_updated", "Profile details, skills, goal and saved CV updated")


def update_account_details(user_id, name, email="", phone="", new_password=None):
    if not all(isinstance(value, str) for value in (name, email, phone)):
        raise ValueError("Account details must be text.")
    name = name.strip()
    email = email.strip().lower()
    phone = phone.strip()
    if not 1 <= len(name) <= 80:
        raise ValueError("Enter a display name with 1-80 characters.")
    if email and (len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)):
        raise ValueError("Enter a valid email address.")
    if phone and (len(phone) > 24 or not re.fullmatch(r"\+?[0-9][0-9 ()-]{6,22}[0-9]", phone)):
        raise ValueError("Enter a valid phone number using digits and an optional country code.")
    if new_password is not None and not 8 <= len(new_password) <= 128:
        raise ValueError("Password must have 8-128 characters.")
    
    with connect() as db:
        if new_password:
            salt = secrets.token_hex(16)
            digest = password_hash(new_password, salt)
            db.execute("UPDATE users SET name=?, email=?, phone=?, salt=?, password_hash=? WHERE id=?", 
                       (name, email, phone, salt, digest, user_id))
        else:
            db.execute("UPDATE users SET name=?, email=?, phone=? WHERE id=?", 
                       (name, email, phone, user_id))
        _log(db, user_id, "account_updated", "Account details updated")


def assistance(user_id, task_id, hints=None, solution=None):
    if not isinstance(task_id, str) or task_id not in TASK_BY_ID:
        raise ValueError("Unknown task.")
    if hints is not None and (not isinstance(hints, int) or isinstance(hints, bool) or not 0 <= hints <= 3):
        raise ValueError("Hint count must be from 0 to 3.")
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO assistance(user_id,task_id) VALUES(?,?)", (user_id, task_id))
        if hints is not None:
            db.execute("UPDATE assistance SET hints=MAX(hints,?) WHERE user_id=? AND task_id=?", (hints, user_id, task_id))
            _log(db, user_id, "hint_viewed", f"{task_id}: hint {hints}")
        if solution:
            db.execute("UPDATE assistance SET solution_seen=1 WHERE user_id=? AND task_id=?", (user_id, task_id))
            _log(db, user_id, "solution_viewed", f"{task_id}: reference solution")
        return dict(db.execute("SELECT * FROM assistance WHERE user_id=? AND task_id=?", (user_id, task_id)).fetchone())


def save_attempt(user_id, task_id, code, result, prediction):
    if not isinstance(task_id, str) or task_id not in TASK_BY_ID:
        raise ValueError("Unknown task.")
    if not isinstance(code, str) or len(code) > 12000:
        raise ValueError("Code must be text with at most 12,000 characters.")
    if not isinstance(result, dict) or not isinstance(prediction, dict):
        raise ValueError("Attempt result and prediction must be structured data.")
    try:
        result_json = json.dumps(result, allow_nan=False)
        prediction_json = json.dumps(prediction, allow_nan=False)
    except (TypeError, ValueError):
        raise ValueError("Attempt data is not valid JSON.") from None
    help_used = assistance(user_id, task_id)
    with connect() as db:
        cur = db.execute("INSERT INTO attempts(user_id,task_id,code,result,prediction,hints,solution_seen,created) VALUES(?,?,?,?,?,?,?,?)",
                         (user_id, task_id, code, result_json, prediction_json,
                          help_used["hints"], help_used["solution_seen"], time.time()))
        _log(db, user_id, "practice_attempt", f"{task_id}: {result.get('status', 'unknown')} ({result.get('passed', 0)}/{result.get('total', 0)} tests)")
        return cur.lastrowid


def attempts(user_id):
    with connect() as db:
        rows = db.execute("SELECT * FROM attempts WHERE user_id=? ORDER BY id", (user_id,)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["result"] = json.loads(item["result"])
        item["prediction"] = json.loads(item["prediction"])
        result.append(item)
    return result


def report_prediction(user_id, attempt_id, comment):
    if not isinstance(comment, str) or not comment.strip() or len(comment) > 1000:
        raise ValueError("Feedback must have 1-1,000 characters.")
    with connect() as db:
        if not db.execute("SELECT id FROM attempts WHERE id=? AND user_id=?", (attempt_id, user_id)).fetchone():
            raise ValueError("Attempt not found.")
        db.execute("INSERT INTO feedback(user_id,attempt_id,comment,created) VALUES(?,?,?,?)", (user_id, attempt_id, comment.strip(), time.time()))
        _log(db, user_id, "prediction_reported", f"Feedback saved for attempt {attempt_id}")


def activity(user_id, limit=None):
    if limit is not None and (not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 500):
        raise ValueError("Activity limit must be between 1 and 500.")
    with connect() as db:
        query = "SELECT id,event,details,created FROM activity_log WHERE user_id=? ORDER BY id DESC"
        values = (user_id,)
        if limit is not None:
            query += " LIMIT ?"
            values += (limit,)
        return [dict(row) for row in db.execute(query, values)]


def export_user(user_id):
    with connect() as db:
        rows = db.execute("SELECT attempt_id,comment,created FROM feedback WHERE user_id=?", (user_id,)).fetchall()
    return {"profile": profile(user_id), "attempts": attempts(user_id),
            "feedback": [dict(r) for r in rows], "saved_jobs": get_saved_jobs(user_id),
            "activity": activity(user_id)}


def save_job_analysis(user_id, title, job_text, score, missing_skills, roadmaps):
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 120:
        raise ValueError("Job title must have 1-120 characters.")
    if not isinstance(job_text, str) or not 1 <= len(job_text.strip()) <= 50000:
        raise ValueError("Job description must have 1-50,000 characters.")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100:
        raise ValueError("Match score must be between 0 and 100.")
    if (not isinstance(missing_skills, list) or len(missing_skills) > 15 or
            any(not isinstance(skill, str) or not 1 <= len(skill) <= 100 for skill in missing_skills)):
        raise ValueError("Missing skills must be a valid list with at most 15 items.")
    if not isinstance(roadmaps, list) or len(roadmaps) > 15:
        raise ValueError("Roadmap data is invalid.")
    try:
        missing_json = json.dumps(missing_skills, allow_nan=False)
        roadmaps_json = json.dumps(roadmaps, allow_nan=False)
    except (TypeError, ValueError):
        raise ValueError("Roadmap data is not valid JSON.") from None
    with connect() as db:
        db.execute("INSERT INTO saved_jobs(user_id, title, job_text, score, missing_skills, roadmaps, created) VALUES(?,?,?,?,?,?,?)",
                   (user_id, title.strip(), job_text.strip(), float(score), missing_json, roadmaps_json, time.time()))
        _log(db, user_id, "job_analysis_saved", f"{title.strip()}: {float(score):.1f}% similarity")


def get_saved_jobs(user_id):
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM saved_jobs WHERE user_id=? ORDER BY created DESC", (user_id,))]


def delete_saved_job(user_id, job_id):
    if not isinstance(job_id, int) or isinstance(job_id, bool):
        raise ValueError("Saved analysis not found.")
    with connect() as db:
        cursor = db.execute("DELETE FROM saved_jobs WHERE id=? AND user_id=?", (job_id, user_id))
        if cursor.rowcount != 1:
            raise ValueError("Saved analysis not found.")
        _log(db, user_id, "job_analysis_deleted", f"Deleted saved analysis {job_id}")
