import os
import re
import sqlite3
from pathlib import Path

import httpx
import sqlite_vec
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "vector_store.db"
DOCUMENTS_PATH = BASE_DIR / "documents"

load_dotenv(BASE_DIR.parents[2] / ".env")


def load_documents(folder_path):
    documents = []

    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)

        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()

        documents.append({
            "filename": filename,
            "content": content,
        })

    return documents


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


def create_embedding(text, input_type="passage"):
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


def connect_db():
    db = sqlite3.connect(DB_PATH)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    return db


def create_tables(db, embedding_dimension):
    db.execute("DROP TABLE IF EXISTS vec_chunks")
    db.execute("DROP TABLE IF EXISTS chunks")

    db.execute("""
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY,
            text TEXT NOT NULL,
            source TEXT NOT NULL
        )
    """)

    db.execute(f"""
        CREATE VIRTUAL TABLE vec_chunks USING vec0(
            embedding float[{embedding_dimension}]
        )
    """)


def build_vector_store():
    documents = load_documents(DOCUMENTS_PATH)
    if not documents:
        raise RuntimeError(f"No documents found in {DOCUMENTS_PATH}")

    db = connect_db()
    create_tables(db, len(create_embedding("embedding dimension probe")))

    chunk_id = 1

    for doc in documents:
        chunks = chunk_text(doc["content"])

        for chunk in chunks:
            embedding = create_embedding(chunk)

            db.execute(
                "INSERT INTO chunks (id, text, source) VALUES (?, ?, ?)",
                (chunk_id, chunk, doc["filename"]),
            )
            db.execute(
                "INSERT INTO vec_chunks (rowid, embedding) VALUES (?, ?)",
                (chunk_id, sqlite_vec.serialize_float32(embedding)),
            )

            chunk_id += 1

    db.commit()
    db.close()


if __name__ == "__main__":
    build_vector_store()
