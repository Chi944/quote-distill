# Quote Distill

A supplier-quotation extractor distilled from Claude into a small open model that runs entirely in your browser, with an honest teacher-versus-student evaluation.

**Demo:** not built yet. It will be a static page with no API key, no server and no paid service.

<!-- results:start -->
| Model | Per-field exact match | Line-item F1 | Arithmetic agrees with gold | Whole document exact | Latency per doc | Cost per doc |
|---|---|---|---|---|---|---|
| Teacher (Claude) | not run yet | | | | | |
| Student: encoder tagger (in browser) | not trained yet | | | | | |
| Student: generative (in browser) | not trained yet | | | | | |
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
