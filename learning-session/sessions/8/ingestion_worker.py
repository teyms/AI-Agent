from logging_config import logger
from job_queue import (
    claim_next_ingestion_job,
    complete_ingestion_job,
    fail_ingestion_job,
)
from sqlite_vec_store import ingest_document


def process_next_ingestion_job():
    job = claim_next_ingestion_job()
    if not job:
        print("No queued ingestion jobs.")
        return None

    try:
        chunk_count = ingest_document(job["document_path"])
        complete_ingestion_job(job["id"])
        logger.info(
            f"Ingestion job {job['id']} completed with {chunk_count} chunks"
        )
        return {
            "job_id": job["id"],
            "status": "completed",
            "chunks": chunk_count,
        }
    except Exception as e:
        fail_ingestion_job(job["id"], str(e))
        logger.error(
            f"Ingestion job {job['id']} failed: {str(e)}"
        )
        return {
            "job_id": job["id"],
            "status": "failed",
            "error": str(e),
        }


if __name__ == "__main__":
    print(process_next_ingestion_job())
