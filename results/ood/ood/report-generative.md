# generative student

Documents: 30

| Measure | Result |
|---|---|
| Parsed as JSON | 21/30 (70.0%) |
| Schema-valid | 15/30 (50.0%) |
| Critical fields exact | 152/270 (56.3%) |
| Line items: precision / recall / F1 | 33/51 (64.7%) / 33/75 (44.0%) / 0.524 |
| Document discounts: precision / recall / F1 | 0/4 (0.0%) / 0/6 (0.0%) / 0.000 |
| Invented values (gold not_stated, predicted stated) | 11/156 (7.1%) |
| Omitted values (gold stated, predicted not_stated) | 49 |
| Arithmetic agrees with gold | 10/30 (33.3%) |
| Arithmetic internally consistent | 10/30 (33.3%) |
| Whole document exact | 0/30 (0.0%) |

| Field | Exact |
|---|---|
| supplier | 19/30 (63.3%) |
| quote_number | 9/30 (30.0%) |
| date | 12/30 (40.0%) |
| currency | 20/30 (66.7%) |
| subtotal | 15/30 (50.0%) |
| total | 18/30 (60.0%) |
| validity | 18/30 (60.0%) |
| payment_terms | 3/30 (10.0%) |
| gst.treatment | 18/30 (60.0%) |
| gst.rate | 20/30 (66.7%) |
| gst.amount | 21/30 (70.0%) |
| line.description (by position) | 49/75 (65.3%) |
| line.quantity (by position) | 44/75 (58.7%) |
| line.unit (by position) | 38/75 (50.7%) |
| line.unit_price (by position) | 46/75 (61.3%) |
| line.discount (by position) | 51/75 (68.0%) |
| line.line_total (by position) | 49/75 (65.3%) |

## Failing documents (30/30)

- **ood-01** (no JSON): `supplier` gold ('Novatone AV Rentals Pte. Ltd.',) vs predicted <missing>; `quote_number` gold ('NVT/AV/2611-07',) vs predicted <missing>; `date` gold ('2026-11-03',) vs predicted <missing>; `currency` gold ('SGD',) vs predicted <missing>; `subtotal` gold ('1323.50',) vs predicted <missing>; `total` gold ('1442.62',) vs predicted <missing>; `validity` gold ('P21D',) vs predicted <missing>; `payment_terms` gold ('50% deposit, balance on installation',) vs predicted <missing>; and 15 more
- **ood-02**: `date` gold ('2026-11-09',) vs predicted not_stated; `subtotal` gold ('701.30',) vs predicted not_stated; `total` gold ('741.48',) vs predicted ('701.30',); `discounts[0].description` gold ('Loyalty discount 3%',) vs predicted ('Loyalty discount',); `discounts[0].kind` gold percent vs predicted amount
- **ood-03**: `payment_terms` gold ('payment within 7 days of delivery',) vs predicted not_stated; `line_items[1].description` gold ('Insulated food carrier 20L',) vs predicted ('Insulated food carrier 20L;6 each',); `line_items[1].quantity` gold ('6',) vs predicted ('1',); `line_items[1].unit` gold ('each',) vs predicted ('box',)
- **ood-04**: `quote_number` gold ('CLD-2026-1144',) vs predicted not_stated; `subtotal` gold ('3260.00',) vs predicted not_stated; `gst.rate` gold ('9',) vs predicted not_stated
- **ood-05** (no JSON): `supplier` gold ('Greenhook Garden Centre',) vs predicted <missing>; `quote_number` gold not_stated vs predicted <missing>; `date` gold not_stated vs predicted <missing>; `currency` gold not_stated vs predicted <missing>; `subtotal` gold not_stated vs predicted <missing>; `total` gold ('271.00',) vs predicted <missing>; `validity` gold not_stated vs predicted <missing>; `payment_terms` gold ('cash on delivery',) vs predicted <missing>; and 21 more
- **ood-06**: `payment_terms` gold ('100% within 30 days of installation',) vs predicted not_stated; `line_items[2].quantity` gold ('1',) vs predicted not_stated; `line_items[2].unit_price` gold ('320.00',) vs predicted not_stated; `discounts[0].description` gold ('Special discount',) vs predicted ('Special discount -200.00',)
- **ood-07** (schema-invalid): `quote_number` gold ('SEH-4471',) vs predicted not_stated; `subtotal` gold ('1739.00',) vs predicted not_stated; `total` gold ('1912.90',) vs predicted ('1739.00',); `payment_terms` gold ('a 20% deposit confirms the booking; the balance is due 7 days before the event',) vs predicted not_stated; `line_items[0].description` gold ('Supply and erect 6x12 m marquee',) vs predicted ('Marquee hire, Spring Fair',); `line_items[2].line_total` gold ('95.00',) vs predicted ('95.00.00',)
- **ood-08**: `payment_terms` gold ('cod',) vs predicted not_stated
- **ood-09**: `payment_terms` gold ('payment 14 days',) vs predicted not_stated; `gst.treatment` gold inclusive vs predicted exclusive; `line_items[0].unit` gold not_stated vs predicted ('month',); `line_items[1].quantity` gold ('1',) vs predicted not_stated; `line_items[1].unit` gold not_stated vs predicted ('lot',); `line_items[1].unit_price` gold ('1480.00',) vs predicted not_stated
- **ood-10** (no JSON): `supplier` gold ('Tea Tree Office Furniture Pty Ltd',) vs predicted <missing>; `quote_number` gold ('TT-77310',) vs predicted <missing>; `date` gold ('2026-11-03',) vs predicted <missing>; `currency` gold ('AUD',) vs predicted <missing>; `subtotal` gold ('1024.00',) vs predicted <missing>; `total` gold ('1070.08',) vs predicted <missing>; `validity` gold ('P60D',) vs predicted <missing>; `payment_terms` gold ('30 days; 2% off if paid within 7 days',) vs predicted <missing>; and 25 more
- **ood-11**: `supplier` gold ('BLUEWREN MARINE ELECTRONICS PTY LTD',) vs predicted ('BLUEWREN MARINE ELECTRONICS PTY LTD — EXPORT QUOTATION',); `payment_terms` gold ('payment by telegraphic transfer before shipment',) vs predicted not_stated; `gst.treatment` gold not_charged vs predicted not_stated
- **ood-12** (schema-invalid): `quote_number` gold ('KCC-2210',) vs predicted ('QUOTE KCC-2210',); `date` gold ('2026-11-01',) vs predicted not_stated; `payment_terms` gold ('eft on order',) vs predicted not_stated; `line_items[0].quantity` gold ('5',) vs predicted ('74.90',); `line_items[0].unit_price` gold ('74.90',) vs predicted ('374.50',); `line_items[0].line_total` gold ('374.50',) vs predicted ('99.50',); `line_items[1].quantity` gold ('5',) vs predicted ('19.90',); `line_items[1].unit` gold ('pack',) vs predicted ('box',); and 3 more
- **ood-13** (schema-invalid): `quote_number` gold ('FGC-P-118',) vs predicted not_stated; `date` gold ('2026-11-05',) vs predicted not_stated; `subtotal` gold ('2639.00',) vs predicted not_stated; `validity` gold ('P30D',) vs predicted not_stated; `payment_terms` gold ('invoices are payable on the 20th of the month following',) vs predicted not_stated
- **ood-14**: `quote_number` gold ('KK-3020',) vs predicted ('Quote KK-3020',); `payment_terms` gold ('payment on the 20th of the following month',) vs predicted not_stated; `gst.treatment` gold inclusive vs predicted exclusive; `line_items[0].unit` gold not_stated vs predicted ('each',); `line_items[1].unit` gold not_stated vs predicted ('each',); `line_items[2].unit` gold not_stated vs predicted ('lot',)
- **ood-15** (schema-invalid): `quote_number` gold ('TTS-6602',) vs predicted ('QUOTE TTS-6602',); `payment_terms` gold ('booking confirmed on payment',) vs predicted not_stated; `line_items[0].unit` gold not_stated vs predicted ('person',); `line_items[1].unit` gold not_stated vs predicted ('person',); `discounts[0].description` gold ('10% group discount',) vs predicted ('Less 10% group discount',)
- **ood-16**: `date` gold ('2026-11-12',) vs predicted not_stated; `subtotal` gold ('528.00',) vs predicted not_stated; `total` gold ('607.20',) vs predicted ('528.00',); `payment_terms` gold ('payment 7 days',) vs predicted not_stated
- **ood-17** (schema-invalid): `quote_number` gold ('PS-2026-552',) vs predicted ('Quote 2026-552',); `date` gold ('2026-11-06',) vs predicted not_stated; `payment_terms` gold ('payment 50% upfront, 50% on install',) vs predicted not_stated; `line_items[0].unit` gold not_stated vs predicted ('at',); `line_items[1].unit` gold not_stated vs predicted ('each',); `line_items[2].unit` gold not_stated vs predicted ('each',)
- **ood-18** (no JSON): `supplier` gold ('Rimu Valley Auto Electrical Ltd',) vs predicted <missing>; `quote_number` gold ('RVA-0087',) vs predicted <missing>; `date` gold ('2026-11-10',) vs predicted <missing>; `currency` gold ('NZD',) vs predicted <missing>; `subtotal` gold ('2310.00',) vs predicted <missing>; `total` gold ('2656.50',) vs predicted <missing>; `validity` gold ('P14D',) vs predicted <missing>; `payment_terms` gold ('account customers 20th of month',) vs predicted <missing>; and 21 more
- **ood-19** (no JSON): `supplier` gold ('Cendana Lab Glassware Sdn. Bhd.',) vs predicted <missing>; `quote_number` gold ('CLG-SH-26-212',) vs predicted <missing>; `date` gold ('2026-11-05',) vs predicted <missing>; `currency` gold ('MYR',) vs predicted <missing>; `subtotal` gold not_stated vs predicted <missing>; `total` gold ('859.00',) vs predicted <missing>; `validity` gold ('2026-12-05',) vs predicted <missing>; `payment_terms` gold ('30 hari / 30 days',) vs predicted <missing>; and 21 more
- **ood-20** (no JSON): `supplier` gold ('Kenanga Industrial Pumps Sdn Bhd',) vs predicted <missing>; `quote_number` gold ('KIP/Q/2026/0778',) vs predicted <missing>; `date` gold ('2026-11-09',) vs predicted <missing>; `currency` gold ('MYR',) vs predicted <missing>; `subtotal` gold ('4260.00',) vs predicted <missing>; `total` gold ('4110.00',) vs predicted <missing>; `validity` gold ('P30D',) vs predicted <missing>; `payment_terms` gold ('30% with po, 70% before delivery',) vs predicted <missing>; and 19 more
- **ood-21** (no JSON): `supplier` gold ('Teratai Stationery & Packaging Enterprise',) vs predicted <missing>; `quote_number` gold ('TSP-1904',) vs predicted <missing>; `date` gold ('2026-11-11',) vs predicted <missing>; `currency` gold ('MYR',) vs predicted <missing>; `subtotal` gold not_stated vs predicted <missing>; `total` gold ('685.00',) vs predicted <missing>; `validity` gold ('P7D',) vs predicted <missing>; `payment_terms` gold ('cash or cheque upon delivery',) vs predicted <missing>; and 15 more
- **ood-22**: `quote_number` gold ('MSS-PQ-0093',) vs predicted not_stated; `payment_terms` gold ('irrevocable l/c at sight',) vs predicted not_stated
- **ood-23**: `supplier` gold ('Seri Pandan Food Ingredients Sdn Bhd',) vs predicted ('PRICE CONFIRMATION',); `quote_number` gold ('SPF-PC-4410',) vs predicted not_stated; `payment_terms` gold ('payment 14 days from delivery',) vs predicted not_stated
- **ood-24** (schema-invalid): `quote_number` gold ('RSR/26/115',) vs predicted ('SRR/26/115',); `date` gold ('2026-11-10',) vs predicted not_stated; `currency` gold ('MYR',) vs predicted not_stated; `validity` gold ('P10D',) vs predicted ('P4W',); `payment_terms` gold ('payment in advance',) vs predicted not_stated
- **ood-25** (no JSON): `supplier` gold ('Bayou Bend Office Tech LLC',) vs predicted <missing>; `quote_number` gold ('BB-104417',) vs predicted <missing>; `date` gold ('2026-11-04',) vs predicted <missing>; `currency` gold ('USD',) vs predicted <missing>; `subtotal` gold ('1768.92',) vs predicted <missing>; `total` gold ('1768.92',) vs predicted <missing>; `validity` gold ('2026-12-04',) vs predicted <missing>; `payment_terms` gold ('net 30 for approved accounts',) vs predicted <missing>; and 21 more
- **ood-26** (no JSON): `supplier` gold ('Prairie Lark Fastener Supply Inc.',) vs predicted <missing>; `quote_number` gold ('PLF-77-2091',) vs predicted <missing>; `date` gold ('2026-11-09',) vs predicted <missing>; `currency` gold ('USD',) vs predicted <missing>; `subtotal` gold not_stated vs predicted <missing>; `total` gold ('316.50',) vs predicted <missing>; `validity` gold ('P30D',) vs predicted <missing>; `payment_terms` gold ('net 30',) vs predicted <missing>; and 21 more
- **ood-27**: `subtotal` gold ('6420.00',) vs predicted not_stated; `validity` gold ('P45D',) vs predicted not_stated; `payment_terms` gold ('progress billing, net 15',) vs predicted not_stated; `discounts[0].amount` gold ('481.50',) vs predicted not_stated
- **ood-28**: `quote_number` gold ('CHM-Q-56012',) vs predicted ('Quotation CHM-Q-56012',); `date` gold ('2026-11-10',) vs predicted not_stated
- **ood-29**: `date` gold ('2026-11-06',) vs predicted not_stated; `payment_terms` gold ('monthly in advance, net 15',) vs predicted not_stated; `line_items[0].quantity` gold ('1',) vs predicted not_stated; `line_items[0].unit_price` gold ('1200.00',) vs predicted not_stated
- **ood-30**: `quote_number` gold ('RSF-EXP-0442',) vs predicted ('EXPORT QUOTE RSF-EXP-0442',); `date` gold ('2026-11-12',) vs predicted not_stated; `payment_terms` gold ('wire transfer in advance',) vs predicted not_stated
