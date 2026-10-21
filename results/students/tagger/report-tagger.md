# tagger student

Documents: 300

| Measure | Result |
|---|---|
| Parsed as JSON | 300/300 (100.0%) |
| Schema-valid | 300/300 (100.0%) |
| Critical fields exact | 2700/2700 (100.0%) |
| Line items: precision / recall / F1 | 1318/1318 (100.0%) / 1318/1318 (100.0%) / 1.000 |
| Document discounts: precision / recall / F1 | 76/77 (98.7%) / 76/77 (98.7%) / 0.987 |
| Invented values (gold not_stated, predicted stated) | 0/2384 (0.0%) |
| Omitted values (gold stated, predicted not_stated) | 1 |
| Arithmetic agrees with gold | 300/300 (100.0%) |
| Arithmetic internally consistent | 274/300 (91.3%) |
| Whole document exact | 299/300 (99.7%) |

| Field | Exact |
|---|---|
| supplier | 300/300 (100.0%) |
| quote_number | 300/300 (100.0%) |
| date | 300/300 (100.0%) |
| currency | 300/300 (100.0%) |
| subtotal | 300/300 (100.0%) |
| total | 300/300 (100.0%) |
| validity | 300/300 (100.0%) |
| payment_terms | 300/300 (100.0%) |
| gst.treatment | 300/300 (100.0%) |
| gst.rate | 300/300 (100.0%) |
| gst.amount | 300/300 (100.0%) |
| line.description (by position) | 1318/1318 (100.0%) |
| line.quantity (by position) | 1318/1318 (100.0%) |
| line.unit (by position) | 1318/1318 (100.0%) |
| line.unit_price (by position) | 1318/1318 (100.0%) |
| line.discount (by position) | 1318/1318 (100.0%) |
| line.line_total (by position) | 1318/1318 (100.0%) |

## Failing documents (1/300)

- **test-candidates-s1-000258**: `discounts[0].rate` gold ('10',) vs predicted not_stated
