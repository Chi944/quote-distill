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
| Teacher: Claude Haiku in a Claude Code subagent | 11172/11208 (99.7%) | 0.997 | 299/300 (99.7%) | 260/300 (86.7%) | not measured | ~$0.0008 (estimate at Haiku batch API prices, 2026-10-18) |
| Student: encoder tagger (in browser) | 11208/11208 (100.0%) | 1.000 | 300/300 (100.0%) | 299/300 (99.7%) | 30 ms median | $0 (runs in the browser) |
| Student: generative (in browser) | 11066/11208 (98.7%) | 0.989 | 293/300 (97.7%) | 278/300 (92.7%) | 12.5 s median | $0 (runs in the browser) |
<!-- results:end -->

Every result is reported against the frozen 300-document test set, with its denominator, in [docs/evaluation.md](docs/evaluation.md). That set comes from the same generator the students trained on, so it favours them; see [Reading the results](docs/evaluation.md#reading-the-results).

## Run locally

```bash
pip install -e ".[dev]"
pytest -q
quote-distill-generate --n 500 --seed 1 --split dev --out data/generated/dev
```

## Off the generator's distribution

The test set above comes from the generator the students trained on. These are 30 quotations written by hand in layouts the generator never produces, plus the 5 hand-written seeds ([docs/ood.md](docs/ood.md)):

<!-- ood:start -->
**Hand-written, out-of-distribution (30 documents)**

| Model | Per-field exact match | Line-item F1 | Arithmetic agrees with gold | Whole document exact | Latency per doc (CPU) |
|---|---|---|---|---|---|
| Student: encoder tagger | 565/888 (63.6%) | 0.452 | 22/30 (73.3%) | 0/30 (0.0%) | 50 ms median |
| Student: generative | 450/780 (57.7%) | 0.524 | 10/30 (33.3%) | 0/30 (0.0%) | 10.7 s median |

**Hand-written seeds (5 documents)**

| Model | Per-field exact match | Line-item F1 | Arithmetic agrees with gold | Whole document exact | Latency per doc (CPU) |
|---|---|---|---|---|---|
| Teacher: Claude Haiku (pilot run) | 156/157 (99.4%) | 1.000 | 5/5 (100.0%) | 3/5 (60.0%) | not measured |
| Student: encoder tagger | 108/193 (56.0%) | 0.800 | 4/5 (80.0%) | 1/5 (20.0%) | 58 ms median |
| Student: generative | 80/157 (51.0%) | 0.615 | 2/5 (40.0%) | 1/5 (20.0%) | 14.9 s median |
<!-- ood:end -->

## Docs

| Topic | Read |
|---|---|
| Final evaluation, results by hard case, and failure gallery | [docs/evaluation.md](docs/evaluation.md) |
| Output schema and its rules | [docs/schema.md](docs/schema.md), [JSON Schema](schema/quotation.schema.json) |
| Synthetic quotation generator | [docs/generator.md](docs/generator.md) |
| Frozen test set and hand check | [docs/test-set.md](docs/test-set.md) |
| Out-of-distribution check | [docs/ood.md](docs/ood.md) |
| Training data, the two students and how they are scored | [docs/student-data.md](docs/student-data.md), [docs/tagger.md](docs/tagger.md), [docs/generative.md](docs/generative.md), [docs/student-eval.md](docs/student-eval.md) |
| Teacher runs and API spend | [docs/pilot-plan.md](docs/pilot-plan.md), [docs/teacher-session.md](docs/teacher-session.md), [docs/spend.md](docs/spend.md) |
| Browser demo and publishing | [docs/demo.md](docs/demo.md) |
| Model card for the Hugging Face repo | [hf/README.md](hf/README.md) |
| Repository layout | [docs/repo-layout.md](docs/repo-layout.md) |

## About

Quote Distill extends [FieldOps](https://github.com/Chi944/fieldops), which compares supplier quotations with the source document beside every value. All data is synthetic: no real suppliers, prices or documents. Released under the [MIT licence](LICENSE).
