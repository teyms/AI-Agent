import sys
from pathlib import Path

SESSION_1_PATH = Path(__file__).resolve().parents[1] / "learning-session" / "sessions" / "1"
sys.path.append(str(SESSION_1_PATH))

from session1 import call_llm_api, structured_output


def main() -> None:
    ## Session1
    # call_llm_api()
    # structured_output()
    ## Session1

    # Session2
    from agent import run_agent

    while True:

        user_input = input("\nUser: ")

        if user_input.lower() == "exit":
            break

        result = run_agent(user_input)

        print("\nAgent:")
        print(result)
    # Session2
    return []



if __name__ == "__main__":
    main()



# import subprocess
# import json

# def call_codex_api(prompt):
#     """
#     Mimics an OpenAI API call by routing the prompt 
#     through the authenticated Codex CLI.
#     """
#     try:
#         result = subprocess.run(
#             ['codex.cmd', 'exec', prompt],
#             # ['codex', 'exec', prompt],
#             capture_output=True,
#             text=True,
#             check=True,
#             timeout=120,
#             # shell=True $less secure to use, might have issues similar to sql injection 
#         )

#         stdout = result.stdout or ""
#         stderr = result.stderr or ""

#         data = {
#             "stdout": stdout.strip(),
#             "stderr": stderr.strip(),
#             "returncode": result.returncode
#         }
#         print('')
#         print('=========OUTPUT=========')
#         print(json.dumps(data, indent=2))

#     except subprocess.TimeoutExpired:
#         print(json.dumps({
#             "error": "Codex timed out",
#             "stdout": "",
#             "stderr": ""
#         }, indent=2))

#     except subprocess.CalledProcessError as e:
#         print(json.dumps({
#             "error": "Codex failed",
#             "stdout": (e.stdout or "").strip(),
#             "stderr": (e.stderr or "").strip(),
#             "returncode": e.returncode
#         }, indent=2))

# # --- Usage Example ---
# my_prompt = "Who are you."
# # response = call_codex_api(my_prompt)
# # print("Codex Response:\n", response)
# print(call_codex_api("Write a python function to add two numbers"))
    
