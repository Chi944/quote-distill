# API spend log

Budget: US$100 of Claude Code cloud session credits, building only, expiring 5 November 2026 at 15:59 GMT+8. The finished demo uses none. Jobs run in a cloud session ([teacher-session.md](teacher-session.md)); there the actual cost is the credit meter read before and after the job, because the session isn't metered per request. API batch jobs, if any, take their actual cost from the API's usage.

Every job gets a row before submission (estimate) and is completed after (actual usage from the API response). Costs use the pricing page rates on the date shown.

| Date | Job | Model | Mode | Requests | Input tokens | Output tokens | Est. cost | Actual cost | Running total | Pricing checked |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-20 | pilot-session-haiku-1 | Haiku subagents (Claude Code) | cloud session | 20 | ~1.8M incl. Claude Code overhead (session report) | n/a | a few dollars (estimate) | not isolated: meter fell $100 → $86 while 2 other cloud sessions also ran, so at most $14.00 | ≤ $14.00 | 2026-10-18 |
| 2026-10-23 to 2026-10-27 | test-session-haiku-1 (300 test docs, plus 19 rate-limited retries and 1 re-run of 000817) | Haiku subagents (Claude Code) | cloud session | 320 | ~85k per subagent incl. Claude Code overhead (session report) | n/a | not estimated per request | not isolated: other cloud sessions ran at the same time, and d reported the credits used up on 27 October 2026 | ≤ $100.00 (whole budget) | 2026-10-18 |

Running total: **the whole US$100 budget**. On 27 October 2026 d reported no cloud credits left. Those credits paid for both teacher runs and the cloud build sessions, which ran side by side, so the teacher's own share can't be separated from the meter. The pilot cost at most $14.00. No further paid jobs will run: the demo, the students and their scoring are free (training ran on d's own GPU, inference runs in the browser).
