from agent import chat
from memory import clear_memory

while True:

    user_input = input("\nUser: ")

    if user_input.lower() == "exit":
        break

    if user_input == "/reset":
        clear_memory()
        print("\nMemory cleared.")
        continue

    response = chat(user_input)

    print("\nAssistant:")
    print(response)
