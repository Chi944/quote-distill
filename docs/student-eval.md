# Scoring the students

**Step.** Score both exported students exactly as the teacher is scored. The scoring runs the same ONNX files the demo page loads (the tagger's int8 `model_quantized.onnx` and the generative student's 4-bit `model_q4.onnx`) through `metrics.py`, and prints the README row.

**It worked when** a run gives a report, predictions and a README row with every number over its denominator, and the frozen test set can only be scored as the final evaluation. **Result:** done and tested on dev documents with the tiny test models. The real scores wait for the trained exports.

```bash
# Quick check on dev documents (either student alone works; they need different extras)
pip install -e ".[train]"
python -m quote_distill.student.evaluate --docs data/generated/dev/docs.jsonl --limit 100 \
    --tagger out/tagger-onnx --out runs/students-dev
pip install -e ".[generative]"
python -m quote_distill.student.evaluate --docs data/generated/dev/docs.jsonl --limit 100 \
    --generative out/generative-onnx --out runs/students-dev-gen
```

Each run writes `report-<student>.md` (the same tables as the teacher's report, failing documents listed), `predictions-<student>.jsonl` (readable by `quote-distill-score --pred`) and `summary.json` with the README row.

## The final evaluation

The test set follows the same rules as for the teacher ([test-set.md](test-set.md)):

- A run is either all frozen test documents with `--evaluation` or none. A test document without the flag, a mixed file, or `--limit` with the flag is refused.
- The hand check and any corrections come first, then the evaluation. Nothing about the students changes after looking at their test scores.

The order once the exports are attached:

1. Check the real tokenizers in the browser: `python -m quote_distill.student.fixtures ... --tokenizer <unpacked export>`, then `npm test` in `demo/`. Ids and offsets must match Python on all 1,020 dev and pilot documents, as they do for the stand-in.
2. Score on dev, to compare with the notebooks' own dev numbers.
3. Record the hand check, then score the 300 test documents with `--evaluation` and put the rows in the README.

## Latency

The latency here is wall time per document on the scoring machine's CPU through onnxruntime, one document at a time, with model loading excluded. It is reported as median and 90th percentile, and the README row says it is CPU onnxruntime. The browser is a different runtime on a different machine; the demo page shows its own time for each run.
