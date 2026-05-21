import sqlite_vec

from ingest import connect_db, create_embedding

MAX_DISTANCE = 2.0

def retrieve(query, top_k=3, max_distance=MAX_DISTANCE):

    query_embedding = create_embedding(query, input_type="query")
    db = connect_db()

    results = db.execute(
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
        )
    ).fetchall()

    db.close()

    return [
        {
            "text": text,
            "source": source,
            "score": distance
        }
        for text, source, distance in results
        if distance <= max_distance
    ]
