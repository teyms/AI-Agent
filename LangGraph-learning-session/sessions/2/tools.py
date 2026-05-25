import os
import sqlite3
from datetime import datetime
from pathlib import Path

import httpx
import sqlite_vec
from dotenv import load_dotenv


def get_weather():
    return "30°C and rainy"


def calculator(expression):
    try:
        return str(eval(expression))

    except Exception as e:
        return f"Calculation failed: {str(e)}"
    
def get_current_time():
    return datetime.now()


def create_embedding(text):
    load_dotenv()
    base_url = os.getenv("LLM_EMBEDDING_BASE_URL")
    model = os.getenv("LLM_EMBEDDING_MODEL")
    api_key = os.getenv("LLM_EMBEDDING_API_KEY")

    response = httpx.post(
        f"{base_url.rstrip('/')}/embeddings",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "input": text,
            "input_type": "query",
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["data"][0]["embedding"]


def search_knowledge_base(query):
    db_path = Path(os.getenv(
        "SQLITE_VEC_DB_PATH",
        "../../../learning-session/sessions/8/vector_store.db"
    ))

    if not db_path.exists():
        return "Knowledge base database not found."

    try:
        embedding = create_embedding(query)

        with sqlite3.connect(db_path) as db:
            db.enable_load_extension(True)
            sqlite_vec.load(db)
            db.enable_load_extension(False)

            rows = db.execute(
                """
                SELECT chunks.text, chunks.source
                FROM (
                    SELECT rowid, distance
                    FROM vec_chunks
                    WHERE embedding MATCH ?
                    ORDER BY distance
                    LIMIT 3
                ) AS matches
                JOIN chunks ON chunks.id = matches.rowid
                """,
                (
                    sqlite_vec.serialize_float32(embedding),
                )
            ).fetchall()
    except Exception as e:
        return f"Knowledge base search failed: {str(e)}"

    if not rows:
        return "No knowledge base results found."

    return "\n\n".join(
        f"[{source}] {text}"
        for text, source in rows
    )

