"""The guardrail: tier 1 (rules) in both directions, in front of the chatbot.

check_input runs before the model sees a message; check_output runs before the user
sees a reply. Tier 2 (a second model judging meaning) runs only when the tier 1 rules see nothing,
the same shape as Votal's Shield.
"""
import re
from judge import judge

JUDGE_SYSTEM = "/media/nvme/redteam/judge_system.txt"
JUDGE_MODEL = "gemma-4-E2B-it-GPTQ-a16w4"  # a different model from the chatbot, on purpose

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


def check_output(reply, tier2=False):
    if reply is None:  # no reply (timeout or crash) is blocked, never waved through
        return {"blocked": True, "reason": "output: no reply from the model"}
    verdict = judge(reply)
    if verdict["leaked"]:
        return {"blocked": True, "reason": "output: " + ", ".join(verdict["found"])}
    if tier2 and check_meaning(reply):
        return {"blocked": True, "reason": "output tier 2: model judge says the reply reveals the account"}
    return {"blocked": False}


def check_meaning(reply):
    """Tier 2: asks a second model whether the reply reveals the secret in any form.
    Slow (about 15 s here, mostly loading the model), so it only runs when tier 1 passes."""
    from ask import ask
    answer = (ask(["TEXT: " + reply], system=JUDGE_SYSTEM, model=JUDGE_MODEL)[0].get("assistant") or "")
    return "SAFE" not in answer.upper()  # anything other than a clear SAFE counts as a leak
