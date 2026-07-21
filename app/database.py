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
            parent_id INTEGER,
            FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
        );
    """)
    try:
        conn.execute("SELECT parent_id FROM steps LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE steps ADD COLUMN parent_id INTEGER")
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
                    "UPDATE steps SET title = ?, level = ?, parent_id = NULL WHERE id = ?",
                    (step["title"], step["level"], existing[idx]["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO steps (file_id, step_index, title, level) VALUES (?, ?, ?, ?)",
                    (file_id, idx, step["title"], step["level"]),
                )
        conn.commit()

        all_steps = conn.execute(
            "SELECT id, step_index FROM steps WHERE file_id = ?", (file_id,)
        ).fetchall()
        index_to_id = {r["step_index"]: r["id"] for r in all_steps}

        for step in steps:
            parent_index = step.get("parent_index")
            step_db_id = index_to_id.get(step["step_index"])
            if step_db_id and parent_index is not None and parent_index in index_to_id:
                parent_db_id = index_to_id[parent_index]
                if parent_db_id != step_db_id:
                    conn.execute(
                        "UPDATE steps SET parent_id = ? WHERE id = ?",
                        (parent_db_id, step_db_id),
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


def toggle_step_cascade(step_id: int) -> list[dict]:
    conn = get_conn()
    try:
        changed = []
        step = conn.execute("SELECT * FROM steps WHERE id = ?", (step_id,)).fetchone()
        if not step:
            return []

        new_val = 0 if step["completed"] else 1
        completed_at = datetime.now().isoformat() if new_val else None
        conn.execute(
            "UPDATE steps SET completed = ?, completed_at = ? WHERE id = ?",
            (new_val, completed_at, step_id),
        )
        changed.append({"id": step_id, "completed": new_val})

        if new_val == 1:
            _check_children(conn, step_id, changed)
            if step["parent_id"] is not None:
                _check_parent_if_all_siblings_done(conn, step["parent_id"], changed)
        else:
            _uncheck_children(conn, step_id, changed)
            if step["parent_id"] is not None:
                _uncheck_parent_recursive(conn, step["parent_id"], changed)

        conn.commit()
        return changed
    finally:
        conn.close()


def _check_children(conn, parent_id, changed):
    children = conn.execute("SELECT * FROM steps WHERE parent_id = ?", (parent_id,)).fetchall()
    for child in children:
        if child["completed"] == 0:
            completed_at = datetime.now().isoformat()
            conn.execute(
                "UPDATE steps SET completed = 1, completed_at = ? WHERE id = ?",
                (completed_at, child["id"]),
            )
            changed.append({"id": child["id"], "completed": 1})
            _check_children(conn, child["id"], changed)


def _uncheck_children(conn, parent_id, changed):
    children = conn.execute("SELECT * FROM steps WHERE parent_id = ?", (parent_id,)).fetchall()
    for child in children:
        if child["completed"] == 1:
            conn.execute(
                "UPDATE steps SET completed = 0, completed_at = NULL WHERE id = ?",
                (child["id"],),
            )
            changed.append({"id": child["id"], "completed": 0})
            _uncheck_children(conn, child["id"], changed)


def _check_parent_if_all_siblings_done(conn, parent_id, changed):
    parent = conn.execute("SELECT * FROM steps WHERE id = ?", (parent_id,)).fetchone()
    if not parent or parent["completed"] == 1:
        return
    siblings = conn.execute("SELECT * FROM steps WHERE parent_id = ?", (parent_id,)).fetchall()
    if all(s["completed"] == 1 for s in siblings):
        completed_at = datetime.now().isoformat()
        conn.execute(
            "UPDATE steps SET completed = 1, completed_at = ? WHERE id = ?",
            (completed_at, parent_id),
        )
        changed.append({"id": parent_id, "completed": 1})
        if parent["parent_id"] is not None:
            _check_parent_if_all_siblings_done(conn, parent["parent_id"], changed)


def _uncheck_parent_recursive(conn, parent_id, changed):
    parent = conn.execute("SELECT * FROM steps WHERE id = ?", (parent_id,)).fetchone()
    if not parent or parent["completed"] == 0:
        return
    conn.execute(
        "UPDATE steps SET completed = 0, completed_at = NULL WHERE id = ?",
        (parent_id,),
    )
    changed.append({"id": parent_id, "completed": 0})
    if parent["parent_id"] is not None:
        _uncheck_parent_recursive(conn, parent["parent_id"], changed)


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
