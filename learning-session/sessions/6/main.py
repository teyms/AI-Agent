from rag import ask_rag
from memory import clear_memory
from evaluation import print_evaluation

while True:

    question = input("\nQuestion: ")

    if question.lower() == "exit":
        break

    if question.lower() == "/reset":
        clear_memory()
        print("\nMemory cleared.")
        continue

    if question.lower() == "/eval":
        print_evaluation()
        continue

    answer = ask_rag(question)

    print("\nAnswer:")
    print(answer["answer"])

    print("\nSources:")
    for citation in answer["citations"]:
        print(f"- {citation['source']}")
        print(citation["chunk"])
