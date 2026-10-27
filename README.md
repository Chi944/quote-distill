# Quote Distill

[![CI](https://github.com/Chi944/quote-distill/actions/workflows/ci.yml/badge.svg)](https://github.com/Chi944/quote-distill/actions/workflows/ci.yml)
[![Demo](https://github.com/Chi944/quote-distill/actions/workflows/pages.yml/badge.svg)](https://chi944.github.io/quote-distill/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A supplier-quotation extractor distilled from Claude into small open models that run entirely in your browser, with an honest teacher-versus-student evaluation.

**Live demo:** [chi944.github.io/quote-distill](https://chi944.github.io/quote-distill/). It's a static page with no API key, no server and no paid service. The models download once from [Hugging Face](https://huggingface.co/werty3684/quote-distill-students) (the tagger is 128 MB, the generative model 387 MB) and then run on your device.

## Results

<!-- results:start -->
| Model | Per-field exact match | Line-item F1 | Arithmetic agrees with gold | Whole document exact | Latency per doc (CPU) | Cost per doc |
|---|---|---|---|---|---|---|
| Teacher: Claude Haiku in a Claude Code subagent | 11172/11208 (99.7%) | 0.997 | 299/300 (99.7%) | 260/300 (86.7%) | not measured | not measured |
| Student: encoder tagger (in browser) | 11208/11208 (100.0%) | 1.000 | 300/300 (100.0%) | 299/300 (99.7%) | 30 ms median | $0 (runs in the browser) |
| Student: generative (in browser) | 11066/11208 (98.7%) | 0.989 | 293/300 (97.7%) | 278/300 (92.7%) | 12.5 s median | $0 (runs in the browser) |
<!-- results:end -->

Every result is reported against the frozen 300-document test set, with its denominator, in [docs/evaluation.md](docs/evaluation.md).

## Run locally

```bash
pip install -e ".[dev]"
pytest -q
quote-distill-generate --n 500 --seed 1 --split dev --out data/generated/dev
```

## Docs

| Topic | Read |
|---|---|
| Final evaluation, results by hard case, and failure gallery | [docs/evaluation.md](docs/evaluation.md) |
| Output schema and its rules | [docs/schema.md](docs/schema.md), [JSON Schema](schema/quotation.schema.json) |
| Synthetic quotation generator | [docs/generator.md](docs/generator.md) |
| Frozen test set and hand check | [docs/test-set.md](docs/test-set.md) |
| Students: training data, tagger, generative model, scoring | [docs/student-data.md](docs/student-data.md), [docs/tagger.md](docs/tagger.md), [docs/generative.md](docs/generative.md), [docs/student-eval.md](docs/student-eval.md) |
| Teacher runs and API spend | [docs/pilot-plan.md](docs/pilot-plan.md), [docs/teacher-session.md](docs/teacher-session.md), [docs/spend.md](docs/spend.md) |
| Browser demo and publishing | [docs/demo.md](docs/demo.md) |
| Repository layout | [docs/repo-layout.md](docs/repo-layout.md) |

## About

Quote Distill extends [FieldOps](https://github.com/Chi944/fieldops), which compares supplier quotations with the source document beside every value. All data is synthetic: no real suppliers, prices or documents. Released under the [MIT licence](LICENSE).
