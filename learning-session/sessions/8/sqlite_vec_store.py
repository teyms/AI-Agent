import os
import re
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


def chunk_text(text):
    chunks = []
    current_chunk = []

    blocks = re.split(r"\n\s*\n", text)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        is_heading = block.startswith("#") or block.endswith(":")

        if is_heading and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = []

        current_chunk.append(block)

        if is_heading:
            continue

        chunks.append("\n\n".join(current_chunk))
        current_chunk = []

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


def ensure_tables(conn, embedding_dimension):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            text TEXT NOT NULL,
            parent_text TEXT NOT NULL,
            source TEXT NOT NULL,
            department TEXT NOT NULL DEFAULT 'General',
            document_type TEXT NOT NULL DEFAULT 'document',
            security_level TEXT NOT NULL DEFAULT 'internal'
        )
    """)

    table_exists = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = 'vec_chunks'
        """
    ).fetchone()

    if not table_exists:
        conn.execute(f"""
            CREATE VIRTUAL TABLE vec_chunks USING vec0(
                embedding float[{embedding_dimension}]
            )
        """)

    conn.commit()


def insert_chunk(conn, text_chunk, parent_text, source):
    embedding = create_embedding(text_chunk, input_type="passage")
    ensure_tables(conn, len(embedding))

    cursor = conn.execute(
        """
        INSERT INTO chunks (
            text,
            parent_text,
            source,
            department,
            document_type,
            security_level
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            text_chunk,
            parent_text,
            source,
            "General",
            "document",
            "internal",
        ),
    )

    conn.execute(
        """
        INSERT INTO vec_chunks (rowid, embedding)
        VALUES (?, ?)
        """,
        (
            cursor.lastrowid,
            sqlite_vec.serialize_float32(embedding),
        ),
    )

    conn.commit()


def ingest_document(document_path):
    path = Path(document_path)
    text = path.read_text(encoding="utf-8")
    chunks = chunk_text(text)
    conn = init_db()

    for chunk in chunks:
        insert_chunk(
            conn,
            text_chunk=chunk,
            parent_text=text,
            source=path.name,
        )

    conn.close()
    return len(chunks)


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
