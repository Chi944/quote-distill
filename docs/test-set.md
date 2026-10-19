# Frozen test set

300 synthetic quotations in [`data/test/docs.jsonl`](../data/test/docs.jsonl), frozen by [`data/test/MANIFEST.sha256`](../data/test/MANIFEST.sha256). Every number in the final evaluation is reported against these 300 documents.

## The step and how we know it worked

**Step.** Draw 300 documents that cover every hard case, freeze them, and make it impossible for training or prompt work to touch them.

**It worked when** CI fails on any edit to a test document, no training or prompt code can read the folder, no test text appears in the dev, train or pilot data, and the hand check is recorded.

## How they were chosen

- Their own split (`test-candidates`, pool seed 1, 3,000 documents), so their random streams never overlap dev or train. A check against 10,000 train, 2,500 dev and the 20 pilot documents found 0 shared texts.
- A greedy, deterministic pick ([`splits.py`](../src/quote_distill/splits.py)) that keeps every locale and layout at exactly 60 and brings every hard-case feature to at least 15 documents. The rarest are: every row a lump sum (15), document discount with no printed amount (15), GST rate not printed (18), half-cent rounding tie (21), "plus GST" with no amount (22), supplier arithmetic error (26). The full counts are in [`coverage.json`](../data/test/coverage.json).
- 1,318 line items in total; 26 documents keep a supplier's arithmetic mistake in the label.
- Every label passes the deterministic checks (schema, provenance, normalisation, arithmetic), which a test re-runs.

## Rules

- `python -m quote_distill.splits verify` runs in CI. Any change to a document, a label, or the set of ids fails the build.
- Only `splits.py` may read `data/test`; a test scans the source tree for anything else that does.
- Training data passes through `splits.exclude_test`, which drops any record whose text is a test document.
- The teacher sees test documents only through `batch.py plan --evaluation`, which also refuses a job that mixes test and non-test documents. The prompt is never changed after looking at test results.
- A correction found in the hand check is made in `docs.jsonl`, logged below with its reason, and re-frozen with `python -m quote_distill.splits freeze` **before** any model is evaluated. After the first evaluation run the set does not change.

## Hand check

Status: **not started.** The generator's labels are machine-checked; the hand check is the independent evidence that the generator, the checker and the shared rounding helper are not wrong together.

The check is done on a private review page that shows each document beside its gold label (hovering a value highlights the text it came from) and records a verdict and note per document. Verdicts are read back from that page into the table below; the page itself holds no data the repository does not.

| Date | Documents checked | Problems found | Corrections (id: field, reason) |
|---|---|---|---|
