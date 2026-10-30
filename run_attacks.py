"""Replays every attack in attacks.json against the Modalix chatbot and scores it three ways:
no guardrail (did the raw reply leak?), tier 1 rules only, and tier 1 plus the tier 2 model judge.

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
    texts = [r.get("assistant") for r in replies]
    reply = None if any(t is None for t in texts) else " ".join(texts)
    raw = judge(reply or "")

    # With the guardrail: an input block stops the attack before the model runs.
    blocked_in = next((check_input(t) for t in a["turns"] if check_input(t)["blocked"]), None)
    def verdict(tier2):
        if blocked_in:
            return f"BLOCKED ({blocked_in['reason']})"
        out = check_output(reply, tier2=tier2)
        return f"BLOCKED ({out['reason']})" if out["blocked"] else "got through"

    tier1 = verdict(False)
    tier12 = tier1 if tier1.startswith("BLOCKED") else verdict(True)
    results.append({**a, "reply": reply, "raw_leak": raw, "tier1": tier1, "tier1_plus_2": tier12})
    print(f"#{a['id']:<2} {a['technique']:<40} raw: {'LEAK ' + ', '.join(raw['found']) if raw['leaked'] else 'no leak (by tier 1 rules)'}")
    print(f"    tier 1:     {tier1}\n    tier 1 + 2: {tier12}   ({time.time() - t0:.0f}s)")
    print(f"    reply: {(reply or '<none>')[:150]!r}\n")

os.makedirs("results", exist_ok=True)
path = f"results/{time.strftime('%Y%m%d-%H%M%S')}.json"
json.dump(results, open(path, "w"), indent=2, ensure_ascii=False)
print(f"saved {path}")
