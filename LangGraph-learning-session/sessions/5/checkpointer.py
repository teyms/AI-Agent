import sqlite3
from datetime import datetime, timedelta, timezone

from langgraph.checkpoint.sqlite import (
    SqliteSaver
)

connection = sqlite3.connect(
    "checkpoints.db",
    check_same_thread=False
)

checkpointer = SqliteSaver(connection)


def cleanup_old_checkpoints(retention_days=7):
    try:
        cutoff = (
            datetime.now(timezone.utc)
            - timedelta(days=retention_days)
        )
    except OverflowError:
        cutoff = datetime.min.replace(
            tzinfo=timezone.utc
        )

    rows = connection.execute(
        """
        SELECT
            thread_id,
            checkpoint_ns,
            checkpoint_id,
            type,
            checkpoint
        FROM checkpoints
        """
    ).fetchall()

    expired = []

    for row in rows:
        (
            thread_id,
            checkpoint_ns,
            checkpoint_id,
            checkpoint_type,
            checkpoint_blob
        ) = row
        checkpoint = checkpointer.serde.loads_typed(
            (
                checkpoint_type,
                checkpoint_blob
            )
        )
        checkpoint_time = datetime.fromisoformat(
            checkpoint["ts"]
        )

        if checkpoint_time < cutoff:
            expired.append(
                (
                    thread_id,
                    checkpoint_ns,
                    checkpoint_id
                )
            )

    for expired_row in expired:
        connection.execute(
            """
            DELETE FROM writes
            WHERE thread_id = ?
              AND checkpoint_ns = ?
              AND checkpoint_id = ?
            """,
            expired_row
        )
        connection.execute(
            """
            DELETE FROM checkpoints
            WHERE thread_id = ?
              AND checkpoint_ns = ?
              AND checkpoint_id = ?
            """,
            expired_row
        )

    connection.commit()
    return len(expired)
