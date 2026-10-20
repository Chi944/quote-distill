# Browser demo

The demo is a static TypeScript page. It runs both students in the browser with transformers.js and needs no key, server or paid service. This page records how it's built. It's being built in parts.

## Part 1: building answers in TypeScript

**Step.** Port everything that turns a model's raw output into a schema label to TypeScript. That covers the tagger's decoder, the generative student's `expand`, the token-label reader and the arithmetic check behind the badges.

**It worked when** the TypeScript gives exactly the Python result on every validation and pilot document. **Result: 1,020/1,020 on all five checks** (1,000 dev and 20 pilot documents):

| Check | Python source | Same result |
|---|---|---|
| Compact target to label | `student/data.py` `expand` | 1,020/1,020 |
| Gold spans to label, with the date-order class | `student/decode.py` `decode` | 1,020/1,020 |
| Gold spans to label, date order guessed from currency | `decode(..., None)` | 1,020/1,020 |
| Arithmetic failures of the gold label (62 documents have intended failures) | `checks.check_arithmetic` | 1,020/1,020 |
| Token labels back to spans | `student/tokens.py` `spans_of` | 1,020/1,020 |

Money uses an exact BigInt decimal ([`demo/src/core/decimal.ts`](../demo/src/core/decimal.ts)) with Python's rounding rules. That means half-up for amounts, and half-even only where Python's string formatting applies it. Dates use a port of CPython's `strptime` patterns for the formats in `normalise.py`.

The fixtures are generated, not committed. CI rebuilds them from the Python code on every push and runs the TypeScript tests against them:

```bash
python -m quote_distill.student.data --out data/generated/student
python -m quote_distill.student.fixtures --data data/generated/student/dev.jsonl --out demo/fixtures/dev.jsonl
cd demo && npm ci && npm test
```

## Next parts

- **Running the models:** load the exported ONNX models with transformers.js, compute token offsets for the tagger, and generate with the fixed prompt for the generative student.
- **The page:** paste or pick a synthetic quotation, run both students, and show the fields, the arithmetic badges, latency, and a link to the results.
