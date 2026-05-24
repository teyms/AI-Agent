import json
import sqlite3

DB_PATH = "workflow_state.db"
STATE_ID = "latest"


def init_state_db(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS workflow_state (
            id TEXT PRIMARY KEY,
            state_json TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

class AgentState:

    def __init__(self):

        self.user_input = ""

        self.current_node = "START"

        self.execution_path = []

        self.messages = []

        self.tool_results = []

        self.retrieved_chunks = []

        self.parallel_retrieval_results = {}

        self.summary = ""

        self.last_tool_node = None

        self.retries = 0

        self.max_retries = 3

        self.final_answer = None

        self.completed = False

def load_state():
    state = AgentState()

    with sqlite3.connect(DB_PATH) as db:
        init_state_db(db)
        row = db.execute(
            """
            SELECT state_json
            FROM workflow_state
            WHERE id = ?
            """,
            (STATE_ID,)
        ).fetchone()

    if row:
        state.__dict__.update(
            json.loads(row[0])
        )

    return state        
