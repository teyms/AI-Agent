import os
import sqlite3
from pathlib import Path

import httpx
import sqlite_vec
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "rag.db"
FALLBACK_DB_PATH = BASE_DIR.parent / "6" / "rag.db"

load_dotenv(BASE_DIR.parents[2] / ".env")


def get_db_path():
    if DB_PATH.exists():
        return DB_PATH

    return FALLBACK_DB_PATH


def init_db():
    conn = sqlite3.connect(
        get_db_path()
    )

    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    return conn


def create_embedding(
    text
):
    base_url = (
        os.getenv("LLM_EMBEDDING_BASE_URL")
        or ""
    ).strip().strip("\"'")
    model = (
        os.getenv("LLM_EMBEDDING_MODEL")
        or ""
    ).strip().strip("\"'")
    api_key = os.getenv(
        "LLM_EMBEDDING_API_KEY"
    )

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

    embeddings = data.get(
        "data",
        []
    )

    if not embeddings:
        raise RuntimeError(
            f"No embedding data received: {data}"
        )

    return embeddings[0]["embedding"]


def retrieve_documents(
    query,
    top_k=3
):
    db_path = get_db_path()

    if not db_path.exists():
        return []

    conn = init_db()
    query_embedding = create_embedding(
        query
    )

    results = conn.execute(
        """
        SELECT
            text_chunk,
            source,
            distance
        FROM document_embeddings
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT ?
        """,
        (
            sqlite_vec.serialize_float32(
                query_embedding
            ),
            top_k
        )
    ).fetchall()

    conn.close()

    return [
        {
            "text": result[0],
            "source": result[1],
            "distance": result[2]
        }
        for result in results
    ]
