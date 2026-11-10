# tagger student

Documents: 5

| Measure | Result |
|---|---|
| Parsed as JSON | 5/5 (100.0%) |
| Schema-valid | 5/5 (100.0%) |
| Critical fields exact | 41/45 (91.1%) |
| Line items: precision / recall / F1 | 16/23 (69.6%) / 16/17 (94.1%) / 0.800 |
| Document discounts: precision / recall / F1 | 0/1 (0.0%) / 0/1 (0.0%) / 0.000 |
| Invented values (gold not_stated, predicted stated) | 4/35 (11.4%) |
| Omitted values (gold stated, predicted not_stated) | 19 |
| Arithmetic agrees with gold | 4/5 (80.0%) |
| Arithmetic internally consistent | 3/5 (60.0%) |
| Whole document exact | 1/5 (20.0%) |

| Field | Exact |
|---|---|
| supplier | 5/5 (100.0%) |
| quote_number | 3/5 (60.0%) |
| date | 4/5 (80.0%) |
| currency | 5/5 (100.0%) |
| subtotal | 5/5 (100.0%) |
| total | 5/5 (100.0%) |
| validity | 3/5 (60.0%) |
| payment_terms | 2/5 (40.0%) |
| gst.treatment | 4/5 (80.0%) |
| gst.rate | 5/5 (100.0%) |
| gst.amount | 5/5 (100.0%) |
| line.description (by position) | 9/23 (39.1%) |
| line.quantity (by position) | 9/23 (39.1%) |
| line.unit (by position) | 9/23 (39.1%) |
| line.unit_price (by position) | 9/23 (39.1%) |
| line.discount (by position) | 17/23 (73.9%) |
| line.line_total (by position) | 9/23 (39.1%) |

## Failing documents (4/5)

- **seed-01**: `quote_number` gold ('KLH-Q-26-0417',) vs predicted ('M9-0000417-X',); `validity` gold ('P14D',) vs predicted not_stated; `payment_terms` gold ('net 30 days',) vs predicted ('from',); `line_items[0].description` gold ('Cordless drill 18V, 2 batteries',) vs predicted (')',); `line_items[0].quantity` gold ('2',) vs predicted not_stated; `line_items[0].unit` gold ('each',) vs predicted not_stated; `line_items[0].unit_price` gold ('189.90',) vs predicted not_stated; `line_items[0].line_total` gold ('379.80',) vs predicted not_stated; and 17 more
- **seed-02**: `gst.treatment` gold exclusive vs predicted not_charged
- **seed-03**: `payment_terms` gold not_stated vs predicted ('stock',); `line_items[0].description` gold ('Galvinised pipe 25mm x 6m',) vs predicted ('fittings',); `line_items[0].quantity` gold ('40',) vs predicted not_stated; `line_items[0].unit` gold ('length',) vs predicted not_stated; `line_items[0].unit_price` gold ('38.50',) vs predicted not_stated; `line_items[0].line_total` gold ('1540.00',) vs predicted not_stated; `line_items[1].description` gold ('Elbow 90deg 25mm (galv)',) vs predicted ('Galvinised pipe 25mm x 6m',); `line_items[1].quantity` gold ('60',) vs predicted ('40',); and 15 more
- **seed-05**: `quote_number` gold not_stated vs predicted ('09',); `date` gold ('2026-10-20',) vs predicted not_stated; `validity` gold ('2026-10-31',) vs predicted not_stated; `payment_terms` gold ('the 20th of the month following, and you can take 2.5% off if paid within 7 days of invoice',) vs predicted ('account',); `line_items[0].description` gold ('H3.2 treated pine 90x45 in 4.8m lengths',) vs predicted ('ing',); `line_items[0].quantity` gold ('24',) vs predicted not_stated; `line_items[0].unit` gold ('length',) vs predicted not_stated; `line_items[0].unit_price` gold ('11.60',) vs predicted not_stated; and 29 more
