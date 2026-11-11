# tagger student

Documents: 5

| Measure | Result |
|---|---|
| Parsed as JSON | 5/5 (100.0%) |
| Schema-valid | 5/5 (100.0%) |
| Critical fields exact | 42/45 (93.3%) |
| Line items: precision / recall / F1 | 16/23 (69.6%) / 16/17 (94.1%) / 0.800 |
| Document discounts: precision / recall / F1 | 0/2 (0.0%) / 0/1 (0.0%) / 0.000 |
| Invented values (gold not_stated, predicted stated) | 3/35 (8.6%) |
| Omitted values (gold stated, predicted not_stated) | 17 |
| Arithmetic agrees with gold | 4/5 (80.0%) |
| Arithmetic internally consistent | 3/5 (60.0%) |
| Whole document exact | 2/5 (40.0%) |

| Field | Exact |
|---|---|
| supplier | 4/5 (80.0%) |
| quote_number | 4/5 (80.0%) |
| date | 5/5 (100.0%) |
| currency | 5/5 (100.0%) |
| subtotal | 5/5 (100.0%) |
| total | 4/5 (80.0%) |
| validity | 4/5 (80.0%) |
| payment_terms | 3/5 (60.0%) |
| gst.treatment | 5/5 (100.0%) |
| gst.rate | 5/5 (100.0%) |
| gst.amount | 5/5 (100.0%) |
| line.description (by position) | 12/23 (52.2%) |
| line.quantity (by position) | 12/23 (52.2%) |
| line.unit (by position) | 12/23 (52.2%) |
| line.unit_price (by position) | 12/23 (52.2%) |
| line.discount (by position) | 17/23 (73.9%) |
| line.line_total (by position) | 12/23 (52.2%) |

## Failing documents (3/5)

- **seed-01**: `quote_number` gold ('KLH-Q-26-0417',) vs predicted ('0142',); `total` gold ('470.15',) vs predicted ('6.00',); `payment_terms` gold ('net 30 days',) vs predicted not_stated; `discounts[0].description` gold ('5% project disount',) vs predicted ('Less 5% project disount',)
- **seed-03**: `supplier` gold ('Sri Kenanga Trading',) vs predicted ('.',); `validity` gold not_stated vs predicted ('P3D',); `line_items[0].description` gold ('Galvinised pipe 25mm x 6m',) vs predicted ('pipe',); `line_items[0].quantity` gold ('40',) vs predicted not_stated; `line_items[0].unit` gold ('length',) vs predicted not_stated; `line_items[0].unit_price` gold ('38.50',) vs predicted not_stated; `line_items[0].line_total` gold ('1540.00',) vs predicted not_stated; `line_items[1].description` gold ('Elbow 90deg 25mm (galv)',) vs predicted ('fittings',); and 26 more
- **seed-05**: `payment_terms` gold ('the 20th of the month following, and you can take 2.5% off if paid within 7 days of invoice',) vs predicted ('the 20th of the month following',); `line_items[0].description` gold ('H3.2 treated pine 90x45 in 4.8m lengths',) vs predicted ('decking job',); `line_items[0].quantity` gold ('24',) vs predicted not_stated; `line_items[0].unit` gold ('length',) vs predicted not_stated; `line_items[0].unit_price` gold ('11.60',) vs predicted not_stated; `line_items[0].line_total` gold ('278.40',) vs predicted not_stated; `line_items[1].description` gold ('decking screws',) vs predicted ('the deck',); `line_items[1].quantity` gold ('3',) vs predicted not_stated; and 26 more
