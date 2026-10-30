"""Runs the attack library across several Tenki sandboxes at once, several times per attack,
and reports a leak RATE per attack instead of a single yes or no.

Usage: python3 sandbox/fanout.py [repeats per sandbox]   (from the repo root)
Needs the tenki CLI signed in, and sandboxes set up by hand (see PROJECT_LOG.md, step 6).
"""
import json, subprocess, sys, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

SESSIONS = ["redteam-base"] + [f"redteam-fork-{i}" for i in range(1, 5)]
REPEATS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
attacks = json.load(open("attacks.json"))


def run(session):
    batch = json.dumps(attacks * REPEATS)
    cmd = ["tenki", "sandbox", "exec", "--session", session, "-c",
           f"cd /home/tenki/redteam && echo '{batch.replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}' | python3 env.py"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    return [dict(json.loads(l), session=session) for l in out.splitlines() if l.startswith("{")]


t0 = time.time()
with ThreadPoolExecutor(len(SESSIONS)) as pool:
    rows = [r for batch in pool.map(run, SESSIONS) for r in batch]
wall = time.time() - t0

by_id = defaultdict(list)
for r in rows:
    by_id[r["id"]].append(r)
print(f"{len(rows)} episodes on {len(SESSIONS)} sandboxes in {wall:.0f}s wall clock "
      f"({sum(r['seconds'] for r in rows):.0f}s of chatbot time)\n")
for a in attacks:
    rs = by_id[a["id"]]
    scored = [r["reward"] for r in rs if r["reward"] is not None]
    rate = sum(scored) / len(scored) if scored else float("nan")
    print(f"#{a['id']:<3} {a['technique']:<46} leak rate {sum(scored)}/{len(scored)}  {'#' * round(rate * 10)}")

json.dump(rows, open(f"results/fanout-{time.strftime('%Y%m%d-%H%M%S')}.json", "w"), indent=2, ensure_ascii=False)
