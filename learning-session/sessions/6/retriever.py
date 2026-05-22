import sqlite_vec
from openai import OpenAI
from dotenv import load_dotenv
from ingest import connect_db, create_embedding
import json

MAX_DISTANCE = 2.0

import os

load_dotenv()
client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

def can_access_chunk(chunk, user_department):
    if chunk["department"] != "HR":
        print(
            f"can_access_chunk: user_department={user_department}, "
            f"chunk_department={chunk['department']}, allowed=True"
        )
        return True

    allowed = user_department == "HR"
    print(
        f"can_access_chunk: user_department={user_department}, "
        f"chunk_department={chunk['department']}, allowed={allowed}"
    )
    return allowed


def retrieve(query, top_k=3, max_distance=MAX_DISTANCE):

    query_embedding = create_embedding(query, input_type="query")
    db = connect_db()

    results = db.execute(
        """
        SELECT
            chunks.text,
            chunks.parent_text,
            chunks.source,
            chunks.department,
            chunks.document_type,
            chunks.security_level,
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
        )
    ).fetchall()

    db.close()

    return [
        {
            "text": text,
            "source": source,
            "department": department,
            "document_type": document_type,
            "security_level": security_level,
            "score": distance
        }
        for text, parent_text, source, department, document_type, security_level, distance in results
        if distance <= max_distance
    ]


def keyword_search(query, documents):

    matches = []

    query_lower = query.lower()

    for doc in documents:

        if query_lower in doc["text"].lower():

            matches.append(doc)

    return matches


def load_chunks_from_db():
    db = connect_db()

    rows = db.execute(
        """
        SELECT
            text,
            parent_text,
            source,
            department,
            document_type,
            security_level
        FROM chunks
        """
    ).fetchall()

    db.close()

    return [
        {
            "text": text,
            "parent_text": parent_text,
            "source": source,
            "department": department,
            "document_type": document_type,
            "security_level": security_level,
            "score": 0,
        }
        for text, parent_text, source, department, document_type, security_level in rows
    ]


def hybrid_search(query, user_department, top_k=5):
    vector_results = filtered_retrieve(
        query,
        user_department=user_department,
        top_k=top_k,
    )

    all_chunks = load_chunks_from_db()
    keyword_results = keyword_search(
        query,
        all_chunks
    )
    keyword_results = [
        chunk
        for chunk in keyword_results
        if can_access_chunk(chunk, user_department)
    ]

    combined = vector_results + keyword_results

    return sorted(
        deduplicate_chunks(combined),
        key=lambda chunk: chunk["score"],
    )[:top_k]


def rerank(query, retrieved_chunks):

    scored = []

    query_words = set(query.lower().split())

    for chunk in retrieved_chunks:

        chunk_words = set(
            chunk["text"].lower().split()
        )

        overlap = len(
            query_words.intersection(chunk_words)
        )

        scored.append({
            "chunk": chunk,
            "score": overlap
        })

    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return [
        item["chunk"]
        for item in scored[:5]
    ]


def deduplicate_chunks(chunks):
    deduplicated = {}

    for chunk in chunks:
        normalized_text = " ".join(chunk["text"].lower().split())
        key = (chunk["source"], normalized_text)

        if key not in deduplicated:
            deduplicated[key] = chunk
            continue

        if chunk["score"] < deduplicated[key]["score"]:
            deduplicated[key] = chunk

    return list(deduplicated.values())

def filtered_retrieve(
    query,
    user_department,
    department=None,
    document_type=None,
    security_level=None,
    top_k=5,
    max_distance=MAX_DISTANCE,
):
    query_embedding = create_embedding(query, input_type="query")
    db = connect_db()

    filters = []
    params = [
        sqlite_vec.serialize_float32(query_embedding),
        top_k * 10,
    ]

    if department:
        filters.append("chunks.department = ?")
        params.append(department)

    if document_type:
        filters.append("chunks.document_type = ?")
        params.append(document_type)

    if security_level:
        filters.append("chunks.security_level = ?")
        params.append(security_level)

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    results = db.execute(
        f"""
        SELECT
            chunks.text,
            chunks.parent_text,
            chunks.source,
            chunks.department,
            chunks.document_type,
            chunks.security_level,
            matches.distance
        FROM (
            SELECT rowid, distance
            FROM vec_chunks
            WHERE embedding MATCH ?
            ORDER BY distance
            LIMIT ?
        ) AS matches
        JOIN chunks ON chunks.id = matches.rowid
        {where_clause}
        """,
        params,
    ).fetchall()

    db.close()

    chunks = [
        {
            "text": text,
            "parent_text": parent_text,
            "source": source,
            "department": department,
            "document_type": document_type,
            "security_level": security_level,
            "score": distance,
        }
        for text, parent_text, source, department, document_type, security_level, distance in results
        if distance <= max_distance
    ]

    allowed_chunks = [
        chunk
        for chunk in chunks
        if can_access_chunk(chunk, user_department)
    ]

    return allowed_chunks[:top_k]


def rewrite_query(query):

    response = client.chat.completions.create(
        model=(os.getenv("LLM_MODEL") or "").strip().strip("\"'"),
        messages=[
            {
                "role": "system",
                "content": """
Generate 3 rewritten search queries to improve retrieval.
Return ONLY valid JSON in this schema:
{
  "queries": ["query 1", "query 2", "query 3"]
}
"""
            },
            {
                "role": "user",
                "content": query
            }
        ]
    )

    content = response.choices[0].message.content
    data = json.loads(content)
    return data["queries"]


def multi_query_retrieve(query, user_department, top_k=5):
    queries = [query] + rewrite_query(query)
    merged_results = []

    for rewritten_query in queries:
        chunks = hybrid_search(
            rewritten_query,
            user_department=user_department,
            top_k=top_k,
        )

        for chunk in chunks:
            merged_results.append(chunk)

    return sorted(
        deduplicate_chunks(merged_results),
        key=lambda chunk: chunk["score"],
    )[:top_k]


def compress_chunk(chunk, query):

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """
Extract only information relevant
to the query.
"""
            },
            {
                "role": "user",
                "content": f"""
Query:
{query}

Chunk:
{chunk}
"""
            }
        ]
    )

    return response.choices[0].message.content













