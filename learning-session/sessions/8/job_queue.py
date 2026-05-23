import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).with_name("jobs.db")


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_path TEXT NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def enqueue_ingestion_job(document_path):
    now = datetime.now().isoformat(timespec="seconds")
    conn = connect_db()
    cursor = conn.execute(
        """
        INSERT INTO ingestion_jobs (
            document_path,
            status,
            error,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            str(document_path),
            "queued",
            None,
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


def claim_next_ingestion_job():
    conn = connect_db()
    row = conn.execute(
        """
        SELECT id, document_path
        FROM ingestion_jobs
        WHERE status = 'queued'
        ORDER BY id
        LIMIT 1
        """
    ).fetchone()

    if not row:
        conn.close()
        return None

    job_id, document_path = row
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        """
        UPDATE ingestion_jobs
        SET status = 'running', updated_at = ?
        WHERE id = ?
        """,
        (now, job_id),
    )
    conn.commit()
    conn.close()

    return {
        "id": job_id,
        "document_path": document_path,
    }


def complete_ingestion_job(job_id):
    update_ingestion_job(job_id, "completed", None)


def fail_ingestion_job(job_id, error):
    update_ingestion_job(job_id, "failed", error)


def update_ingestion_job(job_id, status, error):
    now = datetime.now().isoformat(timespec="seconds")
    conn = connect_db()
    conn.execute(
        """
        UPDATE ingestion_jobs
        SET status = ?, error = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            status,
            error,
            now,
            job_id,
        ),
    )
    conn.commit()
    conn.close()


def list_ingestion_jobs():
    conn = connect_db()
    rows = conn.execute(
        """
        SELECT id, document_path, status, error, created_at, updated_at
        FROM ingestion_jobs
        ORDER BY id DESC
        """
    ).fetchall()
    conn.close()

    return [
        {
            "id": job_id,
            "document_path": document_path,
            "status": status,
            "error": error,
            "created_at": created_at,
            "updated_at": updated_at,
        }
        for job_id, document_path, status, error, created_at, updated_at in rows
    ]
