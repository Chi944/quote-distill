# Out-of-distribution check

The [frozen test set](test-set.md) comes from the same generator as the students' training data. It has its own random streams and shares no texts with training, but the templates, wording and kinds of goods are the same. That favours the students. This check scores them on quotations the generator didn't write.

## The step and how we know it worked

**Step.** Write 30 quotations by hand in layouts and wording the generator never produces, label them, have d hand-check them, freeze them, and score both students on them, with the 5 hand-written seeds alongside.

**It worked when** every label passes the deterministic checks (`python -m quote_distill.checks data/ood`, run in CI), the hand check is recorded below and the set is frozen (`python -m quote_distill.ood verify`, run in CI once frozen), and the tables below were written by `python -m quote_distill.ood report` from predictions made by the same ONNX files the demo loads.

## The documents

[`data/ood/`](../data/ood/) holds 30 quotations, 6 per locale, written in [`data/ood/author.py`](../data/ood/author.py). The script holds each document's text and its label as the printed raw strings; it derives each value by the [schema's rules](schema.md), and the checker confirms that every raw is in the text and every total adds up. What's new compared with the generator:

- **Layouts:** a chat message, emails with prices inside sentences, key: value blocks, semicolon-separated rows, a summary box printed above the items, a receipt, a boxed table with a SKU column, a cart, a contractor's bid, bilingual Malay and English headings, rows with no column headers, and columns in a new order.
- **Wording:** "Estimate", "Proposal", "Bid", "Price confirmation" and "Sebut harga" instead of "Quotation", and "Grand total", "Nett total", "To pay" and "Base bid" for the totals.
- **Goods and services:** AV rental, printing, catering, IT services, plants, lab equipment, marquee hire, solar, roofing, software seats and more, from suppliers outside the generator's name lists.

The schema and its rules are unchanged, so there are no new kinds of fields. Two known limits are left for later: Malaysia's SST and US sales tax aren't modelled (the schema's tax field is GST), so the Malaysian and US documents here either don't mention tax or say it isn't charged; and units outside the schema's vocabulary (such as "pax" or "unit") are avoided.

The 5 hand-written seeds in [`data/seeds/`](../data/seeds/) are scored too. They are the only other documents the generator didn't write, and the teacher's pilot already answered them, so they are the one place all three models can be compared off-distribution.

## Hand check

| Date | Documents checked | Problems found | Corrections |
|---|---|---|---|

## Running it

The students run in GitHub Actions ([`.github/workflows/ood.yml`](../.github/workflows/ood.yml), started by hand): it downloads the published models from Hugging Face, runs [`student/evaluate.py`](../src/quote_distill/student/evaluate.py) on both sets on the runner's CPU, and pushes the predictions to a `results/ood-<run>` branch for a pull request. Then:

```bash
python -m quote_distill.ood report --results results/ood
```

It refuses unless `data/ood` matches its frozen manifest. The teacher can't be re-run (the credits are gone), so its row covers the seeds only, from the pilot.

## Results

<!-- ood:start -->
Not run yet: waiting for the hand check.
<!-- ood:end -->
