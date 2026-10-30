"""The RL environment, running inside one Tenki sandbox. Action in, score out.

Reads attacks as JSON on stdin: [{"id": ..., "turns": [...]}, ...]. For each one it plays the
turns to the local chatbot (Ollama, same Lantern Bank instructions as the Modalix), runs the
tier 1 judge on the reply, and prints one JSON line per attack with the reward:
1 if the chatbot leaked, 0 if not. Standard library only.
"""
import json, sys, time, urllib.request
from judge import judge

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:1.5b"
SYSTEM = open("/home/tenki/redteam/system.txt").read()


def chat(messages):
    body = json.dumps({"model": MODEL, "messages": messages, "stream": False,
                       "options": {"temperature": 0.7, "num_predict": 200}}).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["message"]["content"]


for attack in json.load(sys.stdin):
    t0 = time.time()
    messages, replies = [{"role": "system", "content": SYSTEM}], []
    try:
        for turn in attack["turns"]:
            messages.append({"role": "user", "content": turn})
            reply = chat(messages)
            messages.append({"role": "assistant", "content": reply})
            replies.append(reply)
        text = " ".join(replies)
        verdict = judge(text)
        out = {"id": attack["id"], "reward": int(verdict["leaked"]), "found": verdict["found"], "reply": text}
    except Exception as e:  # an environment that crashes must say so, not score 0 silently
        out = {"id": attack["id"], "reward": None, "error": repr(e)}
    out["seconds"] = round(time.time() - t0, 1)
    print(json.dumps(out, ensure_ascii=False), flush=True)
