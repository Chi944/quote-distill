# Quotation schema v1.0.0

The machine-readable schema is [`schema/quotation.schema.json`](../schema/quotation.schema.json) (JSON Schema 2020-12). This page holds the rules the schema cannot express. The generator, the teacher prompt, the checker and the metrics all follow these rules, so a change here is a schema version bump.

## Field objects

Every scalar is one of two shapes:

```json
{"state": "stated", "value": "1214.64", "raw": "$1,214.64"}
{"state": "not_stated"}
```

- `not_stated` means the document does not print the value. It never means "zero", "unknown but probably X" or "I could not read it". The extractor must not infer a value that is not printed (no assumed 15% NZ GST, no currency guessed from an address).
- `raw` is a verbatim substring of the document. Gold labels always carry it; model outputs may omit it. Metrics score `value` and `state` only.
- Values are re-derivable from `raw` by the rules below. The checker enforces this for text, numbers and dates.

## Normalisation

| Field | Rule | Example raw → value |
|---|---|---|
| Money (`line_total`, `subtotal`, `total`, amounts) | Strip symbols, codes and thousands separators; exactly 2 decimals; `-` for credits | `$1,852.50` → `1852.50`; `$65` → `65.00` |
| `unit_price` | As money, 2 to 4 decimals; free of charge is `0.00` | `FOC` → `0.00` |
| `quantity`, rates | Non-negative decimal, no trailing zeros; number words converted | `three` → `3`; `9%` → `9` |
| `date` | ISO 8601, read with the document's locale | `17/10/2026` (AU) → `2026-10-17` |
| `currency` | ISO 4217, only from a code or an unambiguous symbol or name | `RM` → `MYR`; bare `$` → not_stated |
| `unit` | Controlled vocabulary in the schema | `pcs`, `ea`, `units` → `each`; `L/S`, `flat` → `lot` |
| `validity` | `P{n}D` for a period, ISO date for an end date; relative end dates resolved against the quote date | `end of this month` (20 Oct 2026) → `2026-10-31` |
| `supplier`, `quote_number`, `description` | Raw text with whitespace collapsed; typos kept; part numbers in a separate column excluded | `Galvinised pipe 25mm x 6m` |
| `payment_terms` | Raw with whitespace collapsed, casefolded, trailing full stop removed | `Net 30 days.` → `net 30 days` |

## What goes where

- **Line items** are every priced row that sums into the subtotal: goods, services, delivery, labour, free-of-charge rows and credits, in document order.
- A **lump-sum row** has `unit: lot` and `quantity`/`unit_price` not_stated unless the document prints them.
- A **line discount** belongs to its row. A **document discount** applies to the subtotal. A **conditional discount** (early payment, volume rebate) is only text in `payment_terms`.
- **GST treatment:** `exclusive` (added on top), `inclusive` (already inside prices), `not_charged` (document says no GST, for example export), `not_stated` (never mentioned).
- **Labels record what is printed**, including supplier mistakes. A wrong printed line total stays wrong in the label; the generator lists it as an intended check failure.

## Canonical arithmetic

All rounding is half-up to cents (`Decimal.quantize(Decimal("0.01"), ROUND_HALF_UP)`), never floats.

1. `line_total = round(quantity × unit_price) − line_discount`, where a percent discount is `round(gross × rate / 100)`.
2. `subtotal = Σ line_total` (before document discounts and GST).
3. Percent document discount: `amount = round(subtotal × rate / 100)`.
4. `taxable = subtotal − Σ document discounts`.
5. GST exclusive: `gst = round(taxable × rate / 100)`, `total = taxable + gst`.
6. GST inclusive: `total = taxable`, `gst = round(total × rate / (100 + rate))`.
7. GST not charged or not stated: `total = taxable`.

A check whose inputs are not_stated is skipped and counted as skipped, never as a pass. A label is kept only when its failed checks equal its intended failures exactly ([`src/quote_distill/checks.py`](../src/quote_distill/checks.py)).
