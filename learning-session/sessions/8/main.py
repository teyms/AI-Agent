from memory import clear_memory
from agent import run_agent, recover_run
from persistence import list_unfinished_runs
from job_queue import enqueue_ingestion_job, list_ingestion_jobs
from ingestion_worker import process_next_ingestion_job
# from evaluation import print_evaluation

while True:

    question = input("\nQuestion: ")

    if question.lower() == "exit":
        break

    if question.lower() == "/reset":
        clear_memory()
        print("\nMemory cleared.")
        continue

    if question.lower() == "/eval":
        # print_evaluation()
        continue

    if question.lower() == "/recover":
        unfinished_runs = list_unfinished_runs()

        if not unfinished_runs:
            print("\nNo unfinished runs.")
            continue

        run_id = unfinished_runs[0]["id"]
        print(f"\nRecovering run: {run_id}")
        answer = recover_run(run_id)

        print("\nAnswer:")
        print(answer)
        continue

    if question.lower().startswith("/ingest "):
        document_path = question[len("/ingest "):].strip()
        job_id = enqueue_ingestion_job(document_path)
        print(f"\nQueued ingestion job: {job_id}")
        continue

    if question.lower() == "/work":
        result = process_next_ingestion_job()
        print(result)
        continue

    if question.lower() == "/jobs":
        for job in list_ingestion_jobs():
            print(job)
        continue

    answer = run_agent(question)

    print("\nAnswer:")
    print(answer)
