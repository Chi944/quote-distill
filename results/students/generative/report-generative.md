# generative student

Documents: 300

| Measure | Result |
|---|---|
| Parsed as JSON | 297/300 (99.0%) |
| Schema-valid | 297/300 (99.0%) |
| Critical fields exact | 2664/2700 (98.7%) |
| Line items: precision / recall / F1 | 1298/1306 (99.4%) / 1298/1318 (98.5%) / 0.989 |
| Document discounts: precision / recall / F1 | 75/75 (100.0%) / 75/77 (97.4%) / 0.987 |
| Invented values (gold not_stated, predicted stated) | 0/2384 (0.0%) |
| Omitted values (gold stated, predicted not_stated) | 4 |
| Arithmetic agrees with gold | 293/300 (97.7%) |
| Arithmetic internally consistent | 267/300 (89.0%) |
| Whole document exact | 278/300 (92.7%) |

| Field | Exact |
|---|---|
| supplier | 297/300 (99.0%) |
| quote_number | 297/300 (99.0%) |
| date | 293/300 (97.7%) |
| currency | 297/300 (99.0%) |
| subtotal | 297/300 (99.0%) |
| total | 297/300 (99.0%) |
| validity | 295/300 (98.3%) |
| payment_terms | 297/300 (99.0%) |
| gst.treatment | 293/300 (97.7%) |
| gst.rate | 297/300 (99.0%) |
| gst.amount | 296/300 (98.7%) |
| line.description (by position) | 1302/1318 (98.8%) |
| line.quantity (by position) | 1303/1318 (98.9%) |
| line.unit (by position) | 1298/1318 (98.5%) |
| line.unit_price (by position) | 1302/1318 (98.8%) |
| line.discount (by position) | 1303/1318 (98.9%) |
| line.line_total (by position) | 1302/1318 (98.8%) |

## Failing documents (22/300)

- **test-candidates-s1-000010**: `date` gold ('2026-12-09',) vs predicted ('2026-09-12',); `validity` gold ('2026-12-31',) vs predicted ('2026-09-30',)
- **test-candidates-s1-000495**: `line_items[7].discount` gold ('amount', '50.00') vs predicted not_stated
- **test-candidates-s1-000714**: `date` gold ('2026-05-12',) vs predicted ('2026-12-05',)
- **test-candidates-s1-000751**: `validity` gold ('2027-01-15',) vs predicted ('2027-01-01',)
- **test-candidates-s1-000817**: `gst.treatment` gold exclusive vs predicted not_stated
- **test-candidates-s1-000897**: `line_items[3].description` gold ('Digital multimeter, CAT IV',) vs predicted ('Silicone sealant, clear 300g',); `line_items[3].quantity` gold ('1',) vs predicted ('14',); `line_items[3].unit_price` gold ('219.59',) vs predicted ('13.93',); `line_items[3].line_total` gold ('219.59',) vs predicted ('195.02',); `line_items[4].description` gold ('Silicone sealant, clear 300g',) vs predicted ('Decking screws 10g x 65mm, box of 200',); `line_items[4].unit` gold ('each',) vs predicted ('box',); `line_items[4].unit_price` gold ('13.93',) vs predicted ('20.08',); `line_items[4].line_total` gold ('195.02',) vs predicted ('281.12',); and 16 more
- **test-candidates-s1-000982**: `gst.amount` gold ('29.72',) vs predicted not_stated
- **test-candidates-s1-001188**: `date` gold ('2026-08-12',) vs predicted ('2026-12-08',)
- **test-candidates-s1-001216**: `line_items[5].discount` gold ('amount', '50.00') vs predicted not_stated
- **test-candidates-s1-001351**: `line_items[4].unit` gold ('m',) vs predicted ('each',)
- **test-candidates-s1-001402** (no JSON): `supplier` gold ('Merrow Facilities Services Inc.',) vs predicted <missing>; `quote_number` gold ('MF97321',) vs predicted <missing>; `date` gold ('2026-09-07',) vs predicted <missing>; `currency` gold ('USD',) vs predicted <missing>; `subtotal` gold ('280.00',) vs predicted <missing>; `total` gold ('280.00',) vs predicted <missing>; `validity` gold ('P90D',) vs predicted <missing>; `payment_terms` gold ('payment within 7 days of invoice',) vs predicted <missing>; and 9 more
- **test-candidates-s1-001447** (no JSON): `supplier` gold ('Merrow Facilities Services Sdn Bhd',) vs predicted <missing>; `quote_number` gold ('MF-Q-26-8688',) vs predicted <missing>; `date` gold not_stated vs predicted <missing>; `currency` gold ('MYR',) vs predicted <missing>; `subtotal` gold ('543.87',) vs predicted <missing>; `total` gold ('489.48',) vs predicted <missing>; `validity` gold ('P45D',) vs predicted <missing>; `payment_terms` gold ('payment within 7 days of invoice',) vs predicted <missing>; and 37 more
- **test-candidates-s1-001539**: `line_items[8].unit` gold ('m',) vs predicted ('each',)
- **test-candidates-s1-001594**: `line_items[8].unit` gold ('box',) vs predicted ('sheet',)
- **test-candidates-s1-001944**: `gst.treatment` gold exclusive vs predicted not_stated
- **test-candidates-s1-002028**: `gst.treatment` gold exclusive vs predicted not_stated
- **test-candidates-s1-002268** (no JSON): `supplier` gold ('Wattlebank Civil Supplies Sdn. Bhd.',) vs predicted <missing>; `quote_number` gold ('Q26/4804',) vs predicted <missing>; `date` gold ('2026-10-01',) vs predicted <missing>; `currency` gold ('MYR',) vs predicted <missing>; `subtotal` gold ('3476.70',) vs predicted <missing>; `total` gold ('3302.86',) vs predicted <missing>; `validity` gold ('2026-11-26',) vs predicted <missing>; `payment_terms` gold ('cod',) vs predicted <missing>; and 37 more
- **test-candidates-s1-002408**: `line_items[5].discount` gold ('amount', '20.00') vs predicted not_stated
- **test-candidates-s1-002645**: `date` gold ('2026-09-10',) vs predicted ('2026-10-09',)
- **test-candidates-s1-002705**: `line_items[0].unit` gold ('m',) vs predicted ('each',)
- **test-candidates-s1-002807**: `line_items[2].unit` gold ('l',) vs predicted ('each',)
- **test-candidates-s1-002990**: `gst.treatment` gold exclusive vs predicted not_stated
