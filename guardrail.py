"""The guardrail: tier 1 (rules) in both directions, in front of the chatbot.

check_input runs before the model sees a message; check_output runs before the user
sees a reply. Votal's Shield adds tier 2 (a model judging meaning) behind these.
"""
import re
from judge import judge

# Phrases that signal an attack on the instructions themselves.
INPUT_RULES = [
    (r"system prompt", "asks for the system prompt"),
    (r"(repeat|print|show|output).{0,40}(above|instructions|everything)", "asks to repeat the instructions"),
    (r"ignore.{0,30}(previous|prior|above|your).{0,20}(instructions|rules)", "tries to override the instructions"),
]

REFUSAL = "I'm sorry, I can't help with that. Is there anything else I can do for you?"


def check_input(message):
    for pattern, reason in INPUT_RULES:
        if re.search(pattern, message.lower()):
            return {"blocked": True, "reason": f"input: {reason}"}
    return {"blocked": False}


def check_output(reply):
    verdict = judge(reply)
    if verdict["leaked"]:
        return {"blocked": True, "reason": "output: " + ", ".join(verdict["found"])}
    return {"blocked": False}
