import sqlite3

from langgraph.checkpoint.sqlite import (
    SqliteSaver
)


connection = sqlite3.connect(
    "checkpoints.db",
    check_same_thread=False
)

checkpointer = SqliteSaver(connection)
