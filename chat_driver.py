"""Runs on the Modalix. Plays a conversation to the board's chatbot and prints the replies as JSON.

Usage: echo '["msg 1", "msg 2"]' | python3 chat_driver.py [system_prompt_file] [model]
"""
import json, os, pty, re, select, subprocess, sys, time

SYSTEM = sys.argv[1] if len(sys.argv) > 1 else "/media/nvme/redteam/system.txt"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "Qwen3-VL-4B-Instruct-GPTQ-a16w4"
ANSWER_TIMEOUT = 120  # the 4B model can run away on some inputs

messages = json.load(sys.stdin)
master, slave = pty.openpty()
proc = subprocess.Popen(["llima", "run", "--mode", "cli", MODEL, "--system_prompt_file", SYSTEM],
                        stdin=slave, stdout=slave, stderr=slave, close_fds=True)
os.close(slave)
buf = ""

def read_until(pattern, timeout):
    global buf
    end = time.time() + timeout
    while time.time() < end:
        m = re.search(pattern, buf, re.S)
        if m:
            return m
        r, _, _ = select.select([master], [], [], 0.5)
        if r:
            try:
                buf += os.read(master, 4096).decode("utf-8", "replace")
            except OSError:
                break
    return None

replies = []
if read_until(r">>> ", 90) is None:
    proc.kill(); print(json.dumps({"error": "model did not start"})); sys.exit(1)
for msg in messages:
    buf = ""
    # Every line break becomes a space: the CLI treats \r as well as \n as "send", so a
    # reply with \r\n line breaks used to reach the judge cut off after its first line.
    os.write(master, (" ".join(msg.splitlines()) + "\n").encode())
    m = read_until(r"Assistant:(.*?)Number of generated tokens", ANSWER_TIMEOUT)
    if m is None:
        replies.append({"user": msg, "assistant": None, "error": "timeout"})
        break
    replies.append({"user": msg, "assistant": m.group(1).strip()})
    read_until(r">>> ", 10)
proc.kill()
print(json.dumps(replies, ensure_ascii=False))
