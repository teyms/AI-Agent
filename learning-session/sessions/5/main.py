from rag import ask_rag
from memory import clear_memory

while True:

    question = input("\nQuestion: ")

    if question.lower() == "exit":
        break

    if question.lower() == "/reset":
        clear_memory()
        print("\nMemory cleared.")
        continue

    answer = ask_rag(question)

    print("\nAnswer:")
    print(answer["answer"])

    print("\nSources:")
    for citation in answer["citations"]:
        print(f"- {citation['source']}")
        print(citation["chunk"])
