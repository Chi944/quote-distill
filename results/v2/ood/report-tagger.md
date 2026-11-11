# tagger student

Documents: 30

| Measure | Result |
|---|---|
| Parsed as JSON | 30/30 (100.0%) |
| Schema-valid | 30/30 (100.0%) |
| Critical fields exact | 216/270 (80.0%) |
| Line items: precision / recall / F1 | 56/91 (61.5%) / 56/75 (74.7%) / 0.675 |
| Document discounts: precision / recall / F1 | 3/17 (17.6%) / 3/6 (50.0%) / 0.261 |
| Invented values (gold not_stated, predicted stated) | 6/156 (3.8%) |
| Omitted values (gold stated, predicted not_stated) | 90 |
| Arithmetic agrees with gold | 24/30 (80.0%) |
| Arithmetic internally consistent | 24/30 (80.0%) |
| Whole document exact | 1/30 (3.3%) |

| Field | Exact |
|---|---|
| supplier | 27/30 (90.0%) |
| quote_number | 15/30 (50.0%) |
| date | 30/30 (100.0%) |
| currency | 16/30 (53.3%) |
| subtotal | 23/30 (76.7%) |
| total | 24/30 (80.0%) |
| validity | 24/30 (80.0%) |
| payment_terms | 4/30 (13.3%) |
| gst.treatment | 26/30 (86.7%) |
| gst.rate | 27/30 (90.0%) |
| gst.amount | 28/30 (93.3%) |
| line.description (by position) | 59/91 (64.8%) |
| line.quantity (by position) | 56/91 (61.5%) |
| line.unit (by position) | 64/91 (70.3%) |
| line.unit_price (by position) | 61/91 (67.0%) |
| line.discount (by position) | 74/91 (81.3%) |
| line.line_total (by position) | 57/91 (62.6%) |

## Failing documents (29/30)

- **ood-01**: `quote_number` gold ('NVT/AV/2611-07',) vs predicted ('NV',); `payment_terms` gold ('50% deposit, balance on installation',) vs predicted ('balance',); `gst.amount` gold ('119.12',) vs predicted not_stated; `line_items[0].description` gold ('65-inch interactive display',) vs predicted ('-',); `line_items[0].quantity` gold ('3',) vs predicted not_stated; `line_items[0].unit` gold ('each',) vs predicted not_stated; `line_items[0].unit_price` gold ('412.50',) vs predicted not_stated; `line_items[0].line_total` gold ('1237.50',) vs predicted not_stated; and 31 more
- **ood-03**: `quote_number` gold ('MCS-Q-0918',) vs predicted ('-Q-0918',); `payment_terms` gold ('payment within 7 days of delivery',) vs predicted ('payment',)
- **ood-04**: `subtotal` gold ('3260.00',) vs predicted not_stated; `gst.amount` gold ('293.40',) vs predicted ('293.00',); `line_items[0].line_total` gold ('2500.00',) vs predicted ('40.00',)
- **ood-05**: `supplier` gold ('Greenhook Garden Centre',) vs predicted ('can',); `payment_terms` gold ('cash on delivery',) vs predicted not_stated; `line_items[0].description` gold ('terracotta pot 20cm',) vs predicted ('x terracotta pot 20cm',); `line_items[1].description` gold ('seedling tray',) vs predicted ('x seedling tray',); `line_items[2].description` gold ('potting mix 25L bag',) vs predicted ('x potting mix 25L bag',); `line_items[3].description` gold <missing> vs predicted ('deliver sat. payment cash on delivery',); `line_items[3].quantity` gold <missing> vs predicted not_stated; `line_items[3].unit` gold <missing> vs predicted not_stated; and 3 more
- **ood-06**: `currency` gold ('SGD',) vs predicted not_stated; `payment_terms` gold ('100% within 30 days of installation',) vs predicted ('within',); `line_items[0].line_total` gold ('2980.00',) vs predicted not_stated; `discounts[0].amount` gold ('200.00',) vs predicted ('-200.00',)
- **ood-07**: `quote_number` gold ('SEH-4471',) vs predicted not_stated; `currency` gold ('AUD',) vs predicted not_stated; `subtotal` gold ('1739.00',) vs predicted not_stated; `total` gold ('1912.90',) vs predicted ('1739.00',); `payment_terms` gold ('a 20% deposit confirms the booking; the balance is due 7 days before the event',) vs predicted not_stated; `gst.rate` gold not_stated vs predicted ('20',); `line_items[0].description` gold ('Supply and erect 6x12 m marquee',) vs predicted ('Marquee hire',); `line_items[0].quantity` gold ('2',) vs predicted not_stated; and 33 more
- **ood-08**: `currency` gold ('AUD',) vs predicted not_stated
- **ood-09**: `quote_number` gold ('WRS-0451',) vs predicted ('RS',); `validity` gold ('P45D',) vs predicted ('P14D',); `payment_terms` gold ('payment 14 days',) vs predicted not_stated; `gst.treatment` gold inclusive vs predicted exclusive; `line_items[0].description` gold ('Battery inverter 5 kW',) vs predicted ('Battery inverter 5 kW*',)
- **ood-10**: `quote_number` gold ('TT-77310',) vs predicted ('77',); `currency` gold ('AUD',) vs predicted not_stated; `payment_terms` gold ('30 days; 2% off if paid within 7 days',) vs predicted ('30 days',); `line_items[0].quantity` gold ('40',) vs predicted ('0',); `line_items[0].line_total` gold ('496.00',) vs predicted not_stated; `line_items[1].quantity` gold ('40',) vs predicted ('0',); `line_items[1].line_total` gold ('158.00',) vs predicted not_stated; `line_items[2].quantity` gold ('2',) vs predicted ('0',); and 2 more
- **ood-11**: `payment_terms` gold ('payment by telegraphic transfer before shipment',) vs predicted ('by',); `gst.treatment` gold not_charged vs predicted not_stated; `line_items[0].unit_price` gold ('3600.00',) vs predicted ('3.00',); `line_items[2].description` gold <missing> vs predicted ('telegraphic',); `line_items[2].quantity` gold <missing> vs predicted not_stated; `line_items[2].unit` gold <missing> vs predicted not_stated; `line_items[2].unit_price` gold <missing> vs predicted not_stated; `line_items[2].discount` gold <missing> vs predicted not_stated; and 1 more
- **ood-12**: `quote_number` gold ('KCC-2210',) vs predicted ('22',); `currency` gold ('AUD',) vs predicted not_stated; `subtotal` gold ('519.00',) vs predicted not_stated; `total` gold ('570.90',) vs predicted ('519.00',); `payment_terms` gold ('eft on order',) vs predicted ('eft',); `line_items[2].quantity` gold ('1',) vs predicted ('45',); `line_items[2].unit_price` gold ('45.00',) vs predicted not_stated
- **ood-13**: `subtotal` gold ('2639.00',) vs predicted not_stated; `total` gold ('3034.85',) vs predicted ('2639.00',); `payment_terms` gold ('invoices are payable on the 20th of the month following',) vs predicted not_stated; `line_items[0].description` gold ('Stage 1 workshop facilitation',) vs predicted ('Proposal and fee quote',); `line_items[0].quantity` gold ('2',) vs predicted not_stated; `line_items[0].unit` gold ('day',) vs predicted not_stated; `line_items[0].unit_price` gold ('1125.00',) vs predicted not_stated; `line_items[0].line_total` gold ('2250.00',) vs predicted not_stated; and 15 more
- **ood-14**: `quote_number` gold ('KK-3020',) vs predicted not_stated; `currency` gold ('NZD',) vs predicted not_stated; `payment_terms` gold ('payment on the 20th of the following month',) vs predicted not_stated; `gst.treatment` gold inclusive vs predicted exclusive
- **ood-15**: `quote_number` gold ('TTS-6602',) vs predicted not_stated; `currency` gold ('NZD',) vs predicted not_stated; `validity` gold ('P30D',) vs predicted not_stated; `payment_terms` gold ('booking confirmed on payment',) vs predicted ('on payment',); `line_items[1].description` gold ('Fire warden refresher',) vs predicted ('site',); `line_items[1].quantity` gold ('8',) vs predicted not_stated; `line_items[1].unit_price` gold ('36.00',) vs predicted not_stated; `line_items[1].line_total` gold ('288.00',) vs predicted not_stated; and 13 more
- **ood-16**: `currency` gold ('NZD',) vs predicted not_stated; `subtotal` gold ('528.00',) vs predicted not_stated; `total` gold ('607.20',) vs predicted ('528.00',); `payment_terms` gold ('payment 7 days',) vs predicted not_stated; `line_items[0].description` gold ('Seedlings, flax (Phormium), 1 L pots',) vs predicted ('Seedlings, flax',); `line_items[0].quantity` gold ('120',) vs predicted not_stated; `line_items[0].unit` gold ('each',) vs predicted not_stated; `line_items[0].unit_price` gold ('2.35',) vs predicted not_stated; and 18 more
- **ood-17**: `payment_terms` gold ('payment 50% upfront, 50% on install',) vs predicted not_stated; `gst.rate` gold not_stated vs predicted ('50',); `line_items[3].description` gold <missing> vs predicted ('front',); `line_items[3].quantity` gold <missing> vs predicted not_stated; `line_items[3].unit` gold <missing> vs predicted not_stated; `line_items[3].unit_price` gold <missing> vs predicted not_stated; `line_items[3].discount` gold <missing> vs predicted not_stated; `line_items[3].line_total` gold <missing> vs predicted not_stated; and 4 more
- **ood-18**: `quote_number` gold ('RVA-0087',) vs predicted not_stated; `currency` gold ('NZD',) vs predicted not_stated; `payment_terms` gold ('account customers 20th of month',) vs predicted not_stated; `line_items[0].line_total` gold ('1860.00',) vs predicted not_stated
- **ood-19**: `supplier` gold ('Cendana Lab Glassware Sdn. Bhd.',) vs predicted ('SEBUT HARGA',); `validity` gold ('2026-12-05',) vs predicted not_stated; `payment_terms` gold ('30 hari / 30 days',) vs predicted ('30 h',)
- **ood-20**: `quote_number` gold ('KIP/Q/2026/0778',) vs predicted ('Q/2026/0778',); `subtotal` gold ('4260.00',) vs predicted not_stated; `total` gold ('4110.00',) vs predicted ('4260.00',); `validity` gold ('P30D',) vs predicted not_stated; `payment_terms` gold ('30% with po, 70% before delivery',) vs predicted (',',); `gst.rate` gold not_stated vs predicted ('30',); `line_items[0].discount` gold not_stated vs predicted ('amount', '0.00'); `discounts[1].description` gold <missing> vs predicted ('PO',); and 3 more
- **ood-21**: `currency` gold ('MYR',) vs predicted not_stated; `payment_terms` gold ('cash or cheque upon delivery',) vs predicted ('cash or',)
- **ood-22**: `quote_number` gold ('MSS-PQ-0093',) vs predicted ('MSS-',); `payment_terms` gold ('irrevocable l/c at sight',) vs predicted ('irrevocable',)
- **ood-23**: `supplier` gold ('Seri Pandan Food Ingredients Sdn Bhd',) vs predicted ('PRICE CONFIRMATION',); `payment_terms` gold ('payment 14 days from delivery',) vs predicted not_stated
- **ood-24**: `quote_number` gold ('RSR/26/115',) vs predicted ('SR/26/115',); `currency` gold ('MYR',) vs predicted not_stated; `payment_terms` gold ('payment in advance',) vs predicted ('in',)
- **ood-25**: `total` gold ('1768.92',) vs predicted not_stated; `payment_terms` gold ('net 30 for approved accounts',) vs predicted not_stated
- **ood-26**: `payment_terms` gold ('net 30',) vs predicted not_stated; `line_items[0].quantity` gold ('200',) vs predicted not_stated; `line_items[1].quantity` gold ('50',) vs predicted not_stated; `line_items[2].quantity` gold ('1',) vs predicted not_stated
- **ood-27**: `currency` gold ('USD',) vs predicted not_stated; `subtotal` gold ('6420.00',) vs predicted ('420.00',); `validity` gold ('P45D',) vs predicted not_stated; `payment_terms` gold ('progress billing, net 15',) vs predicted ('progress',); `line_items[0].description` gold ('Tear-off and re-roof, 30-yr shingle',) vs predicted ('Library annex re-roof',); `line_items[0].quantity` gold ('2',) vs predicted not_stated; `line_items[0].unit` gold ('lot',) vs predicted not_stated; `line_items[0].unit_price` gold ('2450.00',) vs predicted not_stated; and 26 more
- **ood-28**: `quote_number` gold ('CHM-Q-56012',) vs predicted ('56',); `currency` gold ('USD',) vs predicted not_stated
- **ood-29**: `quote_number` gold ('Q-2026-1187',) vs predicted ('Q-2026-11',); `payment_terms` gold ('monthly in advance, net 15',) vs predicted ('monthly in advance',)
- **ood-30**: `quote_number` gold ('RSF-EXP-0442',) vs predicted not_stated; `currency` gold ('USD',) vs predicted not_stated; `validity` gold ('P30D',) vs predicted not_stated; `payment_terms` gold ('wire transfer in advance',) vs predicted ('on',); `gst.treatment` gold not_charged vs predicted not_stated; `line_items[2].description` gold <missing> vs predicted ('Sales',); `line_items[2].quantity` gold <missing> vs predicted not_stated; `line_items[2].unit` gold <missing> vs predicted not_stated; and 15 more
