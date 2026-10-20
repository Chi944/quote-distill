# Repository layout for Chi944/quote-distill

Built so far: schema, seeds, checks, generator, scoring metrics, teacher pilot tooling (not yet run), the 20 pilot documents, the frozen 300-document test set (hand check pending), student training data with compact generative targets and tagger spans ([student-data.md](student-data.md)), the tagger's labels, training and export code and notebook ([tagger.md](tagger.md)), the same for the generative student ([generative.md](generative.md)), the demo's TypeScript post-processing, model runners and page ([demo.md](demo.md)), student scoring ([student-eval.md](student-eval.md)), tests and CI. Everything else below is planned.

Python owns data, teacher jobs, training and metrics; TypeScript owns the static demo. The demo folder builds to plain static files and never needs a key or server.

```text
quote-distill/
├── README.md                    # one sentence, demo link, results table, run locally in 3 commands
├── LICENSE
├── .env.example                 # ANTHROPIC_API_KEY= (placeholder only)
├── .gitignore                   # .env, data/generated/, runs/, models/, demo/dist/, demo/public/models/
├── pyproject.toml               # package quote_distill; dev extras: pytest, ruff, jsonschema
├── schema/
│   └── quotation.schema.json    # the single source of truth (v1.0.0)
├── src/quote_distill/
│   ├── schema.py                # load and validate against the JSON Schema
│   ├── money.py                 # Decimal parsing, half-up rounding; no floats anywhere
│   ├── normalise.py             # unit, currency and date tables shared by generator and checks
│   ├── checks.py                # provenance, normalisation and arithmetic checks
│   ├── generator/
│   │   ├── vocab.py             # fictional suppliers, items, units, typo tables
│   │   ├── sample.py            # draw values and their printed forms; build the gold label
│   │   ├── layouts.py           # five renderers: fixed table, pipe table, item blocks, email list, prose
│   │   └── build.py             # CLI; keeps only labels that pass checks.py
│   ├── splits.py                # dev / train / test assignment by hash; test is frozen
│   ├── teacher/
│   │   ├── pilot.py             # picks the 20 pilot documents (5 seeds + 3 per hard-case family, dev only)
│   │   ├── prompt.py            # system prompt built from docs/schema.md + schema; strict JSON parsing
│   │   ├── batch.py             # plan, log, count, submit, collect Message Batches; custom_id = doc id
│   │   └── spend.py             # pricing table; estimate and actual rows in docs/spend.md
│   ├── student/
│   │   ├── data.py              # train/dev sets without test or pilot texts; compact targets and expand()
│   │   ├── spans.py             # where each gold value is printed, for the encoder tagger
│   │   ├── decode.py            # tagged spans + two document classes back to a schema label
│   │   ├── tokens.py            # spans to per-token labels and back (no tokenizer needed)
│   │   ├── tagger.py            # train, predict, score and export the tagger (needs the train extra)
│   │   ├── generative.py        # prompt, train, generate, score and export the generative student
│   │   ├── fixtures.py          # Python results the demo's TypeScript port must match
│   │   └── evaluate.py          # scores the exported students like the teacher (docs/student-eval.md)
│   ├── metrics.py               # per-field exact match, line-item F1, arithmetic, whole-doc match, pilot gates
│   └── report.py                # results tables and failure gallery (metrics.py prints a first version)
├── students/
│   ├── encoder/                 # token tagger: BIO labels from `raw` spans + deterministic assembly
│   └── generative/              # small seq2seq / decoder (< ~500M) emitting compact JSON that student/data.py expands to the schema
│       └── (each has train.py, export_onnx.py, and a Colab/Kaggle notebook)
├── notebooks/
│   ├── train_tagger.ipynb       # Colab/Kaggle: train, score on dev, export ONNX (docs/tagger.md)
│   └── train_generative.ipynb   # Colab/Kaggle: same for the generative student (docs/generative.md)
├── data/
│   ├── seeds/                   # the five hand-authored hard cases (committed)
│   ├── samples/                 # small committed generator sample for review
│   ├── pilot/                   # the 20 frozen pilot documents with gold, and their manifest
│   ├── test/                    # 300 hand-checked, frozen: docs, labels, MANIFEST.sha256
│   └── generated/               # dev and train output (git-ignored, reproducible from a seed)
├── demo/                        # TypeScript + Vite static site
│   ├── src/core/                # TypeScript port of decode, expand, token reading, arithmetic, offsets (docs/demo.md)
│   ├── src/models/              # tagger and generative runners on transformers.js
│   ├── src/page/                # the page: samples, rendering, wiring
│   ├── test/                    # vitest: parity with Python on every dev and pilot document
│   ├── src/                     # transformers.js inference, schema validation, arithmetic badges
│   ├── public/models/           # quantised ONNX weights (git-ignored; fetched from Hugging Face Hub)
│   └── package.json
├── tests/                       # pytest: money, checks, metrics, generator invariants, test-set hashes
├── docs/
│   ├── schema.md                # normalisation and arithmetic rules
│   ├── pilot-plan.md
│   ├── spend.md                 # every API job: estimate, actual tokens, cost, running total
│   ├── test-set.md              # how the 300 were hand-checked; freeze date and hashes
│   ├── evaluation.md            # full results, per field, with denominators and failures
│   └── decisions.md             # choices made, options rejected, and why
└── .github/workflows/
    └── ci.yml                   # on every push: ruff, pytest, schema check on seeds and test set,
                                 # test-set hash check, demo typecheck and build
```

## Rules the layout enforces

- **Test set is frozen.** `data/test/MANIFEST.sha256` is checked in CI; any change to a test document or label fails the build. Training and prompt code never import from `data/test/`; a test checks that.
- **One schema.** Python validates with `schema/quotation.schema.json`; the demo imports the same file at build time.
- **No key in the demo.** The demo build has no environment variables. Model weights are served as static files (or from the Hub), so it runs on GitHub Pages.
- **Spend is logged by code.** `teacher/batch.py` refuses to submit without an estimate row in `docs/spend.md`, without `--yes`, if the prompt changed since the estimate, or if the job was already submitted. `collect` writes the actual usage and cost back to the same row.
