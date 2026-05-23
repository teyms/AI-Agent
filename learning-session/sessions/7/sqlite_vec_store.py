import os
import sqlite3
from pathlib import Path

import httpx
import sqlite_vec
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "vector_store.db"

load_dotenv(BASE_DIR.parents[2] / ".env")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def create_embedding(text, input_type="query"):
    base_url = (os.getenv("LLM_EMBEDDING_BASE_URL") or "").strip().strip("\"'")
    model = (os.getenv("LLM_EMBEDDING_MODEL") or "").strip().strip("\"'")
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
            "input_type": input_type,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    embeddings = data.get("data", [])
    if not embeddings:
        raise RuntimeError(f"No embedding data received: {data}")

    return embeddings[0]["embedding"]


def search_similar(conn, query, top_k=5):
    query_embedding = create_embedding(query, input_type="query")

    return conn.execute(
        """
        SELECT
            chunks.text,
            chunks.source,
            matches.distance
        FROM (
            SELECT rowid, distance
            FROM vec_chunks
            WHERE embedding MATCH ?
            ORDER BY distance
            LIMIT ?
        ) AS matches
        JOIN chunks ON chunks.id = matches.rowid
        """,
        (
            sqlite_vec.serialize_float32(query_embedding),
            top_k,
        ),
    ).fetchall()
