"""SQLite ma'lumotlar bazasi — ulanish, sxema va ma'lumotга kirish funksiyalari.

MVP uchun bitta ulanish + qulf (write'lar uchun). WAL rejimi bilan o'qish parallel.
CLAUDE saboqi: SQLite avtoinc PK faqat INTEGER bo'lsin; sxema o'zi migratsiya bo'lmaydi.
"""
import json
import secrets
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

# DB yo'li: env (DB_PATH) berilса o'sha (Railway volume uchun), aks holда backend/argus_tutor.db
DB_PATH = Path(settings.db_path) if settings.db_path else (
    Path(__file__).resolve().parent.parent / "argus_tutor.db"
)

# Kunlik hisoblagich ustunlari — faqat shu nomlar SQL'ga qo'yiladi (foydalanuvchi kiritmaydi)
_COUNTERS = {"sessions_started", "llm_calls"}

_conn: sqlite3.Connection | None = None
# Reentrant qulf: bitta umumiy ulanish HECH QACHON parallel ishlatilmasin.
# Sabab: qulfsiz o'qish yozuv bilan bir vaqtда ishlaganда sqlite3.InterfaceError beradi
# (konkurentlik testи bilan isbotlangan). Shuning uchun O'QISH ham, YOZISH ham shu qulf ostида.
_lock = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def today() -> str:
    """Bugungi kun (UTC) — kunlik limit uchun. Timestamp'lar ham UTC (izchillik)."""
    return datetime.now(timezone.utc).date().isoformat()


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # volume yo'li uchun
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
    return _conn


def init_db() -> None:
    """Sxemani yaratish (agar yo'q bo'lsa) + yengil migratsiya."""
    conn = get_conn()
    with _lock:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id          TEXT PRIMARY KEY,
                device_id   TEXT,
                name        TEXT,
                goal        TEXT,
                level       TEXT,
                token       TEXT UNIQUE NOT NULL,
                is_premium  INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                scenario_id TEXT,
                level       TEXT,
                user_turns  INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT NOT NULL,
                role        TEXT NOT NULL,
                text        TEXT NOT NULL,
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS daily_usage (
                user_id          TEXT NOT NULL,
                day              TEXT NOT NULL,
                sessions_started INTEGER NOT NULL DEFAULT 0,
                llm_calls        INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, day)
            );

            CREATE TABLE IF NOT EXISTS events (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT,
                type       TEXT NOT NULL,
                payload    TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS waitlist (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                email      TEXT UNIQUE NOT NULL,
                source     TEXT,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id);
            """
        )
        # Migratsiya: eski daily_usage'да llm_calls bo'lmasa qo'shamiz
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(daily_usage)")}
        if "llm_calls" not in cols:
            conn.execute("ALTER TABLE daily_usage ADD COLUMN llm_calls INTEGER NOT NULL DEFAULT 0")
        # Migratsiya: eski sessions'да user_turns bo'lmasa qo'shamiz
        scols = {r["name"] for r in conn.execute("PRAGMA table_info(sessions)")}
        if "user_turns" not in scols:
            conn.execute("ALTER TABLE sessions ADD COLUMN user_turns INTEGER NOT NULL DEFAULT 0")
        conn.commit()


# ---------------- Users ----------------

def create_user(device_id: str | None, name: str | None, goal: str | None) -> sqlite3.Row:
    """Har doim YANGI foydalanuvchи yaratadi. device_id faqat metadata (auth uchun emas).

    Token — yagona hisob kaliti; klient uni xavfsiz saqlaydi. (Xavfsizlik: device_id
    bo'yicha token qaytarmaymiz — aks holda hisob o'g'irlanadi.)
    """
    conn = get_conn()
    uid = uuid.uuid4().hex
    token = secrets.token_urlsafe(32)
    with _lock:
        conn.execute(
            "INSERT INTO users (id, device_id, name, goal, token, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (uid, device_id, name, goal, token, _now()),
        )
        conn.commit()
    return get_user_by_id(uid)


def get_user_by_token(token: str) -> sqlite3.Row | None:
    conn = get_conn()
    with _lock:
        cur = conn.execute("SELECT * FROM users WHERE token = ?", (token,))
        return cur.fetchone()


def get_user_by_id(uid: str) -> sqlite3.Row | None:
    conn = get_conn()
    with _lock:
        cur = conn.execute("SELECT * FROM users WHERE id = ?", (uid,))
        return cur.fetchone()


def update_user_level(uid: str, level: str) -> None:
    conn = get_conn()
    with _lock:
        conn.execute("UPDATE users SET level = ? WHERE id = ?", (level, uid))
        conn.commit()


# ---------------- Sessions & messages ----------------

def create_session(user_id: str, scenario_id: str, level: str | None) -> str:
    conn = get_conn()
    sid = uuid.uuid4().hex[:12]
    with _lock:
        conn.execute(
            "INSERT INTO sessions (id, user_id, scenario_id, level, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (sid, user_id, scenario_id, level, _now()),
        )
        conn.commit()
    return sid


def get_session(session_id: str) -> sqlite3.Row | None:
    conn = get_conn()
    with _lock:
        cur = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        return cur.fetchone()


def add_message(session_id: str, role: str, text: str) -> None:
    conn = get_conn()
    with _lock:
        conn.execute(
            "INSERT INTO messages (session_id, role, text, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, text, _now()),
        )
        conn.commit()


def get_history(session_id: str, limit: int | None = None) -> list[dict]:
    """[{'role': 'user'|'model', 'text': ...}] — vaqt bo'yicha tartibda.

    limit berilsa — oxirgi `limit` ta xabar (narx cheklovi uchun oyna).
    """
    conn = get_conn()
    with _lock:
        if limit is None:
            cur = conn.execute(
                "SELECT role, text FROM messages WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            )
            rows = cur.fetchall()
        else:
            cur = conn.execute(
                "SELECT role, text FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            )
            rows = list(reversed(cur.fetchall()))
    return [{"role": r["role"], "text": r["text"]} for r in rows]


def count_user_turns(session_id: str) -> int:
    conn = get_conn()
    with _lock:
        cur = conn.execute(
            "SELECT COUNT(*) AS c FROM messages WHERE session_id = ? AND role = 'user'",
            (session_id,),
        )
        return cur.fetchone()["c"]


# ---------------- Kunlik limit (ATOMIK — TOCTOU'siz) ----------------

def try_consume(user_id: str, counter: str, limit: int) -> bool:
    """Atomik: agar bugungi `counter` < limit bo'lsa, +1 qilib True qaytaradi; aks holda False.

    Butun tekshirish+increment BITTA qulf ostida — konkurent so'rovlar ketma-ket bo'ladi
    (TOCTOU race yo'q). `counter` faqat ichki oq ro'yxatдан (foydalanuvchи kiritmaydi).
    """
    if counter not in _COUNTERS:
        raise ValueError(f"noma'lum hisoblagich: {counter}")
    conn = get_conn()
    with _lock:
        conn.execute(
            "INSERT OR IGNORE INTO daily_usage (user_id, day) VALUES (?, ?)",
            (user_id, today()),
        )
        cur = conn.execute(
            f"UPDATE daily_usage SET {counter} = {counter} + 1 "
            f"WHERE user_id = ? AND day = ? AND {counter} < ?",
            (user_id, today(), limit),
        )
        conn.commit()
        return cur.rowcount == 1


def refund(user_id: str, counter: str) -> None:
    """Rezerv qilingan hisobни qaytarish (masalan LLM chaqiruvi muvaffaqiyatsiz bo'lса)."""
    if counter not in _COUNTERS:
        raise ValueError(f"noma'lum hisoblagich: {counter}")
    conn = get_conn()
    with _lock:
        conn.execute(
            f"UPDATE daily_usage SET {counter} = MAX(0, {counter} - 1) "
            f"WHERE user_id = ? AND day = ?",
            (user_id, today()),
        )
        conn.commit()


def try_reserve_turn(session_id: str, limit: int) -> bool:
    """Atomik: sessiya navbatи < limit bo'lsa +1 qilib True; aks holda False.

    TOCTOU'siz — bitta conditional UPDATE qulf ostида (try_consume kabi).
    """
    conn = get_conn()
    with _lock:
        cur = conn.execute(
            "UPDATE sessions SET user_turns = user_turns + 1 WHERE id = ? AND user_turns < ?",
            (session_id, limit),
        )
        conn.commit()
        return cur.rowcount == 1


def refund_turn(session_id: str) -> None:
    """Rezerv qilingan navbatни qaytarish (LLM yiqilса)."""
    conn = get_conn()
    with _lock:
        conn.execute(
            "UPDATE sessions SET user_turns = MAX(0, user_turns - 1) WHERE id = ?",
            (session_id,),
        )
        conn.commit()


def get_today_usage(user_id: str) -> sqlite3.Row | None:
    """Bugungi (sessions_started, llm_calls) — /auth/me uchun."""
    conn = get_conn()
    with _lock:
        cur = conn.execute(
            "SELECT sessions_started, llm_calls FROM daily_usage WHERE user_id = ? AND day = ?",
            (user_id, today()),
        )
        return cur.fetchone()


# ---------------- Analytics ----------------

def add_waitlist(email: str, source: str | None) -> bool:
    """Waitlist'ga email qo'shadi. Yangi bo'lsa True, allaqachon bor bo'lsa False."""
    conn = get_conn()
    with _lock:
        cur = conn.execute(
            "INSERT OR IGNORE INTO waitlist (email, source, created_at) VALUES (?, ?, ?)",
            (email.lower().strip(), source, _now()),
        )
        conn.commit()
        return cur.rowcount == 1


def waitlist_count() -> int:
    conn = get_conn()
    with _lock:
        return conn.execute("SELECT COUNT(*) AS c FROM waitlist").fetchone()["c"]


def log_event(user_id: str | None, type_: str, payload: dict | None = None) -> None:
    conn = get_conn()
    with _lock:
        conn.execute(
            "INSERT INTO events (user_id, type, payload, created_at) VALUES (?, ?, ?, ?)",
            (user_id, type_, json.dumps(payload) if payload else None, _now()),
        )
        conn.commit()
