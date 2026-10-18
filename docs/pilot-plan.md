# Teacher pilot plan (20 samples)

Status: **planned, not run.** No API call has been made. Prices were read from the [pricing page](https://platform.claude.com/docs/en/about-claude/pricing) on 18 October 2026.

## The step and how we will know it worked

**Step.** Run the teacher (claude-haiku-5-5) once over 20 development quotations through the Message Batches API and score its output against our gold labels.

**It worked when** all five gates below pass on the 20 documents. If they pass, Haiku becomes the teacher for bulk labelling and for the teacher column of the final evaluation. If any gate fails, the same 20 run on claude-sonnet-5-5, scored against the same gates.

## What the teacher is for

The generator already produces gold labels, so the teacher is not needed to create ground truth. It has two jobs:

1. **Baseline.** Its scores on the frozen 300-document test set are the "teacher" column we compare the student against.
2. **Distillation targets (optional).** Its outputs on training documents can be extra or alternative training targets.

| Option | Trade-off |
|---|---|
| A. Train the student on generator gold; the teacher is only the baseline | Cheapest and cleanest labels; "distillation" then means matching the teacher's task, not its outputs |
| B. Train on teacher outputs, filtered by the same checks as gold | A true distillation story and a learned teacher-style output; costs a bulk job and inherits teacher errors that pass the checks |

**Recommendation: A first, B as an ablation if budget allows.** The pilot is the same under both.

## Sample

- 20 documents from the **dev** split: the 5 seeds in `data/seeds/` plus 15 generator documents, 3 from each hard-case family (inclusive GST and rounding, line and lump-sum discounts, sparse or missing fields, supplier arithmetic errors and credits, prose layouts with bare `$` and conditional discounts).
- Generator seed and document hashes recorded before the run. **No test-set document is used**, because the pilot is prompt tuning.

## Request

- System prompt: `docs/schema.md` rules plus the minified JSON Schema, identical for all 20 requests. User turn: the document text only.
- `model: claude-haiku-5-5`, `output_config.effort: "low"` (adaptive thinking stays on, which is the model's default), `max_tokens: 8000`, no sampling parameters (Haiku 5.5 rejects non-default values).
- JSON output via `output_config.format` if the schema fits the structured-outputs subset (we check this locally first; `oneOf` may need to become `anyOf`). Otherwise a plain JSON instruction. Either way every output is validated locally with `jsonschema`.
- `custom_id` = document id. Results are keyed by `custom_id`, never by order.

## Token and cost estimate

Sizes are measured from the files in this folder; tokens use a conservative 3 characters per token because exact counts need the token-counting endpoint, which is an API call. Generated pilot documents are assumed larger than the seeds (about 6 lines each).

| Per request | Measured basis | Estimate |
|---|---|---|
| System prompt | schema 6,720 chars + rules 3,907 chars + about 1,000 chars of instructions | ~3,900 tokens |
| Document | seeds average 855 chars; generated docs up to ~2,500 | ~600 tokens |
| Output JSON with `raw` | seeds average 2,060 chars for 3.4 lines | ~1,200 tokens |
| Thinking at effort low | allowance, billed as output | ~1,500 tokens |
| **Input / output** | | **~4,500 / ~2,700** |

Batch prices (50% of standard): Haiku 5.5 $0.05 input and $0.25 output per million tokens (prompts up to 100K tokens); Sonnet 5.5 $1 and $5.

| Job (20 requests) | Input tokens | Output tokens | Expected cost | Worst case (every reply hits 8,000 tokens) |
|---|---|---|---|---|
| Haiku 5.5 pilot | 90,000 | 54,000 | **$0.018** | $0.045 |
| Sonnet 5.5 pilot (only if Haiku fails) | 90,000 | 54,000 | **$0.36** | $0.89 |

For later planning, the same per-document figures give about $0.0009 per document on Haiku and $0.018 on Sonnet in batch, so 300 test documents cost about $0.27 or $5.40. Caching the shared system prompt would cut input cost further, but output dominates.

## Quality gates (fixed before the run)

Scored per document against gold, with denominators reported.

| Gate | Threshold | Denominator |
|---|---|---|
| 1. Schema-valid JSON, no repair | 20/20 | 20 documents |
| 2. Critical fields exact (state and value): supplier, quote_number, date, currency, subtotal, gst.treatment, gst.rate, gst.amount, total | ≥ 95% | 180 fields |
| 3. Line-item F1, a line counting only when all six fields match exactly | ≥ 0.90 | gold and predicted lines |
| 4. Invented values: gold not_stated but teacher stated | ≤ 1 | all not_stated gold fields |
| 5. Arithmetic: teacher's failed checks equal gold's intended failures (it must not "fix" a supplier's mistake) | ≥ 19/20 | 20 documents |

Whole-document exact match and per-field exact match for every field are reported, not gated. Every failing document goes into the failure gallery.

## Sequence

1. Freeze the prompt, gold, sample list and gates in a commit.
2. Count tokens for the 20 requests with the token-counting endpoint and update the estimate above (needs your go-ahead, as it is an API call, though it is not billed).
3. Submit the Haiku batch; log it in `docs/spend.md` before and after (estimate, then actual usage and cost).
4. Score locally. Pass: stop here and report. Fail: report the failing gates first, then run Sonnet on the same 20 and log it.
5. If a failure is clearly a rule our prompt never stated (for example a normalisation rule), I will say so and propose one Haiku rerun with the fixed prompt as a new logged job before escalating. You decide.

The pilot can only run once the generator (plan step 2) exists, because it needs 15 generated documents. Until then the 5 seeds let us dry-run the scoring code with no API call.
