# API spend log

Budget: US$100 of Claude Code cloud session credits, building only, expiring 5 November 2026 at 15:59 GMT+8. The finished demo uses none. Jobs run in a cloud session ([teacher-session.md](teacher-session.md)); there the actual cost is the credit meter read before and after the job, because the session isn't metered per request. API batch jobs, if any, take their actual cost from the API's usage.

Every job gets a row before submission (estimate) and is completed after (actual usage from the API response). Costs use the pricing page rates on the date shown.

| Date | Job | Model | Mode | Requests | Input tokens | Output tokens | Est. cost | Actual cost | Running total | Pricing checked |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-20 | pilot-session-haiku-1 | Haiku subagents (Claude Code) | cloud session | 20 | ~1.8M incl. Claude Code overhead (session report) | n/a | a few dollars (estimate) | not isolated: meter fell $100 → $86 while 2 other cloud sessions also ran, so at most $14.00 | ≤ $14.00 | 2026-10-18 |

Running total: **at most $14.00** of US$100 (meter at $86 on 20 October 2026, shared with other sessions). To measure a job alone, read the meter right before and after with no other cloud session running.
