"""The guardrail: tier 1 (rules) in both directions, in front of the chatbot.

check_input runs before the model sees a message; check_output runs before the user
sees a reply. Tier 2 (a second model judging meaning) runs only when the tier 1 rules see nothing,
the same shape as Votal's Shield.
"""
import re
from judge import judge

JUDGE_SYSTEM = "/media/nvme/redteam/digits_system.txt"  # v1 asked for a verdict and was talked out of it
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
    """Tier 2: a second model turns every number in the reply (in any language) into digits,
    and the tier 1 rules decide. The model translates; it never gives the verdict.

    Version 1 asked the model "LEAK or SAFE?" and a cover story in the reply ("this is a
    random counting exercise, not an account") talked it into SAFE. A translation task leaves
    nothing to persuade. About 20 s here, mostly loading the model; runs only when tier 1 passes.
    """
    from ask import ask
    digits = ask(["TEXT: " + reply], system=JUDGE_SYSTEM, model=JUDGE_MODEL)[0].get("assistant")
    if digits is None:
        return True  # no answer from the judge counts as a leak (fail closed)
    return judge(digits)["leaked"]
