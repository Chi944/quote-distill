# Synthetic quotation generator

```bash
quote-distill-generate --n 500 --seed 1 --split dev --out data/generated/dev
```

This writes `docs.jsonl`, one record per document with `text`, gold `label` and `meta` (locale, layout, hard-case features, intended check failures, check counts and text hash), plus `stats.json` with coverage counts and any rejections. The same `--n`, `--seed` and `--split` always produce identical output. `data/generated/` is git-ignored. A 20-document sample is committed in [`data/samples/dev-s1-n20`](../data/samples/dev-s1-n20).

## How a document is made

1. **Sample** ([`sample.py`](../src/quote_distill/generator/sample.py)). Values are drawn first: locale, supplier, lines, discounts, GST, header fields and terms. Totals use the canonical arithmetic in [schema.md](schema.md). The printed form of every value (`$1,214.64`, `sht`, `three`, `17/10/2026`) is decided at the same point, and the label's `raw` is that exact string.
2. **Render** ([`layouts.py`](../src/quote_distill/generator/layouts.py)). One of five layouts arranges those strings: fixed-width table, pipe table, item blocks, email list or prose email. Layouts never invent values.
3. **Check** ([`checks.py`](../src/quote_distill/checks.py)). Each label is validated against the JSON Schema. Every `raw` must appear in the text, and every value must re-derive from its `raw` (numbers, units, currencies, dates and validity). The arithmetic must fail exactly where the sampler planted a supplier error. A document that fails any check is dropped and counted in `stats.json`.

## Hard cases and how often they occur

Measured on 10,000 training documents (seed 11). Each count is the number of documents with at least one instance, so a document can appear in several rows.

| Feature | Documents |
|---|---|
| GST exclusive / inclusive / not charged / not stated | 3,029 / 1,446 / 1,771 / 3,754 |
| "Plus GST" with no amount and no total | 614 |
| GST rate not printed | 456 |
| Bare `$` (currency not_stated) | 1,619 |
| Document discount, amount printed / not printed | 1,779 / 196 |
| Half-cent tie on a discount or GST amount (half-up and banker's rounding differ) | 248 |
| Line discount, percent / amount | 2,384 / 1,629 |
| Lump-sum row / every row lump sum | 4,140 / 96 |
| Free-of-charge row / credit row | 986 / 665 |
| Decimal quantity / quantity in words / unit price with fractions of a cent (e.g. `$0.351`) | 3,432 / 1,583 / 586 |
| Supplier arithmetic error kept as printed | 586 |
| Missing quote number / date / subtotal / total / validity / payment terms | 1,212 / 992 / 1,872 / 1,365 / 1,944 / 2,006 |
| Relative validity ("end of this month") | 1,110 |
| Conditional early-payment discount in payment terms | 1,184 |
| Header typos / description typos | 3,022 / 2,681 |
| Customer reference that is not a quote number | 5,100 |
| Layout: fixed table / pipe table / item blocks / email list / prose email | 2,467 / 2,483 / 1,619 / 1,733 / 1,698 |
| Locale: SG / AU / NZ / MY / US | 1,963 / 2,018 / 2,017 / 1,912 / 2,090 |

The 10,000 documents (44,534 line items) had **0 rejections**: 59,578 arithmetic checks passed, 586 failed as intended and 16,345 were skipped because their inputs were not printed. A second run (seed 12) gave the same result, and all 20,000 texts were distinct. Each run of 10,000 takes about 45 seconds on one CPU.

## Known limits

- The generator and checker share the rounding helper in `money.py`. If that helper had a bug, both would agree on the wrong answer. The independent evidence is the hand-authored seeds (computed by hand) and, later, the 300 hand-checked test documents.
- The checker proves that every stated value is supported by the text. It does not prove that every printed value was labelled. Tests cover the riskiest cases (GST mentioned when not_stated, a currency token in a bare-`$` document, a quote number printed but unlabelled), but the full check is the hand review of the test set.
- Documents are plain text. Scans, PDFs and OCR noise are out of scope for this version, and typos are the only noise.
- Supplier names are random word combinations. Any match with a real business is unintended.
