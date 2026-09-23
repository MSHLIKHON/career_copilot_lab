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
        ''')


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000).hex()


def register(username, name, password):
    if not all(isinstance(value, str) for value in (username, name, password)):
        raise ValueError("Username, name and password must be text.")
    username = username.strip().lower()
    name = name.strip()
    if not re.fullmatch(r"[a-z0-9_]{3,24}", username):
        raise ValueError("Username: 3-24 lowercase letters, digits or underscores.")
    if not 1 <= len(name) <= 80:
        raise ValueError("Enter a display name with 1-80 characters.")
    if not 8 <= len(password) <= 128:
        raise ValueError("Password must have 8-128 characters.")
    salt = secrets.token_hex(16)
    digest = password_hash(password, salt)
    try:
        with connect() as db:
            cursor = db.execute("INSERT INTO users(username,name,salt,password_hash,created) VALUES(?,?,?,?,?)",
                                (username, name, salt, digest, time.time()))
            db.execute("INSERT INTO profiles(user_id) VALUES(?)", (cursor.lastrowid,))
            # Failed sign-ins for a not-yet-created username must not lock a new account.
            db.execute("DELETE FROM login_limits WHERE username=?", (username,))
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("This username is already taken.") from None


def login(username, password):
    if not isinstance(username, str) or not isinstance(password, str):
        return None
    username = username.strip().lower()[:24]
    if len(password) > 128:
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
            return {"id": row["id"], "name": row["name"], "username": row["username"]}
        failures = (limit["failures"] if limit else 0) + 1
        locked = time.time() + 300 if failures >= 5 else 0
        db.execute("INSERT OR REPLACE INTO login_limits VALUES(?,?,?)", (username, 0 if locked else failures, locked))
    return None


def profile(user_id):
    with connect() as db:
        row = db.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,)).fetchone()
    if row is None:
        raise ValueError("Profile not found.")
    try:
        claims = json.loads(row["claims"])
    except (TypeError, json.JSONDecodeError):
        claims = []
    if not isinstance(claims, list):
        claims = []
    claims = list(dict.fromkeys(claim for claim in claims if claim in SKILLS))
    target = row["target"] if row["target"] in GOALS else "Python foundations"
    return {"claims": claims, "target": target}


def save_profile(user_id, claims, target):
    if (not isinstance(claims, list) or len(claims) > len(SKILLS) or
            any(not isinstance(claim, str) or claim not in SKILLS for claim in claims) or
            len(set(claims)) != len(claims)):
        raise ValueError("Choose each skill at most once from the supported list.")
    if not isinstance(target, str) or target not in GOALS:
        raise ValueError("Choose a supported learning goal.")
    with connect() as db:
        db.execute("UPDATE profiles SET claims=?,target=? WHERE user_id=?", (json.dumps(claims), target, user_id))


def assistance(user_id, task_id, hints=None, solution=None):
    if not isinstance(task_id, str) or task_id not in TASK_BY_ID:
        raise ValueError("Unknown task.")
    if hints is not None and (not isinstance(hints, int) or isinstance(hints, bool) or not 0 <= hints <= 3):
        raise ValueError("Hint count must be from 0 to 3.")
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO assistance(user_id,task_id) VALUES(?,?)", (user_id, task_id))
        if hints is not None:
            db.execute("UPDATE assistance SET hints=MAX(hints,?) WHERE user_id=? AND task_id=?", (hints, user_id, task_id))
        if solution:
            db.execute("UPDATE assistance SET solution_seen=1 WHERE user_id=? AND task_id=?", (user_id, task_id))
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


def export_user(user_id):
    with connect() as db:
        rows = db.execute("SELECT attempt_id,comment,created FROM feedback WHERE user_id=?", (user_id,)).fetchall()
    return {"profile": profile(user_id), "attempts": attempts(user_id), "feedback": [dict(r) for r in rows]}
