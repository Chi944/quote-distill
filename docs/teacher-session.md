# Running the teacher in a cloud session

The project's Claude budget is US$100 of Claude Code **cloud session credits**, expiring 5 November 2026 at 15:59 GMT+8. They pay for cloud sessions you start yourself at claude.ai/code. They don't cover API keys, Projects or scheduled tasks. So the teacher runs inside such a session rather than through the Message Batches API. Decided 20 October 2026.

Only the teacher baseline needs Claude: the 20-document pilot, then the 300 frozen test documents. The student trains on generator gold.

## What changes from the API plan

| | Batches API (`teacher/batch.py`) | Cloud session (`teacher/session.py`) |
|---|---|---|
| Prompt | system prompt + `<quotation>` user turn | the same text, joined into one message, because a subagent takes no system prompt |
| Model | `claude-haiku-5-5` at effort low | a Haiku subagent; Claude Code adds its own instructions around it |
| Isolation | one request per document | one fresh subagent per document, with no tools used |
| Parsing and scoring | strict `parse_output`, `quote-distill-score` | identical |
| Cost per document | measured from API usage | not metered per request: you read the credit meter before and after, and the difference is logged with the job |

The results will say the teacher was "Claude Haiku in a Claude Code subagent", not a bare API call.

## Pilot: what to paste into a new cloud session

Start a cloud session at claude.ai/code on the `Chi944/quote-distill` repository. Use the branch `build/teacher-session`, or `main` once it's merged. Read the cloud session credit meter and note it. Then paste:

```text
Run the Quote Distill teacher pilot. Follow docs/teacher-session.md exactly; do not change any file under src/ or docs/schema.md.

1. pip install -e ".[dev]" and run: python -m quote_distill.teacher.session prepare --job pilot-session-haiku-1 --docs data/pilot/pilot-20.jsonl
2. For every file runs/pilot-session-haiku-1/tasks/<id>.txt, start one Agent subagent with model "haiku" whose prompt is the file's full contents, unchanged. Run them in parallel batches of 5. Do not read data/pilot gold labels or give the subagent anything else.
3. Save each subagent's final reply verbatim, with no edits or reformatting, to results/teacher/pilot-session-haiku-1/outputs/<id>.txt. If a subagent errors, save nothing for that id and say which.
4. Run: python -m quote_distill.teacher.session collect --job pilot-session-haiku-1, then the score command it prints, and save that report to results/teacher/pilot-session-haiku-1/report.md.
5. Commit results/teacher/pilot-session-haiku-1/ on a new branch, push, open a pull request, and tell me the five pilot gate results.
```

When it finishes, read the meter again and post both readings in the project thread. They go into `docs/spend.md` with the job.

## After the pilot

The gates in [`pilot-plan.md`](pilot-plan.md) decide what happens next, as before. If Haiku fails, the same steps run again with `--model sonnet` as a new job. The test-set run uses `--evaluation` and `data/test/docs.jsonl`. It happens once, after the hand check, and the prompt never changes after looking at its results.

## Expected credit use

The subagents read about 82,000 tokens and write about 48,000 for the pilot. At Haiku's standard API price, that would be about US$0.03. Claude Code adds its own instructions to each subagent, and the session's main model spends tokens coordinating them, so the real draw will be larger. I expect a few dollars at most for the pilot. That is an estimate: the meter readings are the measurement.
