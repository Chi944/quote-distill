# generative student

Documents: 300

| Measure | Result |
|---|---|
| Parsed as JSON | 298/300 (99.3%) |
| Schema-valid | 297/300 (99.0%) |
| Critical fields exact | 2674/2700 (99.0%) |
| Line items: precision / recall / F1 | 1299/1312 (99.0%) / 1299/1318 (98.6%) / 0.988 |
| Document discounts: precision / recall / F1 | 75/75 (100.0%) / 75/77 (97.4%) / 0.987 |
| Invented values (gold not_stated, predicted stated) | 0/2384 (0.0%) |
| Omitted values (gold stated, predicted not_stated) | 6 |
| Arithmetic agrees with gold | 289/300 (96.3%) |
| Arithmetic internally consistent | 265/300 (88.3%) |
| Whole document exact | 275/300 (91.7%) |

| Field | Exact |
|---|---|
| supplier | 298/300 (99.3%) |
| quote_number | 298/300 (99.3%) |
| date | 294/300 (98.0%) |
| currency | 296/300 (98.7%) |
| subtotal | 298/300 (99.3%) |
| total | 298/300 (99.3%) |
| validity | 294/300 (98.0%) |
| payment_terms | 298/300 (99.3%) |
| gst.treatment | 296/300 (98.7%) |
| gst.rate | 298/300 (99.3%) |
| gst.amount | 298/300 (99.3%) |
| line.description (by position) | 1309/1319 (99.2%) |
| line.quantity (by position) | 1311/1319 (99.4%) |
| line.unit (by position) | 1307/1319 (99.1%) |
| line.unit_price (by position) | 1310/1319 (99.3%) |
| line.discount (by position) | 1306/1319 (99.0%) |
| line.line_total (by position) | 1310/1319 (99.3%) |

## Failing documents (25/300)

- **test-candidates-s1-000010**: `date` gold ('2026-12-09',) vs predicted ('2026-09-12',); `validity` gold ('2026-12-31',) vs predicted ('2026-09-30',)
- **test-candidates-s1-000085**: `line_items[2].discount` gold ('amount', '5.00') vs predicted not_stated
- **test-candidates-s1-000116**: `validity` gold ('2026-07-20',) vs predicted ('2020-07-20',)
- **test-candidates-s1-000167**: `validity` gold ('P90D',) vs predicted ('2026-04-29',)
- **test-candidates-s1-000252**: `line_items[1].unit` gold ('m',) vs predicted ('each',)
- **test-candidates-s1-000495**: `validity` gold ('2026-08-31',) vs predicted ('2026-08-30',)
- **test-candidates-s1-000600**: `line_items[1].unit` gold ('pair',) vs predicted ('each',)
- **test-candidates-s1-000714**: `date` gold ('2026-05-12',) vs predicted ('2026-12-05',)
- **test-candidates-s1-000958**: `currency` gold ('MYR',) vs predicted not_stated
- **test-candidates-s1-000982**: `gst.treatment` gold inclusive vs predicted exclusive
- **test-candidates-s1-001073**: `gst.treatment` gold inclusive vs predicted exclusive
- **test-candidates-s1-001075**: `line_items[1].discount` gold ('amount', '50.00') vs predicted not_stated
- **test-candidates-s1-001188**: `date` gold ('2026-08-12',) vs predicted ('2026-12-08',)
- **test-candidates-s1-001192**: `line_items[0].unit` gold ('m',) vs predicted ('each',)
- **test-candidates-s1-001194**: `line_items[1].discount` gold ('amount', '50.00') vs predicted not_stated; `line_items[1].line_total` gold ('171.84',) vs predicted ('50.00',)
- **test-candidates-s1-001351**: `line_items[4].unit` gold ('m',) vs predicted ('each',)
- **test-candidates-s1-001363**: `line_items[2].description` gold <missing> vs predicted ('Line 1',); `line_items[2].quantity` gold <missing> vs predicted not_stated; `line_items[2].unit` gold <missing> vs predicted ('lot',); `line_items[2].unit_price` gold <missing> vs predicted not_stated; `line_items[2].discount` gold <missing> vs predicted not_stated; `line_items[2].line_total` gold <missing> vs predicted ('0.00',)
- **test-candidates-s1-001401** (schema-invalid): `currency` gold ('SGD',) vs predicted ('SGD 6080.27',)
- **test-candidates-s1-001447** (no JSON): `supplier` gold ('Merrow Facilities Services Sdn Bhd',) vs predicted <missing>; `quote_number` gold ('MF-Q-26-8688',) vs predicted <missing>; `date` gold not_stated vs predicted <missing>; `currency` gold ('MYR',) vs predicted <missing>; `subtotal` gold ('543.87',) vs predicted <missing>; `total` gold ('489.48',) vs predicted <missing>; `validity` gold ('P45D',) vs predicted <missing>; `payment_terms` gold ('payment within 7 days of invoice',) vs predicted <missing>; and 37 more
- **test-candidates-s1-001512** (no JSON): `supplier` gold ('NORTHGATE FACILITIES SERVICES LLC',) vs predicted <missing>; `quote_number` gold not_stated vs predicted <missing>; `date` gold ('2026-09-26',) vs predicted <missing>; `currency` gold ('USD',) vs predicted <missing>; `subtotal` gold ('555.00',) vs predicted <missing>; `total` gold ('513.37',) vs predicted <missing>; `validity` gold not_stated vs predicted <missing>; `payment_terms` gold ('20th of the month following',) vs predicted <missing>; and 19 more
- **test-candidates-s1-001594**: `line_items[1].unit_price` gold ('-107.95',) vs predicted ('0.481',); `line_items[7].description` gold ('Treated pine 90x45 H3.2, 4.8m',) vs predicted ('Treated pine 90x45 4.8m',)
- **test-candidates-s1-002645**: `date` gold ('2026-09-10',) vs predicted ('2026-10-09',)
- **test-candidates-s1-002705**: `line_items[10].discount` gold ('percent', '15') vs predicted not_stated
- **test-candidates-s1-002807**: `line_items[4].discount` gold ('percent', '5') vs predicted not_stated
- **test-candidates-s1-002912**: `line_items[7].description` gold ('Elbow 90deg 25mm (galv)',) vs predicted ('Elbow 90deg 25mm',)
