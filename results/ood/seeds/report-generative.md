# generative student

Documents: 5

| Measure | Result |
|---|---|
| Parsed as JSON | 3/5 (60.0%) |
| Schema-valid | 2/5 (40.0%) |
| Critical fields exact | 23/45 (51.1%) |
| Line items: precision / recall / F1 | 8/9 (88.9%) / 8/17 (47.1%) / 0.615 |
| Document discounts: precision / recall / F1 | 0/0 (n/a) / 0/1 (0.0%) / 0.000 |
| Invented values (gold not_stated, predicted stated) | 1/35 (2.9%) |
| Omitted values (gold stated, predicted not_stated) | 1 |
| Arithmetic agrees with gold | 2/5 (40.0%) |
| Arithmetic internally consistent | 2/5 (40.0%) |
| Whole document exact | 1/5 (20.0%) |

| Field | Exact |
|---|---|
| supplier | 2/5 (40.0%) |
| quote_number | 3/5 (60.0%) |
| date | 3/5 (60.0%) |
| currency | 3/5 (60.0%) |
| subtotal | 2/5 (40.0%) |
| total | 2/5 (40.0%) |
| validity | 3/5 (60.0%) |
| payment_terms | 2/5 (40.0%) |
| gst.treatment | 2/5 (40.0%) |
| gst.rate | 3/5 (60.0%) |
| gst.amount | 3/5 (60.0%) |
| line.description (by position) | 8/17 (47.1%) |
| line.quantity (by position) | 8/17 (47.1%) |
| line.unit (by position) | 9/17 (52.9%) |
| line.unit_price (by position) | 9/17 (52.9%) |
| line.discount (by position) | 9/17 (52.9%) |
| line.line_total (by position) | 9/17 (52.9%) |

## Failing documents (4/5)

- **seed-01** (no JSON): `supplier` gold ('KESTREL LANE HARDWARE PTE. LTD.',) vs predicted <missing>; `quote_number` gold ('KLH-Q-26-0417',) vs predicted <missing>; `date` gold ('2026-10-18',) vs predicted <missing>; `currency` gold ('SGD',) vs predicted <missing>; `subtotal` gold ('494.90',) vs predicted <missing>; `total` gold ('470.15',) vs predicted <missing>; `validity` gold ('P14D',) vs predicted <missing>; `payment_terms` gold ('net 30 days',) vs predicted <missing>; and 25 more
- **seed-03**: `supplier` gold ('Sri Kenanga Trading',) vs predicted ('Lim W.K.',); `subtotal` gold not_stated vs predicted ('1669.00',); `total` gold ('1669.00',) vs predicted not_stated
- **seed-04** (no JSON): `supplier` gold ('HARROWGATE INSTRUMENTS INC.',) vs predicted <missing>; `quote_number` gold ('HI-26-1015-B',) vs predicted <missing>; `date` gold ('2026-10-15',) vs predicted <missing>; `currency` gold ('USD',) vs predicted <missing>; `subtotal` gold ('609.00',) vs predicted <missing>; `total` gold ('609.00',) vs predicted <missing>; `validity` gold ('P60D',) vs predicted <missing>; `payment_terms` gold ('100% t/t in advance',) vs predicted <missing>; and 33 more
- **seed-05** (schema-invalid): `payment_terms` gold ('the 20th of the month following, and you can take 2.5% off if paid within 7 days of invoice',) vs predicted ('20th of the month following',); `gst.treatment` gold exclusive vs predicted not_stated; `line_items[1].description` gold ('decking screws',) vs predicted ('Decking screws, three boxes (200 per box) at 14.90 a box',); `line_items[1].quantity` gold ('3',) vs predicted ('44.70',)
