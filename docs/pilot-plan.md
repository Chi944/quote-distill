# Teacher pilot plan (20 samples)

Status: **ready to run, not run.** Documents, prompt, scoring and spend guard are built and tested. No API call has been made. Prices were read from the [pricing page](https://platform.claude.com/docs/en/about-claude/pricing) on 18 October 2026.

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

Frozen in [`data/pilot/`](../data/pilot) (`manifest.json` lists ids, families and text hashes; a test regenerates them and checks the hashes).

- The 5 seeds in `data/seeds/`.
- 15 generator documents from a **dev** pool (seed 7, 2,000 documents), 3 per hard-case family, picked by [`teacher/pilot.py`](../src/quote_distill/teacher/pilot.py): the documents with the most hard features of that family, spread across locales and layouts.

| Family | Must have | Documents |
|---|---|---|
| Inclusive GST and rounding | `gst:inclusive` | 3 (AU, SG, SG) |
| Line and lump-sum discounts | a lump-sum row | 3 (US, AU, MY) |
| Sparse or missing fields | no subtotal and no quote number | 3 (AU, MY, NZ) |
| Supplier errors and credits | a supplier arithmetic error kept as printed | 3 (AU, NZ, US) |
| Prose, bare `$` and conditional discounts | prose email with a bare `$` | 3 (US, US, AU) |

**No test-set document is used**, because the pilot is prompt tuning; `batch.py plan` refuses any document from a test split.

## Request

- System prompt: `docs/schema.md` rules plus the minified JSON Schema, identical for all 20 requests. User turn: the document text only.
- `model: claude-haiku-5-5`, `output_config.effort: "low"` (adaptive thinking stays on, which is the model's default), `max_tokens: 8000`, no sampling parameters (Haiku 5.5 rejects non-default values).
- Plain JSON instruction, no structured outputs. Whether our schema fits the structured-outputs subset can only be confirmed by an API call, and gate 1 measures exactly what we need to know: whether the teacher returns valid JSON unaided. Parsing is strict (a code fence counts as a failure) and every output is validated locally with `jsonschema`. If gate 1 is the only failure, structured outputs is the first fix to try.
- `custom_id` = document id. Results are keyed by `custom_id`, never by order.

## Token and cost estimate

Measured from the actual 20 requests by `python -m quote_distill.teacher.batch plan` (no network call), at a conservative 3 characters per token. The `count` command replaces the input figure with exact counts from the token-counting endpoint, which is free but is an API call.

| Per request (average of 20) | Measured basis | Estimate |
|---|---|---|
| System prompt | 11,472 characters (instructions, schema rules, minified JSON Schema) | ~3,800 tokens |
| Document | 762 characters on average, longest 1,374 | ~260 tokens |
| Output JSON with `raw` | gold labels average 2,455 characters | ~900 tokens |
| Thinking at effort low | allowance, billed as output | ~1,500 tokens |
| **Input / output** | | **~4,100 / ~2,400** |

Batch prices (50% of standard), checked 18 October 2026: Haiku 5.5 $0.05 input and $0.25 output per million tokens (prompts up to 100K tokens); Sonnet 5.5 $1 and $5.

| Job (20 requests) | Input tokens | Output tokens | Expected cost | Worst case (every reply hits 8,000 tokens) |
|---|---|---|---|---|
| Haiku 5.5 pilot | ~81,900 | ~48,000 | **$0.016** | $0.044 |
| Sonnet 5.5 pilot (only if Haiku fails) | ~81,900 | ~48,000 | **$0.32** | $0.88 |

For later planning that is about $0.0008 per document on Haiku and $0.016 on Sonnet in batch, so 300 test documents cost about $0.24 or $4.80. Prices are re-checked on the pricing page before every job.

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

The gates are coded in [`metrics.py`](../src/quote_distill/metrics.py) (`PILOT_GATES`) and tested, so they cannot drift after the results are in. Line-item F1 counts a line only when all six fields match and ignores order; per-field line accuracy is also reported by position.

## Sequence

1. Freeze the prompt, gold, sample list and gates in a commit. **Done.**
2. Count tokens for the 20 requests with the token-counting endpoint and update the estimate above (needs your go-ahead, as it is an API call, though it is not billed).
3. Submit the Haiku batch; log it in `docs/spend.md` before and after (estimate, then actual usage and cost).
4. Score locally. Pass: stop here and report. Fail: report the failing gates first, then run Sonnet on the same 20 and log it.
5. If a failure is clearly a rule our prompt never stated (for example a normalisation rule), I will say so and propose one Haiku rerun with the fixed prompt as a new logged job before escalating. You decide.

## Commands

```bash
python -m quote_distill.teacher.batch plan    --job pilot-haiku-1 --docs data/pilot/pilot-20.jsonl --model claude-haiku-5-5
python -m quote_distill.teacher.batch log     --job pilot-haiku-1          # estimate row in docs/spend.md
python -m quote_distill.teacher.batch count   --job pilot-haiku-1 --yes    # API call, free
python -m quote_distill.teacher.batch submit  --job pilot-haiku-1 --yes    # API call, billed
python -m quote_distill.teacher.batch collect --job pilot-haiku-1          # actual cost into docs/spend.md
quote-distill-score --gold data/pilot/pilot-20.jsonl --pred runs/pilot-haiku-1/predictions.jsonl --gates
```

`submit` refuses without `--yes`, without the estimate row, if the prompt changed since `plan`, or if the job was already submitted. The key is read from the git-ignored `.env`.
