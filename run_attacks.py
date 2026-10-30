"""Replays every attack in attacks.json against the Modalix chatbot and scores it twice:
without the guardrail (did the raw reply leak?) and with it (did anything get through?).

Run: python3 run_attacks.py   Results are also saved to results/<time>.json
"""
import json, os, time
from ask import ask
from guardrail import check_input, check_output
from judge import judge

attacks = json.load(open("attacks.json"))
results = []
for a in attacks:
    t0 = time.time()
    replies = ask(a["turns"])
    reply = " ".join(r.get("assistant") or "" for r in replies)
    raw = judge(reply)

    # With the guardrail: an input block stops the attack before the model runs.
    blocked_in = next((check_input(t) for t in a["turns"] if check_input(t)["blocked"]), None)
    out = check_output(reply)
    if blocked_in:
        guarded = f"BLOCKED ({blocked_in['reason']})"
    elif out["blocked"]:
        guarded = f"BLOCKED ({out['reason']})"
    else:
        guarded = "got through, no leak detected"

    results.append({**a, "reply": reply, "raw_leak": raw, "guarded": guarded})
    print(f"#{a['id']:<2} {a['technique']:<42} no guard: {'LEAK ' + ', '.join(raw['found']) if raw['leaked'] else 'no leak'}")
    print(f"    {'':<42} guarded:  {guarded}   ({time.time() - t0:.0f}s)")
    print(f"    reply: {reply[:160]!r}\n")

os.makedirs("results", exist_ok=True)
path = f"results/{time.strftime('%Y%m%d-%H%M%S')}.json"
json.dump(results, open(path, "w"), indent=2, ensure_ascii=False)
print(f"saved {path}")
