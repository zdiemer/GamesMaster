from typing import List


class InputHelper:
    @staticmethod
    def boolean_input(question: str) -> bool:
        res = input(f"{question} (y/n): ")

        while res.strip().lower() not in ("y", "n"):
            res = input("Invalid input. Enter only (y/n): ")

        return res.strip().lower() == "y"

    @staticmethod
    def multiple_choice_input(question: str, choices: List[str]) -> str:
        choice_str = ""

        for i, choice in enumerate(choices):
            choice_str += f"{i + 1}. {choice}"

            if i + 1 < len(choices):
                choice_str += "\n"

        res = input(f"{question}\n\n{choice_str}\nEnter choice: ")

        while True:
            try:
                res_int = int(res.strip())
            except ValueError:
                res = input(f"'{res}' is not a valid choice: ")
                continue

            if res_int < 0 or res_int > len(choices):
                res = input(f"'{res}' is not a valid choice: ")
                continue

            return choices[res_int - 1]
