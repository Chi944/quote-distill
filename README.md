# Quote Distill

A supplier-quotation extractor distilled from Claude into a small open model that runs entirely in your browser, with an honest teacher-versus-student evaluation.

**Demo:** [chi944.github.io/quote-distill](https://chi944.github.io/quote-distill/). It's a static page with no API key, no server and no paid service. The models download once (the tagger is 128 MB, the generative model 387 MB) and then run on your device.

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

- [Schema rules](docs/schema.md) and [JSON Schema](schema/quotation.schema.json)
- [Synthetic generator](docs/generator.md)
- [Teacher pilot plan](docs/pilot-plan.md) and [API spend log](docs/spend.md)
- [Final evaluation](docs/evaluation.md)
- [Repository layout](docs/repo-layout.md)

Extends [FieldOps](https://github.com/Chi944/fieldops), which compares supplier quotations with the source document beside every value. All data here is synthetic: no real suppliers, prices or documents.
