from workflow import run_workflow


def main():
    while True:
        user_input = input("\nUser: ")

        if user_input.lower() == "exit":
            break

        result = run_workflow(user_input)

        print("\nAgent:")
        print(result)


if __name__ == "__main__":
    main()
