"""Runs on the Mac. Sends a conversation to the chatbot on the Modalix and prints the replies.

Usage: python3 ask.py "first message" ["second message" ...]
"""
import json, subprocess, sys

BOARD = "sima@192.168.1.20"

def ask(messages, system="/media/nvme/redteam/system.txt"):
    out = subprocess.run(["ssh", BOARD, f"python3 /media/nvme/redteam/chat_driver.py {system}"],
                         input=json.dumps(messages), capture_output=True, text=True, timeout=600)
    return json.loads(out.stdout.strip().splitlines()[-1])

if __name__ == "__main__":
    for turn in ask(sys.argv[1:]):
        print(f"YOU:     {turn['user']}\nCHATBOT: {turn.get('assistant') or turn.get('error')}\n")
