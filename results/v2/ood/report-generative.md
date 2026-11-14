# generative student

Documents: 30

| Measure | Result |
|---|---|
| Parsed as JSON | 26/30 (86.7%) |
| Schema-valid | 22/30 (73.3%) |
| Critical fields exact | 201/270 (74.4%) |
| Line items: precision / recall / F1 | 36/64 (56.2%) / 36/75 (48.0%) / 0.518 |
| Document discounts: precision / recall / F1 | 3/6 (50.0%) / 3/6 (50.0%) / 0.500 |
| Invented values (gold not_stated, predicted stated) | 11/156 (7.1%) |
| Omitted values (gold stated, predicted not_stated) | 47 |
| Arithmetic agrees with gold | 17/30 (56.7%) |
| Arithmetic internally consistent | 17/30 (56.7%) |
| Whole document exact | 1/30 (3.3%) |

| Field | Exact |
|---|---|
| supplier | 23/30 (76.7%) |
| quote_number | 19/30 (63.3%) |
| date | 22/30 (73.3%) |
| currency | 22/30 (73.3%) |
| subtotal | 19/30 (63.3%) |
| total | 23/30 (76.7%) |
| validity | 24/30 (80.0%) |
| payment_terms | 6/30 (20.0%) |
| gst.treatment | 23/30 (76.7%) |
| gst.rate | 26/30 (86.7%) |
| gst.amount | 24/30 (80.0%) |
| line.description (by position) | 56/75 (74.7%) |
| line.quantity (by position) | 49/75 (65.3%) |
| line.unit (by position) | 51/75 (68.0%) |
| line.unit_price (by position) | 60/75 (80.0%) |
| line.discount (by position) | 64/75 (85.3%) |
| line.line_total (by position) | 59/75 (78.7%) |

## Failing documents (29/30)

- **ood-01** (no JSON): `supplier` gold ('Novatone AV Rentals Pte. Ltd.',) vs predicted <missing>; `quote_number` gold ('NVT/AV/2611-07',) vs predicted <missing>; `date` gold ('2026-11-03',) vs predicted <missing>; `currency` gold ('SGD',) vs predicted <missing>; `subtotal` gold ('1323.50',) vs predicted <missing>; `total` gold ('1442.62',) vs predicted <missing>; `validity` gold ('P21D',) vs predicted <missing>; `payment_terms` gold ('50% deposit, balance on installation',) vs predicted <missing>; and 15 more
- **ood-03**: `payment_terms` gold ('payment within 7 days of delivery',) vs predicted not_stated
- **ood-04**: `subtotal` gold ('3260.00',) vs predicted not_stated
- **ood-05** (no JSON): `supplier` gold ('Greenhook Garden Centre',) vs predicted <missing>; `quote_number` gold not_stated vs predicted <missing>; `date` gold not_stated vs predicted <missing>; `currency` gold not_stated vs predicted <missing>; `subtotal` gold not_stated vs predicted <missing>; `total` gold ('271.00',) vs predicted <missing>; `validity` gold not_stated vs predicted <missing>; `payment_terms` gold ('cash on delivery',) vs predicted <missing>; and 21 more
- **ood-06**: `payment_terms` gold ('100% within 30 days of installation',) vs predicted not_stated; `line_items[2].quantity` gold ('1',) vs predicted not_stated; `line_items[2].unit_price` gold ('320.00',) vs predicted not_stated
- **ood-07**: `subtotal` gold ('1739.00',) vs predicted not_stated; `total` gold ('1912.90',) vs predicted ('1739.00',); `payment_terms` gold ('a 20% deposit confirms the booking; the balance is due 7 days before the event',) vs predicted not_stated
- **ood-08**: `currency` gold ('AUD',) vs predicted not_stated; `payment_terms` gold ('cod',) vs predicted not_stated
- **ood-09**: `payment_terms` gold ('payment 14 days',) vs predicted not_stated; `gst.treatment` gold inclusive vs predicted exclusive; `gst.amount` gold ('194.27',) vs predicted not_stated; `line_items[0].unit` gold not_stated vs predicted ('month',); `line_items[1].quantity` gold ('1',) vs predicted not_stated; `line_items[1].unit` gold not_stated vs predicted ('lot',); `line_items[1].unit_price` gold ('1480.00',) vs predicted not_stated
- **ood-10**: `quote_number` gold ('TT-77310',) vs predicted ('Quotation TT-77310',); `currency` gold ('AUD',) vs predicted not_stated; `subtotal` gold ('1024.00',) vs predicted not_stated; `line_items[0].description` gold ('Desk cable tray',) vs predicted ('12.40 Desk cable tray',); `line_items[0].line_total` gold ('496.00',) vs predicted ('12.40',); `line_items[1].description` gold ('Cable tie mount',) vs predicted ('3.95 Cable tie mount',); `line_items[1].quantity` gold ('40',) vs predicted ('4',); `line_items[1].line_total` gold ('158.00',) vs predicted ('3.95',); and 4 more
- **ood-11**: `payment_terms` gold ('payment by telegraphic transfer before shipment',) vs predicted not_stated; `gst.treatment` gold not_charged vs predicted not_stated; `line_items[0].quantity` gold ('1',) vs predicted ('3600',)
- **ood-12** (schema-invalid): `payment_terms` gold ('eft on order',) vs predicted not_stated; `line_items[0].quantity` gold ('5',) vs predicted ('374.50',); `line_items[1].quantity` gold ('5',) vs predicted ('99.50',); `line_items[2].quantity` gold ('1',) vs predicted ('45',); `line_items[2].unit` gold not_stated vs predicted ('each',); `line_items[2].line_total` gold ('45.00',) vs predicted ('145.00',)
- **ood-13**: `subtotal` gold ('2639.00',) vs predicted not_stated; `payment_terms` gold ('invoices are payable on the 20th of the month following',) vs predicted not_stated; `line_items[1].description` gold ('Travel and materials',) vs predicted ('Travel and materials 1 lot',)
- **ood-14**: `quote_number` gold ('KK-3020',) vs predicted ('Quote KK-3020',); `payment_terms` gold ('payment on the 20th of the following month',) vs predicted not_stated; `gst.treatment` gold inclusive vs predicted exclusive; `gst.amount` gold ('122.87',) vs predicted not_stated; `line_items[0].unit` gold not_stated vs predicted ('each',); `line_items[1].unit` gold not_stated vs predicted ('each',); `line_items[2].unit` gold not_stated vs predicted ('each',)
- **ood-15**: `quote_number` gold ('TTS-6602',) vs predicted ('QUOTE TTS-6602',); `payment_terms` gold ('booking confirmed on payment',) vs predicted not_stated; `line_items[0].unit` gold not_stated vs predicted ('each',); `line_items[1].unit` gold not_stated vs predicted ('each',); `discounts[0].description` gold ('10% group discount',) vs predicted ('Less 10% group discount',)
- **ood-16** (schema-invalid): `subtotal` gold ('528.00',) vs predicted not_stated; `total` gold ('607.20',) vs predicted ('528.00',); `payment_terms` gold ('payment 7 days',) vs predicted not_stated; `line_items[0].description` gold ('Seedlings, flax (Phormium), 1 L pots',) vs predicted ('Seedlings, flax (Phormium)',); `line_items[0].quantity` gold ('120',) vs predicted <missing>
- **ood-17**: `date` gold ('2026-11-06',) vs predicted not_stated; `payment_terms` gold ('payment 50% upfront, 50% on install',) vs predicted not_stated; `line_items[0].unit` gold not_stated vs predicted ('each',); `line_items[1].unit` gold not_stated vs predicted ('each',); `line_items[2].unit` gold not_stated vs predicted ('each',)
- **ood-18** (no JSON): `supplier` gold ('Rimu Valley Auto Electrical Ltd',) vs predicted <missing>; `quote_number` gold ('RVA-0087',) vs predicted <missing>; `date` gold ('2026-11-10',) vs predicted <missing>; `currency` gold ('NZD',) vs predicted <missing>; `subtotal` gold ('2310.00',) vs predicted <missing>; `total` gold ('2656.50',) vs predicted <missing>; `validity` gold ('P14D',) vs predicted <missing>; `payment_terms` gold ('account customers 20th of month',) vs predicted <missing>; and 21 more
- **ood-19**: `supplier` gold ('Cendana Lab Glassware Sdn. Bhd.',) vs predicted ('SEBUT HARGA / QUOTATION',); `payment_terms` gold ('30 hari / 30 days',) vs predicted ('30 day',)
- **ood-20**: `subtotal` gold ('4260.00',) vs predicted not_stated; `total` gold ('4110.00',) vs predicted ('4260.00',); `payment_terms` gold ('30% with po, 70% before delivery',) vs predicted not_stated
- **ood-21**: `payment_terms` gold ('cash or cheque upon delivery',) vs predicted not_stated
- **ood-22**: `quote_number` gold ('MSS-PQ-0093',) vs predicted not_stated; `payment_terms` gold ('irrevocable l/c at sight',) vs predicted not_stated; `line_items[0].quantity` gold ('1',) vs predicted ('4200',); `line_items[1].quantity` gold ('1',) vs predicted ('650',)
- **ood-23**: `supplier` gold ('Seri Pandan Food Ingredients Sdn Bhd',) vs predicted ('Pandan Food Ingredients Sdn Bhd',); `payment_terms` gold ('payment 14 days from delivery',) vs predicted not_stated
- **ood-24** (schema-invalid): `quote_number` gold ('RSR/26/115',) vs predicted ('SRR/26/115',); `currency` gold ('MYR',) vs predicted not_stated; `validity` gold ('P10D',) vs predicted ('P4W',); `payment_terms` gold ('payment in advance',) vs predicted ('none',); `line_items[0].quantity` gold ('3',) vs predicted not_stated; `line_items[0].unit` gold ('set',) vs predicted ('lot',); `line_items[0].unit_price` gold ('980.00',) vs predicted not_stated; `line_items[0].line_total` gold ('2940.00',) vs predicted ('980.00',); and 1 more
- **ood-25** (no JSON): `supplier` gold ('Bayou Bend Office Tech LLC',) vs predicted <missing>; `quote_number` gold ('BB-104417',) vs predicted <missing>; `date` gold ('2026-11-04',) vs predicted <missing>; `currency` gold ('USD',) vs predicted <missing>; `subtotal` gold ('1768.92',) vs predicted <missing>; `total` gold ('1768.92',) vs predicted <missing>; `validity` gold ('2026-12-04',) vs predicted <missing>; `payment_terms` gold ('net 30 for approved accounts',) vs predicted <missing>; and 21 more
- **ood-26** (schema-invalid): `supplier` gold ('Prairie Lark Fastener Supply Inc.',) vs predicted ('Prairie Lark Lark Fastener Supply Inc.',); `quote_number` gold ('PLF-77-2091',) vs predicted ('Quote PLF-77-2091',); `currency` gold ('USD',) vs predicted not_stated; `line_items[0].description` gold ('Hex bolt 3/8-16 x 1-1/2, zinc',) vs predicted ('Hex bolt 3/8-16 x 1-1/2',); `line_items[0].quantity` gold ('200',) vs predicted ('84',); `line_items[1].description` gold ('Wood screw #8 x 1-1/4, box of 100',) vs predicted ('Wood screw #8 x 1-1/4',); `line_items[1].quantity` gold ('50',) vs predicted ('157.50',); `line_items[2].quantity` gold ('1',) vs predicted ('75',); and 1 more
- **ood-27**: `subtotal` gold ('6420.00',) vs predicted not_stated; `validity` gold ('P45D',) vs predicted not_stated; `payment_terms` gold ('progress billing, net 15',) vs predicted not_stated; `discounts[0].amount` gold ('481.50',) vs predicted not_stated
- **ood-28**: `quote_number` gold ('CHM-Q-56012',) vs predicted ('Quote CHM-Q-56012',); `date` gold ('2026-11-10',) vs predicted not_stated
- **ood-29**: `date` gold ('2026-11-06',) vs predicted not_stated; `line_items[0].quantity` gold ('1',) vs predicted not_stated; `line_items[0].unit_price` gold ('1200.00',) vs predicted not_stated
- **ood-30**: `date` gold ('2026-11-12',) vs predicted not_stated; `payment_terms` gold ('wire transfer in advance',) vs predicted not_stated
