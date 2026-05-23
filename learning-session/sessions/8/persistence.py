import json
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).with_name("agent_state.db")


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs(
            id TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def save_state(run_id, state, status):
    conn = connect_db()
    conn.execute(
        """
        INSERT OR REPLACE INTO agent_runs
        VALUES (?, ?, ?)
        """,
        (
            run_id,
            json.dumps(state),
            status,
        )
    )
    conn.commit()
    conn.close()


def list_unfinished_runs():
    conn = connect_db()
    rows = conn.execute(
        """
        SELECT id, state, status
        FROM agent_runs
        WHERE status = 'running'
        ORDER BY rowid DESC
        """
    ).fetchall()
    conn.close()

    return [
        {
            "id": run_id,
            "state": json.loads(state),
            "status": status,
        }
        for run_id, state, status in rows
    ]


def load_state(run_id):
    conn = connect_db()
    row = conn.execute(
        """
        SELECT state, status
        FROM agent_runs
        WHERE id = ?
        """,
        (run_id,)
    ).fetchone()
    conn.close()

    if not row:
        return None

    state, status = row
    return {
        "id": run_id,
        "state": json.loads(state),
        "status": status,
    }
