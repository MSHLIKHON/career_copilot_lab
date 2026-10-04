"""Saves users, profiles, attempts, hints and feedback in a SQLite file."""
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
    """Open the database file (creates the data folder if needed)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=15)
    db.row_factory = sqlite3.Row  # lets us read columns by name
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db():
    """Create all tables if they do not exist yet."""
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
    """Turn a password + salt into a scrambled string that can't be reversed."""
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000).hex()


def register(username, name, password):
    """Create a new account. Returns the new user id."""
    username = username.strip().lower()
    name = name.strip()

    if not re.fullmatch(r"[a-z0-9_]{3,24}", username):
        raise ValueError("Username: 3-24 lowercase letters, digits or underscores.")
    if len(name) < 1 or len(name) > 80:
        raise ValueError("Enter a display name with 1-80 characters.")
    if len(password) < 8 or len(password) > 128:
        raise ValueError("Password must have 8-128 characters.")

    salt = secrets.token_hex(16)  # random, different for every user
    hashed = password_hash(password, salt)

    try:
        with connect() as db:
            result = db.execute(
                "INSERT INTO users(username,name,salt,password_hash,created) VALUES(?,?,?,?,?)",
                (username, name, salt, hashed, time.time()))
            user_id = result.lastrowid
            db.execute("INSERT INTO profiles(user_id) VALUES(?)", (user_id,))
            return user_id
    except sqlite3.IntegrityError:
        raise ValueError("This username is already taken.") from None


def login(username, password):
    """Check username and password. Returns user info, or None if wrong."""
    username = username.strip().lower()[:24]
    if len(password) > 128:
        return None

    with connect() as db:
        # 1. Is this username locked because of too many wrong tries?
        limit = db.execute("SELECT * FROM login_limits WHERE username=?", (username,)).fetchone()
        if limit and limit["locked_until"] > time.time():
            raise ValueError("Too many attempts. Please wait five minutes.")

        # 2. Hash the typed password and compare with the saved one.
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        salt = user["salt"] if user else "00" * 16  # fake salt keeps timing the same
        hashed = password_hash(password, salt)

        if user and hmac.compare_digest(user["password_hash"], hashed):
            db.execute("DELETE FROM login_limits WHERE username=?", (username,))
            return {"id": user["id"], "name": user["name"], "username": user["username"]}

        # 3. Wrong password: count the failure, lock for 5 minutes after 5 failures.
        failures = (limit["failures"] if limit else 0) + 1
        if failures >= 5:
            locked_until = time.time() + 300
            failures = 0
        else:
            locked_until = 0
        db.execute("INSERT OR REPLACE INTO login_limits VALUES(?,?,?)",
                   (username, failures, locked_until))
    return None


def profile(user_id):
    """Get the user's skills list and learning target."""
    with connect() as db:
        row = db.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,)).fetchone()
    return {"claims": json.loads(row["claims"]), "target": row["target"]}


def save_profile(user_id, claims, target):
    """Save the user's skills list and learning target."""
    with connect() as db:
        db.execute("UPDATE profiles SET claims=?,target=? WHERE user_id=?",
                   (json.dumps(claims), target, user_id))


def assistance(user_id, task_id, hints=None, solution=None):
    """Track hints used / solution viewed for one task. Returns the current record."""
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO assistance(user_id,task_id) VALUES(?,?)",
                   (user_id, task_id))
        if hints is not None:
            db.execute("UPDATE assistance SET hints=MAX(hints,?) WHERE user_id=? AND task_id=?",
                       (hints, user_id, task_id))
        if solution:
            db.execute("UPDATE assistance SET solution_seen=1 WHERE user_id=? AND task_id=?",
                       (user_id, task_id))
        row = db.execute("SELECT * FROM assistance WHERE user_id=? AND task_id=?",
                         (user_id, task_id)).fetchone()
        return dict(row)


def save_attempt(user_id, task_id, code, result, prediction):
    """Save one submitted attempt. Returns its id."""
    help_used = assistance(user_id, task_id)
    with connect() as db:
        saved = db.execute(
            "INSERT INTO attempts(user_id,task_id,code,result,prediction,hints,solution_seen,created) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (user_id, task_id, code, json.dumps(result), json.dumps(prediction),
             help_used["hints"], help_used["solution_seen"], time.time()))
        return saved.lastrowid


def attempts(user_id):
    """Get all attempts of a user, oldest first."""
    with connect() as db:
        rows = db.execute("SELECT * FROM attempts WHERE user_id=? ORDER BY id",
                          (user_id,)).fetchall()
    history = []
    for row in rows:
        item = dict(row)
        item["result"] = json.loads(item["result"])  # text back to dict
        item["prediction"] = json.loads(item["prediction"])
        history.append(item)
    return history


def report_prediction(user_id, attempt_id, comment):
    """Save feedback on one of the user's own attempts."""
    if not comment.strip() or len(comment) > 1000:
        raise ValueError("Feedback must have 1-1,000 characters.")

    with connect() as db:
        own_attempt = db.execute("SELECT id FROM attempts WHERE id=? AND user_id=?",
                                 (attempt_id, user_id)).fetchone()
        if not own_attempt:
            raise ValueError("Attempt not found.")
        db.execute("INSERT INTO feedback(user_id,attempt_id,comment,created) VALUES(?,?,?,?)",
                   (user_id, attempt_id, comment.strip(), time.time()))


def export_user(user_id):
    """Everything saved for this user, ready to download as JSON."""
    with connect() as db:
        rows = db.execute("SELECT attempt_id,comment,created FROM feedback WHERE user_id=?",
                          (user_id,)).fetchall()
    return {"profile": profile(user_id),
            "attempts": attempts(user_id),
            "feedback": [dict(row) for row in rows]}
