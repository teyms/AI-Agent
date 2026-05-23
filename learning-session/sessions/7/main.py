from memory import clear_memory
from agent import run_agent
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

    answer = run_agent(question)

    print("\nAnswer:")
    print(answer)
