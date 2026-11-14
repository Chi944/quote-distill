# generative student

Documents: 5

| Measure | Result |
|---|---|
| Parsed as JSON | 5/5 (100.0%) |
| Schema-valid | 4/5 (80.0%) |
| Critical fields exact | 44/45 (97.8%) |
| Line items: precision / recall / F1 | 15/17 (88.2%) / 15/17 (88.2%) / 0.882 |
| Document discounts: precision / recall / F1 | 0/1 (0.0%) / 0/1 (0.0%) / 0.000 |
| Invented values (gold not_stated, predicted stated) | 1/35 (2.9%) |
| Omitted values (gold stated, predicted not_stated) | 0 |
| Arithmetic agrees with gold | 3/5 (60.0%) |
| Arithmetic internally consistent | 3/5 (60.0%) |
| Whole document exact | 1/5 (20.0%) |

| Field | Exact |
|---|---|
| supplier | 4/5 (80.0%) |
| quote_number | 5/5 (100.0%) |
| date | 5/5 (100.0%) |
| currency | 5/5 (100.0%) |
| subtotal | 5/5 (100.0%) |
| total | 5/5 (100.0%) |
| validity | 5/5 (100.0%) |
| payment_terms | 4/5 (80.0%) |
| gst.treatment | 5/5 (100.0%) |
| gst.rate | 5/5 (100.0%) |
| gst.amount | 5/5 (100.0%) |
| line.description (by position) | 16/17 (94.1%) |
| line.quantity (by position) | 16/17 (94.1%) |
| line.unit (by position) | 16/17 (94.1%) |
| line.unit_price (by position) | 17/17 (100.0%) |
| line.discount (by position) | 17/17 (100.0%) |
| line.line_total (by position) | 17/17 (100.0%) |

## Failing documents (4/5)

- **seed-01**: `discounts[0].description` gold ('5% project disount',) vs predicted ('Less 5% project disount',)
- **seed-03**: `supplier` gold ('Sri Kenanga Trading',) vs predicted ('Lim W.K.',)
- **seed-04** (schema-invalid): `line_items[4].unit` gold not_stated vs predicted ('45.00',)
- **seed-05**: `payment_terms` gold ('the 20th of the month following, and you can take 2.5% off if paid within 7 days of invoice',) vs predicted ('the 20th of the month following',); `line_items[1].description` gold ('decking screws',) vs predicted ('Decking screws, three boxes',); `line_items[1].quantity` gold ('3',) vs predicted ('200',)
