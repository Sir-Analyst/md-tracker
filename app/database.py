import sqlite3
from datetime import datetime
from pathlib import Path
from app.config import DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            path TEXT UNIQUE NOT NULL,
            added_at TEXT DEFAULT (datetime('now')),
            last_opened TEXT
        );
        CREATE TABLE IF NOT EXISTS steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            step_index INTEGER NOT NULL,
            title TEXT NOT NULL,
            level TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            completed_at TEXT,
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        );
    """)
    conn.close()


def add_file(name: str, path: str) -> dict:
    conn = get_conn()
    try:
        conn.execute("INSERT INTO files (name, path) VALUES (?, ?)", (name, path))
        conn.commit()
        file_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        return get_file(file_id, conn=conn)
    except sqlite3.IntegrityError:
        row = conn.execute("SELECT * FROM files WHERE path = ?", (path,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_file(file_id: int, conn=None) -> dict | None:
    should_close = conn is None
    if conn is None:
        conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
        return dict(row) if row else None
    finally:
        if should_close:
            conn.close()


def list_files() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM files ORDER BY last_opened DESC NULLS LAST").fetchall()
        result = []
        for row in rows:
            f = dict(row)
            stats = get_file_stats(f["id"], conn=conn)
            f.update(stats)
            result.append(f)
        return result
    finally:
        conn.close()


def delete_file(file_id: int) -> bool:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def touch_file(file_id: int):
    conn = get_conn()
    try:
        conn.execute("UPDATE files SET last_opened = datetime('now') WHERE id = ?", (file_id,))
        conn.commit()
    finally:
        conn.close()


def get_steps(file_id: int) -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM steps WHERE file_id = ? ORDER BY step_index", (file_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def upsert_steps(file_id: int, steps: list[dict]):
    conn = get_conn()
    try:
        existing = {
            r["step_index"]: dict(r)
            for r in conn.execute("SELECT * FROM steps WHERE file_id = ?", (file_id,)).fetchall()
        }
        existing_indices = set(existing.keys())
        new_indices = {s["step_index"] for s in steps}

        for idx in existing_indices - new_indices:
            conn.execute("DELETE FROM steps WHERE id = ?", (existing[idx]["id"],))

        for step in steps:
            idx = step["step_index"]
            if idx in existing:
                conn.execute(
                    "UPDATE steps SET title = ?, level = ? WHERE id = ?",
                    (step["title"], step["level"], existing[idx]["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO steps (file_id, step_index, title, level) VALUES (?, ?, ?, ?)",
                    (file_id, idx, step["title"], step["level"]),
                )
        conn.commit()
    finally:
        conn.close()


def toggle_step(step_id: int) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM steps WHERE id = ?", (step_id,)).fetchone()
        if not row:
            return None
        new_val = 0 if row["completed"] else 1
        completed_at = datetime.now().isoformat() if new_val else None
        conn.execute(
            "UPDATE steps SET completed = ?, completed_at = ? WHERE id = ?",
            (new_val, completed_at, step_id),
        )
        conn.commit()
        return dict(conn.execute("SELECT * FROM steps WHERE id = ?", (step_id,)).fetchone())
    finally:
        conn.close()


def get_file_stats(file_id: int, conn=None) -> dict:
    should_close = conn is None
    if conn is None:
        conn = get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as done FROM steps WHERE file_id = ?",
            (file_id,),
        ).fetchone()
        total = row["total"] or 0
        done = row["done"] or 0
        pct = round(done / total * 100) if total > 0 else 0
        return {"total_steps": total, "completed_steps": done, "progress_pct": pct}
    finally:
        if should_close:
            conn.close()


def get_global_stats() -> dict:
    conn = get_conn()
    try:
        files_row = conn.execute("SELECT COUNT(*) as c FROM files").fetchone()
        steps_row = conn.execute(
            "SELECT COUNT(*) as total, SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as done FROM steps"
        ).fetchone()
        total = steps_row["total"] or 0
        done = steps_row["done"] or 0
        pct = round(done / total * 100) if total > 0 else 0
        return {
            "total_files": files_row["c"],
            "total_steps": total,
            "completed_steps": done,
            "progress_pct": pct,
        }
    finally:
        conn.close()
