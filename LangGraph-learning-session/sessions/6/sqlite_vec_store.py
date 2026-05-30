import sqlite3
import sqlite_vec

import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "rag.db"

load_dotenv(BASE_DIR.parents[2] / ".env")

EMBEDDING_MODEL = os.getenv(
    "LLM_EMBEDDING_MODEL"
)

def init_db():

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.enable_load_extension(True)

    sqlite_vec.load(conn)

    return conn


def ensure_table(
    conn,
    embedding_dimension
):
    row = conn.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'document_embeddings'
        """
    ).fetchone()

    expected_dimension = (
        f"embedding float[{embedding_dimension}]"
    )

    if row:
        table_sql = row[0].lower()
        if (
            expected_dimension not in table_sql
            or "department" not in table_sql
            or "document_type" not in table_sql
        ):
            conn.execute(
                "DROP TABLE document_embeddings"
            )
            row = None

    if not row:
        conn.execute(f"""
            CREATE VIRTUAL TABLE document_embeddings
            USING vec0(
                id INTEGER PRIMARY KEY,
                text_chunk TEXT,
                source TEXT,
                department TEXT,
                document_type TEXT,
                embedding FLOAT[{embedding_dimension}]
            )
        """)

    conn.commit()


def create_embedding(
    text,
    input_type="query"
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
            "input_type": input_type,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    embeddings = data.get("data", [])
    if not embeddings:
        raise RuntimeError(
            f"No embedding data received: {data}"
        )

    return embeddings[0]["embedding"]

def insert_document(
    conn,
    text_chunk,
    source,
    department,
    document_type
):

    embedding = create_embedding(
        text_chunk,
        input_type="passage"
    )

    ensure_table(
        conn,
        len(embedding)
    )

    conn.execute(
        """
        INSERT INTO document_embeddings(
            text_chunk,
            source,
            department,
            document_type,
            embedding
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            text_chunk,
            source,
            department,
            document_type,
            sqlite_vec.serialize_float32(embedding)
        )
    )

    conn.commit()


def search_similar(
    conn,
    query,
    top_k=3,
    department=None,
    document_type=None
):

    query_embedding = create_embedding(
        query,
        input_type="query"
    )

    sql = """
        SELECT
            text_chunk,
            source,
            department,
            document_type,
            distance
        FROM document_embeddings
        WHERE embedding MATCH ?
    """
    params = [
        sqlite_vec.serialize_float32(
            query_embedding
        )
    ]

    if department:
        sql += " AND department = ?"
        params.append(department)

    if document_type:
        sql += " AND document_type = ?"
        params.append(document_type)

    sql += """
        ORDER BY distance
        LIMIT ?
    """
    params.append(top_k)

    results = conn.execute(
        sql,
        params
    ).fetchall()

    return results


def keyword_search(
    conn,
    query,
    top_k=3,
    department=None,
    document_type=None
):
    table_exists = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'document_embeddings'
        """
    ).fetchone()

    if not table_exists:
        return []

    keywords = [
        word
        for word in re.findall(r"\w+", query.lower())
        if len(word) > 2
    ]

    sql = """
        SELECT
            text_chunk,
            source,
            department,
            document_type
        FROM document_embeddings
        WHERE 1 = 1
    """
    params = []

    if department:
        sql += " AND department = ?"
        params.append(department)

    if document_type:
        sql += " AND document_type = ?"
        params.append(document_type)

    rows = conn.execute(
        sql,
        params
    ).fetchall()

    scored = []

    for row in rows:
        text = row[0].lower()
        matches = sum(
            1
            for keyword in keywords
            if keyword in text
        )

        if matches > 0:
            scored.append((
                row[0],
                row[1],
                row[2],
                row[3],
                matches / max(len(keywords), 1)
            ))

    scored.sort(
        key=lambda result: result[4],
        reverse=True
    )

    return scored[:top_k]


def hybrid_search(
    conn,
    query,
    top_k=3,
    department=None,
    document_type=None
):
    combined = {}

    try:
        vector_results = search_similar(
            conn,
            query,
            top_k=top_k,
            department=department,
            document_type=document_type
        )
    except Exception:
        vector_results = []

    for result in vector_results:
        key = (
            result[1],
            result[0]
        )
        vector_score = 1 / (1 + result[4])
        combined[key] = {
            "text": result[0],
            "source": result[1],
            "department": result[2],
            "document_type": result[3],
            "score": vector_score,
            "match_type": "vector"
        }

    keyword_results = keyword_search(
        conn,
        query,
        top_k=top_k,
        department=department,
        document_type=document_type
    )

    for result in keyword_results:
        key = (
            result[1],
            result[0]
        )

        if key in combined:
            combined[key]["score"] += result[4]
            combined[key]["match_type"] = "hybrid"
        else:
            combined[key] = {
                "text": result[0],
                "source": result[1],
                "department": result[2],
                "document_type": result[3],
                "score": result[4],
                "match_type": "keyword"
            }

    ranked = sorted(
        combined.values(),
        key=lambda result: result["score"],
        reverse=True
    )

    return ranked[:top_k]
