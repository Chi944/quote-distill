Documents: 20

| Gate | Result | Pass |
|---|---|---|
| Schema-valid JSON, no repair | 20/20 (100.0%) | yes |
| Critical fields exact | 180/180 (100.0%) | yes |
| Line-item F1 (all six fields) | 1.000 | yes |
| Invented values | 0/165 (0.0%) | yes |
| Arithmetic agrees with gold | 20/20 (100.0%) | yes |

| Measure | Result |
|---|---|
| Parsed as JSON | 20/20 (100.0%) |
| Schema-valid | 20/20 (100.0%) |
| Critical fields exact | 180/180 (100.0%) |
| Line items: precision / recall / F1 | 90/90 (100.0%) / 90/90 (100.0%) / 1.000 |
| Document discounts: precision / recall / F1 | 4/5 (80.0%) / 4/5 (80.0%) / 0.800 |
| Invented values (gold not_stated, predicted stated) | 0/165 (0.0%) |
| Omitted values (gold stated, predicted not_stated) | 0 |
| Arithmetic agrees with gold | 20/20 (100.0%) |
| Arithmetic internally consistent | 16/20 (80.0%) |
| Whole document exact | 18/20 (90.0%) |

| Field | Exact |
|---|---|
| supplier | 20/20 (100.0%) |
| quote_number | 20/20 (100.0%) |
| date | 20/20 (100.0%) |
| currency | 20/20 (100.0%) |
| subtotal | 20/20 (100.0%) |
| total | 20/20 (100.0%) |
| validity | 20/20 (100.0%) |
| payment_terms | 19/20 (95.0%) |
| gst.treatment | 20/20 (100.0%) |
| gst.rate | 20/20 (100.0%) |
| gst.amount | 20/20 (100.0%) |
| line.description (by position) | 90/90 (100.0%) |
| line.quantity (by position) | 90/90 (100.0%) |
| line.unit (by position) | 90/90 (100.0%) |
| line.unit_price (by position) | 90/90 (100.0%) |
| line.discount (by position) | 90/90 (100.0%) |
| line.line_total (by position) | 90/90 (100.0%) |

## Failing documents (2/20)

- **seed-01**: `discounts[0].description` gold ('5% project disount',) vs predicted ('Less 5% project disount',)
- **seed-05**: `payment_terms` gold ('the 20th of the month following, and you can take 2.5% off if paid within 7 days of invoice',) vs predicted ('account terms are the 20th of the month following, and you can take 2.5% off if paid within 7 days of invoice',)

