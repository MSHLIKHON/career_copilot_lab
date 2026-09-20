import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from pathlib import Path

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
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
            created REAL NOT NULL);
        ''')


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000).hex()


def register(username, name, password):
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
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("This username is already taken.") from None


def login(username, password):
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
    return {"claims": json.loads(row["claims"]), "target": row["target"]}


def save_profile(user_id, claims, target):
    with connect() as db:
        db.execute("UPDATE profiles SET claims=?,target=? WHERE user_id=?", (json.dumps(claims), target, user_id))


def assistance(user_id, task_id, hints=None, solution=None):
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO assistance(user_id,task_id) VALUES(?,?)", (user_id, task_id))
        if hints is not None:
            db.execute("UPDATE assistance SET hints=MAX(hints,?) WHERE user_id=? AND task_id=?", (hints, user_id, task_id))
        if solution:
            db.execute("UPDATE assistance SET solution_seen=1 WHERE user_id=? AND task_id=?", (user_id, task_id))
        return dict(db.execute("SELECT * FROM assistance WHERE user_id=? AND task_id=?", (user_id, task_id)).fetchone())


def save_attempt(user_id, task_id, code, result, prediction):
    help_used = assistance(user_id, task_id)
    with connect() as db:
        cur = db.execute("INSERT INTO attempts(user_id,task_id,code,result,prediction,hints,solution_seen,created) VALUES(?,?,?,?,?,?,?,?)",
                         (user_id, task_id, code, json.dumps(result), json.dumps(prediction),
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
    if not comment.strip() or len(comment) > 1000:
        raise ValueError("Feedback must have 1-1,000 characters.")
    with connect() as db:
        if not db.execute("SELECT id FROM attempts WHERE id=? AND user_id=?", (attempt_id, user_id)).fetchone():
            raise ValueError("Attempt not found.")
        db.execute("INSERT INTO feedback(user_id,attempt_id,comment,created) VALUES(?,?,?,?)", (user_id, attempt_id, comment.strip(), time.time()))


def export_user(user_id):
    with connect() as db:
        rows = db.execute("SELECT attempt_id,comment,created FROM feedback WHERE user_id=?", (user_id,)).fetchall()
    return {"profile": profile(user_id), "attempts": attempts(user_id), "feedback": [dict(r) for r in rows]}


def create_session(user_id):
    token = secrets.token_urlsafe(32)
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO sessions(token, user_id, created) VALUES(?,?,?)",
                   (token, user_id, time.time()))
    return token


def get_user_by_session(token):
    if not token or not isinstance(token, str):
        return None
    with connect() as db:
        row = db.execute(
            "SELECT u.id, u.name, u.username, s.created FROM sessions s JOIN users u ON s.user_id = u.id WHERE s.token = ?",
            (token,),
        ).fetchone()
        if row:
            if time.time() - row["created"] > 30 * 86400:
                db.execute("DELETE FROM sessions WHERE token = ?", (token,))
                return None
            return {"id": row["id"], "name": row["name"], "username": row["username"]}
    return None


def delete_session(token):
    if not token or not isinstance(token, str):
        return
    with connect() as db:
        db.execute("DELETE FROM sessions WHERE token = ?", (token,))

