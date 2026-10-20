# Final evaluation

The teacher and both students on the frozen 300-document [test set](test-set.md), scored by the same [`metrics.py`](../src/quote_distill/metrics.py) as the pilot. The README's results table comes from here.

## The step and how we know it worked

**Step.** Run the teacher and both students once over the 300 test documents and score them side by side.

**It worked when** every system has an output row for each of the 300 documents (an error is an empty row, scored as wrong), the test set matches its manifest, the hand check covers all 300, and the tables below and in the README were written by `python -m quote_distill.evaluation`, not by hand.

## Before it runs

- **Hand check done.** [`docs/test-set.md`](test-set.md) records all 300 documents as checked, and any corrections have been re-frozen. The command counts the table and refuses below 300.
- **Students trained.** The two notebooks' `tagger-onnx.zip` and `generative-onnx.zip` are unzipped into `demo/public/models/tagger/` and `demo/public/models/generative/`, the files the page serves ([demo.md](demo.md)).
- **Prompt frozen.** The teacher's prompt is the pilot's (`prompt_sha256` `ce5021cd37bf…`). It is not changed after looking at any test result.

## 1. Teacher

The teacher runs in a cloud session, as the pilot did ([teacher-session.md](teacher-session.md)). Read the credit meter, then paste:

```text
Run the Quote Distill teacher evaluation. Follow docs/teacher-session.md exactly; do not change any file under src/ or docs/schema.md.

1. pip install -e ".[dev]" and run: python -m quote_distill.teacher.session prepare --job test-session-haiku-1 --docs data/test/docs.jsonl --evaluation
2. For every file runs/test-session-haiku-1/tasks/<id>.txt, start one Agent subagent with model "haiku" whose prompt is the file's full contents, unchanged. Run them in parallel batches of 5. Do not read data/test labels or give the subagent anything else.
3. Save each subagent's final reply verbatim, with no edits or reformatting, to results/teacher/test-session-haiku-1/outputs/<id>.txt. If a subagent errors, save nothing for that id and say which.
4. Run: python -m quote_distill.teacher.session collect --job test-session-haiku-1. Do not run the score command or look at the scores.
5. Commit results/teacher/test-session-haiku-1/ on a new branch, push, and open a pull request.
```

Read the meter again and log the job in [`spend.md`](spend.md). The teacher's latency isn't measured: subagents run five at a time and the session doesn't time them.

## 2. Students

Both run on CPU through onnxruntime with the same model files the page loads (int8 tagger, 4-bit generative), one document at a time ([`student/evaluate.py`](../src/quote_distill/student/evaluate.py), [student-eval.md](student-eval.md)):

```bash
python -m quote_distill.student.evaluate --docs data/test/docs.jsonl --evaluation --tagger out/tagger-onnx --out results/students/tagger
python -m quote_distill.student.evaluate --docs data/test/docs.jsonl --evaluation --generative out/generative-onnx --out results/students/generative
```

Each writes `predictions-<student>.jsonl` with a `latency_ms` per document, and `summary.json`, which records the model file's SHA-256. The latency is that machine's CPU with model loading excluded. A browser runs the same files in WebAssembly, usually slower, so the number is a floor for the demo, not a measurement of it. Run on dev documents with `--limit 5` first.

## 3. Score

```bash
python -m quote_distill.evaluation \
  --teacher results/teacher/test-session-haiku-1/predictions.jsonl \
  --tagger results/students/tagger/predictions-tagger.jsonl \
  --generative results/students/generative/predictions-generative.jsonl \
  --teacher-cost-usd <the teacher job's credit draw from spend.md>
```

It refuses when the test set differs from its manifest, when the hand check is short of 300, when a file's ids aren't exactly the 300 test ids, or when the teacher job wasn't prepared with `--evaluation`. Then it writes the section below and the README table. `--draft PATH` writes the same report to PATH alone without the hand-check refusal, to check the pipeline; a draft is never quoted as a result.

After this run the test set doesn't change and the scores stand, whatever they are.

## Results

<!-- results:start -->
Not run yet.
<!-- results:end -->
