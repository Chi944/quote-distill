# Student training data

The student trains on generator gold (teacher role A, decided 19 October 2026). This page records how that data is built and what it looks like.

## The step and how we know it worked

**Step.** Build a training set and a validation set from the generator, with every frozen test document and every pilot document removed, and write each label as the string the generative student will learn to produce.

**It worked when** no test or pilot text appears in either set, train and dev share no text, every target turns back into a schema-valid label that scores exact against its gold label, and a rebuild is byte-identical.

## Build

```bash
python -m quote_distill.student.data --out data/generated/student
```

It takes about two minutes on one CPU and writes `train.jsonl`, `dev.jsonl` and `stats.json`. The data folder is git-ignored because the command rebuilds it exactly; [`stats.json`](#result) records the hashes to check against.

| Set | Generator split and seed | Documents |
|---|---|---|
| train | `train`, seed 1 | 10,000 |
| dev | `dev`, seed 2 | 1,000 |

The pilot pool is `dev` seed 7 and the test pool is `test-candidates` seed 1, so their random streams don't overlap these sets. Both sets still go through `splits.exclude_test` and a pilot filter.

## Result

| Check | Train | Dev |
|---|---|---|
| Test documents dropped | 0 of 10,000 | 0 of 1,000 |
| Pilot documents dropped | 0 of 10,000 | 0 of 1,000 |
| Targets that expand back exact and schema-valid | 10,000/10,000 | 1,000/1,000 |
| Texts shared between train and dev | 0 | |
| Document length, characters (median / p95 / max) | 672 / 1,343 / 2,182 | 681 / 1,351 / 1,979 |
| Target length, characters (median / p95 / max) | 578 / 953 / 1,279 | 575 / 972 / 1,183 |
| Documents with every field located (spans) | 10,000/10,000 | 1,000/1,000 |
| File SHA-256 (first 12) | `7bde65f87aa2` | `c15dc3f9e84e` |

Token counts aren't measured yet, because this build environment can't reach the Hugging Face Hub to load a tokenizer. They'll be measured in the training notebook, which sets the model's maximum input and output lengths from them.

## Target format

The generative student writes a compact form of the label, and `student.data.expand` turns it back into the schema before scoring. The metrics, gates and failure gallery see exactly what they would see from the teacher.

- A field is its value, or `null` when it is not stated. A line discount stays an object (`{"kind": "percent", "value": "15"}`).
- A line item is a row in a fixed order: description, quantity, unit, unit price, discount, line total.
- `raw` and `schema_version` are left out. Outputs may omit `raw` and metrics never score it.

```json
{"supplier":"KESTREL LANE HARDWARE PTE. LTD.","quote_number":"KLH-Q-26-0417","date":"2026-10-18","currency":"SGD","subtotal":"494.90","total":"470.15","validity":"P14D","payment_terms":"net 30 days","line_items":[["Cordless drill 18V, 2 batteries","2","each","189.90",null,"379.80"],["Drill bit set (19 pc)","3","set","24.55",null,"73.65"],["Nitrile safety gloves, box/12pr","5","box","8.29",null,"41.45"]],"discounts":[{"description":"5% project disount","rate":"5","amount":"24.75","kind":"percent"}],"gst":{"treatment":"inclusive","rate":"9","amount":"38.82"}}
```

**Why not the full schema JSON?** The full form, without `raw`, has a median of 1,736 characters. The compact form has 578, a third as long. A small model in a browser generates one token at a time, so output length is the largest part of latency. The cost is one deterministic decoding step. A malformed output (a row with the wrong number of cells, a missing key) raises an error in `expand` and is scored as unparsed, the same as broken JSON from the teacher.

## Spans for the encoder tagger

The encoder tagger labels stretches of the document instead of writing a string, so each example also carries `spans`: `[start, end, field path]` for every stated field. A label records what was printed but not where, so [`student/spans.py`](../src/quote_distill/student/spans.py) finds the place.

1. It finds every occurrence of the field's `raw` text. Whitespace may differ, and a match may not split a word or a number, so `"2"` is never found inside `"12"`.
2. It places line-item descriptions in document order. Each row's region runs from its description's line to the next row, and the row's quantity, unit, prices and total are taken from that region, after the description where possible. This skips row numbers and a "2" inside "Drill, 2 batteries".
3. Totals, GST amounts and document discounts are looked for below the items. That way a "Discount" column header can't be mistaken for a discount row.
4. Every other field must then have exactly one free place. A subtotal printed the same as its total takes the earlier one.
5. A currency symbol, a GST rate or a discount rate printed inside another field's text (`NZ$ 101.75`, `10% trade discount`) is recorded in `nested` and not tagged. The tagger's decoder will read it out of the enclosing field.

Anything still ambiguous is reported and never guessed. Such a document would be left out of tagger training and counted, but none was: all 11,000 align. The tests check four things: every pilot document aligns, each span's text matches its `raw`, tagged spans never overlap, and a quote number printed twice is reported as ambiguous.

An alignment can be complete and still wrong, and there is no gold for positions. On 3,000 extra documents I checked that no row's fields fall after the next row's description, and that no total or subtotal sits above an item, with 0 violations. I also read a tagged prose quotation by eye.

## Decoding the tagger's output

[`student/decode.py`](../src/quote_distill/student/decode.py) turns tagged spans back into a schema label, so the tagger is scored with the same metrics as the teacher and the generative student. Each record's `classes` holds two answers the tagger predicts for the whole document, because neither is a stretch of text:

- **GST treatment:** exclusive, inclusive, not charged or not stated.
- **Date order:** whether numeric dates are written month first (US) or day first. `05/06/2026` reads differently in each.

The decoder groups line items and discounts by their descriptions, using the same row regions as the aligner. It converts printed text to values with the generator's own tables (units, currencies, date formats, half-up money). It reads a currency symbol or a rate from inside an enclosing field, and leaves anything untagged as not stated.

**Ceiling check.** Gold spans and gold classes, decoded, reproduce the gold label exactly for every document: 10,000/10,000 train and 1,000/1,000 dev, and all 20 pilot documents, including the five hand-written seeds. So any mistake in the tagger's results is the tagger's own, not the decoder's. Without the date-order class, guessing month-first from US-dollar currency alone gets 9,946/10,000 train and 993/1,000 dev, because a US quotation with a bare `$` has ambiguous dates. That's why date order is a class.

Next: convert spans to token tags in the training notebook, which needs a tokenizer.
