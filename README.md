# Red team lab

Learning AI security by building it: a small, hand-made version of the loop that AI red-teaming products run. **Find** an attack that makes a chatbot leak, **block** it with a guardrail, **re-verify** that the same attack now fails.

The target is a fictional bank chatbot running on a SiMa.ai Modalix board (an edge AI computer, no internet) with a made-up customer record it must never reveal. The attacks, the judge and the guardrail run from a laptop.

Built step by step at the Post-Training & RL Buildathon (San Francisco, 30 October 2026). **[PROJECT_LOG.md](PROJECT_LOG.md) is the real story:** every attack tried, what leaked, what was learned, in order.

## Where it stands

| # | Step | Status |
|---|---|---|
| 1 | Chatbot holding a secret | Done |
| 2 | Attack it by hand | 6 of the first 10 attacks leaked |
| 3 | A judge that decides whether a reply leaked | Rules alone: 12/16 on its eval, with the 4 misses (number words, base64, Spanish, French) kept in as known blind spots |
| 4 | A guardrail on input and output | All 6 leaks blocked, no harmless conversation blocked |
| 5 | The loop: attack, patch, replay | A Spanish leak got past the rules; a second model as judge fixed it and caught a French variant too. 10 of 15 attacks leaked; all 10 blocked |
| 6 | Attacks in parallel sandboxes | Tenki: 160 attack episodes on 5 forked sandboxes in under 2 minutes; leak rates per attack. The patched judge was fooled by a cover story, re-patched, and a line-break bug found along the way |
| 7 | Search loop as a stand-in for RL | Rewarding only leaks that beat the guardrail made the search rediscover its language blind spot unprompted, and exposed a judge false positive an RL attacker could exploit. A 3B mutator never improved on the seeds |

## Files

| File | What it is |
|---|---|
| `chat_driver.py` | Runs on the board: plays a conversation to the model, returns replies as JSON |
| `ask.py` | `python3 ask.py "turn 1" ["turn 2" ...]`: talk to the chatbot from the laptop |
| `judge.py` | Did a reply leak? Normalizes disguises (spelled-out digits, filler words) before checking |
| `test_judge.py` | The judge's eval, including the cases it still gets wrong |
| `guardrail.py` | Tier 1 checks on the input and the output |
| `attacks.json` | The attack library |
| `run_attacks.py` | Replays every attack, scored with and without the guardrail |
| `board/` | The prompt files used on the Modalix (chatbot instructions, judge versions, hardened prompt) |
| `sandbox/env.py` | The RL environment inside a Tenki sandbox: attacks in, reward out |
| `sandbox/fanout.py` | Runs the attack library across forked sandboxes and reports leak rates |
| `sandbox/search.py`, `sandbox/mutate.py` | The search loop and the variant writer |
| `results/` | Saved replay runs |

## Notes

- The bank, the customer and the account number are invented.
- The model is `Qwen3-VL-4B-Instruct` (4-bit quantized) through SiMa's `llima` runtime. Results are from this model on this board; other models behave differently.
