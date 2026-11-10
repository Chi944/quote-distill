# Out-of-distribution check

The [frozen test set](test-set.md) comes from the same generator as the students' training data. It has its own random streams and shares no texts with training, but the templates, wording and kinds of goods are the same. That favours the students. This check scores them on quotations the generator didn't write.

## The step and how we know it worked

**Step.** Write 30 quotations by hand in layouts and wording the generator never produces, label them, have d hand-check them, freeze them, and score both students on them, with the 5 hand-written seeds alongside.

**It worked when** every label passes the deterministic checks (`python -m quote_distill.checks data/ood`, run in CI), the hand check is recorded below and the set is frozen (`python -m quote_distill.ood verify`, run in CI once frozen), and the tables below were written by `python -m quote_distill.ood report` from predictions made by the same ONNX files the demo loads.

## The documents

[`data/ood/`](../data/ood/) holds 30 quotations, 6 per locale, written in [`data/ood/author.py`](../data/ood/author.py). The script holds each document's text and its label as the printed raw strings; it derives each value by the [schema's rules](schema.md), and the checker confirms that every raw is in the text and every total adds up. What's new compared with the generator:

- **Layouts:** a chat message, emails with prices inside sentences, key: value blocks, semicolon-separated rows, a summary box printed above the items, a receipt, a boxed table with a SKU column, a cart, a contractor's bid, bilingual Malay and English headings, rows with no column headers, and columns in a new order.
- **Wording:** "Estimate", "Proposal", "Bid", "Price confirmation" and "Sebut harga" instead of "Quotation", and "Grand total", "Nett total", "To pay" and "Base bid" for the totals.
- **Goods and services:** AV rental, printing, catering, IT services, plants, lab equipment, marquee hire, solar, roofing, software seats and more, from suppliers outside the generator's name lists.

The schema and its rules are unchanged, so there are no new kinds of fields. Two known limits are left for later: Malaysia's SST and US sales tax aren't modelled (the schema's tax field is GST), so the Malaysian and US documents here either don't mention tax or say it isn't charged; and units outside the schema's vocabulary (such as "pax" or "unit") are avoided.

The 5 hand-written seeds in [`data/seeds/`](../data/seeds/) are scored too. They are the only other documents the generator didn't write, and the teacher's pilot already answered them, so they are the one place all three models can be compared off-distribution.

## Hand check

| Date | Documents checked | Problems found | Corrections |
|---|---|---|---|
| 2026-11-10 | 30/30 | 0/30 | None |

## Running it

The students run in GitHub Actions ([`.github/workflows/ood.yml`](../.github/workflows/ood.yml), started by hand): it downloads the published models from Hugging Face, runs [`student/evaluate.py`](../src/quote_distill/student/evaluate.py) on both sets on the runner's CPU, and pushes the predictions to a `results/ood-<run>` branch for a pull request. Then:

```bash
python -m quote_distill.ood report --results results/ood
```

It refuses unless `data/ood` matches its frozen manifest. The teacher can't be re-run (the credits are gone), so its row covers the seeds only, from the pilot.

## Results

<!-- ood:start -->
Every rate is numerator/denominator; a missing or unparseable output counts as wrong in every field. Latency is onnxruntime on the scoring machine's CPU.

### Hand-written, out-of-distribution (30 documents)

| Model | Per-field exact match | Line-item F1 | Arithmetic agrees with gold | Whole document exact | Latency per doc (CPU) |
|---|---|---|---|---|---|
| Student: encoder tagger | 565/888 (63.6%) | 0.452 | 22/30 (73.3%) | 0/30 (0.0%) | 50 ms median |
| Student: generative | 450/780 (57.7%) | 0.524 | 10/30 (33.3%) | 0/30 (0.0%) | 10.7 s median |

Whole-document exact by locale:

| Locale | n | Student: encoder tagger | Student: generative |
|---|---|---|---|
| AU | 6 | 0/6 (0.0%) | 0/6 (0.0%) |
| MY | 6 | 0/6 (0.0%) | 0/6 (0.0%) |
| NZ | 6 | 0/6 (0.0%) | 0/6 (0.0%) |
| SG | 6 | 0/6 (0.0%) | 0/6 (0.0%) |
| US | 6 | 0/6 (0.0%) | 0/6 (0.0%) |

<details><summary>Student: encoder tagger: 30 of 30 documents not exact</summary>

- **ood-01**: `supplier` gold ('Novatone AV Rentals Pte. Ltd.',) vs ('refresh',); `quote_number` gold ('NVT/AV/2611-07',) vs ('NV',); `total` gold ('1442.62',) vs not_stated; `payment_terms` gold ('50% deposit, balance on installation',) vs ('% deposit',); `line_items[0].description` gold ('65-inch interactive display',) vs ('-room AV',); `line_items[0].quantity` gold ('3',) vs not_stated; and 36 more
- **ood-02**: `subtotal` gold ('701.30',) vs not_stated; `total` gold ('741.48',) vs ('30.00',); `validity` gold ('2026-11-30',) vs not_stated; `payment_terms` gold ('cash or paynow on collection',) vs ('cash',); `discounts[0].amount` gold ('21.04',) vs ('4.00',)
- **ood-03**: `line_items[0].unit_price` gold ('18.90',) vs ('18.00',); `line_items[0].discount` gold not_stated vs ('amount', '90.00'); `line_items[1].description` gold ('Insulated food carrier 20L',) vs ('Insulated food carrier 20L;',); `line_items[1].discount` gold not_stated vs ('amount', '0.00'); `line_items[2].description` gold ('Chafing dish fuel, carton',) vs ('Chafing dish fuel, carton;',); `line_items[2].discount` gold not_stated vs ('amount', '0.00')
- **ood-04**: `subtotal` gold ('3260.00',) vs not_stated; `payment_terms` gold ('30 days from invoice',) vs ('from',); `gst.treatment` gold exclusive vs inclusive; `gst.amount` gold ('293.40',) vs not_stated; `line_items[0].line_total` gold ('2500.00',) vs not_stated
- **ood-05**: `supplier` gold ('Greenhook Garden Centre',) vs ('Green',); `payment_terms` gold ('cash on delivery',) vs ('on',); `line_items[0].description` gold ('terracotta pot 20cm',) vs ('x terracotta pot 20cm',); `line_items[1].description` gold ('seedling tray',) vs ('x',); `line_items[1].unit_price` gold ('1.15',) vs not_stated; `line_items[1].line_total` gold ('46.00',) vs not_stated; and 16 more
- **ood-06**: `payment_terms` gold ('100% within 30 days of installation',) vs ('-',); `gst.treatment` gold exclusive vs not_stated; `line_items[0].unit_price` gold ('2980.00',) vs not_stated; `line_items[0].line_total` gold ('2980.00',) vs not_stated
- **ood-07**: `quote_number` gold ('SEH-4471',) vs ('SE',); `currency` gold ('AUD',) vs not_stated; `subtotal` gold ('1739.00',) vs not_stated; `total` gold ('1912.90',) vs ('1739.00',); `validity` gold ('P30D',) vs not_stated; `payment_terms` gold ('a 20% deposit confirms the booking; the balance is due 7 days before the event',) vs ('quote',); and 21 more
- **ood-08**: `currency` gold ('AUD',) vs not_stated
- **ood-09**: `validity` gold ('P45D',) vs not_stated; `payment_terms` gold ('payment 14 days',) vs not_stated; `line_items[0].description` gold ('Battery inverter 5 kW',) vs ('Battery inverter 5 kW*',); `line_items[0].quantity` gold ('3',) vs not_stated; `line_items[0].unit_price` gold ('219.00',) vs not_stated; `line_items[0].line_total` gold ('657.00',) vs not_stated; and 23 more
- **ood-10**: `currency` gold ('AUD',) vs not_stated; `line_items[0].quantity` gold ('40',) vs ('496',); `line_items[0].line_total` gold ('496.00',) vs not_stated; `line_items[1].quantity` gold ('40',) vs ('158',); `line_items[1].line_total` gold ('158.00',) vs not_stated; `line_items[2].quantity` gold ('2',) vs ('370',); and 5 more
- **ood-11**: `supplier` gold ('BLUEWREN MARINE ELECTRONICS PTY LTD',) vs ('BLUEWREN MARINE ELECTRONICS PTY LTD — EXPORT QUOTATION',); `quote_number` gold ('BME-EX-2026-019',) vs ('B',); `payment_terms` gold ('payment by telegraphic transfer before shipment',) vs ('payment',); `line_items[2].description` gold <missing> vs ('ic',); `line_items[2].quantity` gold <missing> vs not_stated; `line_items[2].unit` gold <missing> vs not_stated; and 3 more
- **ood-12**: `currency` gold ('AUD',) vs not_stated; `subtotal` gold ('519.00',) vs not_stated; `total` gold ('570.90',) vs ('0.00',); `payment_terms` gold ('eft on order',) vs not_stated; `gst.treatment` gold exclusive vs not_stated; `gst.amount` gold ('51.90',) vs ('519.00',); and 8 more
- **ood-13**: `subtotal` gold ('2639.00',) vs not_stated; `payment_terms` gold ('invoices are payable on the 20th of the month following',) vs ('invoices',); `line_items[0].description` gold ('Stage 1 workshop facilitation',) vs ('Proposal and fee quote —',); `line_items[0].quantity` gold ('2',) vs not_stated; `line_items[0].unit` gold ('day',) vs not_stated; `line_items[0].unit_price` gold ('1125.00',) vs not_stated; and 16 more
- **ood-14**: `quote_number` gold ('KK-3020',) vs ('KK',); `currency` gold ('NZD',) vs not_stated; `payment_terms` gold ('payment on the 20th of the following month',) vs ('on',); `gst.treatment` gold inclusive vs not_charged; `line_items[0].quantity` gold ('30',) vs not_stated; `line_items[0].unit_price` gold ('22.50',) vs ('30.00',); and 3 more
- **ood-15**: `currency` gold ('NZD',) vs not_stated; `validity` gold ('P30D',) vs not_stated; `payment_terms` gold ('booking confirmed on payment',) vs ('on payment;',); `line_items[1].description` gold ('Fire warden refresher',) vs ('site',); `line_items[1].quantity` gold ('8',) vs not_stated; `line_items[1].unit_price` gold ('36.00',) vs not_stated; and 8 more
- **ood-16**: `currency` gold ('NZD',) vs not_stated; `subtotal` gold ('528.00',) vs not_stated; `total` gold ('607.20',) vs ('528.00',); `payment_terms` gold ('payment 7 days',) vs ('tax',); `gst.treatment` gold exclusive vs not_stated
- **ood-17**: `supplier` gold ('Pohutukawa Signs Limited',) vs ('s',); `payment_terms` gold ('payment 50% upfront, 50% on install',) vs ('on install',); `gst.treatment` gold not_stated vs not_charged; `gst.rate` gold not_stated vs ('50',); `line_items[2].unit_price` gold ('64.50',) vs ('64.00',)
- **ood-18**: `quote_number` gold ('RVA-0087',) vs ('00',); `currency` gold ('NZD',) vs not_stated; `payment_terms` gold ('account customers 20th of month',) vs ('customers 20th of month',); `line_items[0].line_total` gold ('1860.00',) vs not_stated; `line_items[1].description` gold ('Labour',) vs ('our',)
- **ood-19**: `supplier` gold ('Cendana Lab Glassware Sdn. Bhd.',) vs ('SEBUT HARGA',); `validity` gold ('2026-12-05',) vs not_stated; `payment_terms` gold ('30 hari / 30 days',) vs ('30',)
- **ood-20**: `subtotal` gold ('4260.00',) vs not_stated; `total` gold ('4110.00',) vs ('4260.00',); `validity` gold ('P30D',) vs not_stated; `payment_terms` gold ('30% with po, 70% before delivery',) vs ('ivery',); `gst.rate` gold not_stated vs ('30',); `line_items[2].description` gold <missing> vs ('Del',); and 11 more
- **ood-21**: `currency` gold ('MYR',) vs not_stated; `payment_terms` gold ('cash or cheque upon delivery',) vs ('cash',); `line_items[0].unit_price` gold ('7.60',) vs not_stated; `line_items[1].unit_price` gold ('15.25',) vs ('25.00',)
- **ood-22**: `payment_terms` gold ('irrevocable l/c at sight',) vs ('irrevocable l/c at',)
- **ood-23**: `supplier` gold ('Seri Pandan Food Ingredients Sdn Bhd',) vs ('PRICE CONFIRMATION',); `payment_terms` gold ('payment 14 days from delivery',) vs ('payment',); `line_items[0].description` gold ('Coconut milk, UHT 1 litre carton',) vs ('Ing',); `line_items[0].quantity` gold ('24',) vs not_stated; `line_items[0].unit` gold ('l',) vs not_stated; `line_items[0].unit_price` gold ('11.75',) vs not_stated; and 12 more
- **ood-24**: `currency` gold ('MYR',) vs not_stated; `validity` gold ('P10D',) vs not_stated; `payment_terms` gold ('payment in advance',) vs not_stated; `line_items[0].discount` gold not_stated vs ('amount', '0.00')
- **ood-25**: `supplier` gold ('Bayou Bend Office Tech LLC',) vs ('Bayou Bend Office Tech LLC —',); `subtotal` gold ('1768.92',) vs not_stated; `validity` gold ('2026-12-04',) vs not_stated; `payment_terms` gold ('net 30 for approved accounts',) vs not_stated; `line_items[0].quantity` gold ('4',) vs not_stated; `line_items[0].discount` gold not_stated vs ('amount', '4.00'); and 8 more
- **ood-26**: `payment_terms` gold ('net 30',) vs not_stated; `line_items[0].quantity` gold ('200',) vs not_stated; `line_items[0].unit` gold ('each',) vs not_stated; `line_items[1].quantity` gold ('50',) vs not_stated; `line_items[1].unit` gold ('box',) vs not_stated; `line_items[2].quantity` gold ('1',) vs not_stated; and 1 more
- **ood-27**: `currency` gold ('USD',) vs not_stated; `subtotal` gold ('6420.00',) vs not_stated; `validity` gold ('P45D',) vs not_stated; `payment_terms` gold ('progress billing, net 15',) vs ('if not',); `line_items[0].description` gold ('Tear-off and re-roof, 30-yr shingle',) vs ('annex',); `line_items[0].quantity` gold ('2',) vs not_stated; and 26 more
- **ood-28**: `quote_number` gold ('CHM-Q-56012',) vs ('CHM-Q-56',); `validity` gold ('2026-12-10',) vs not_stated
- **ood-29**: `quote_number` gold ('Q-2026-1187',) vs ('Q-2026-11',); `currency` gold ('USD',) vs not_stated; `payment_terms` gold ('monthly in advance, net 15',) vs ('illing',); `line_items[0].discount` gold not_stated vs ('amount', '0.00'); `line_items[1].discount` gold not_stated vs ('amount', '0.00'); `line_items[2].discount` gold not_stated vs ('amount', '0.00')
- **ood-30**: `quote_number` gold ('RSF-EXP-0442',) vs ('-',); `currency` gold ('USD',) vs not_stated; `payment_terms` gold ('wire transfer in advance',) vs ('charged on export',); `gst.treatment` gold not_charged vs not_stated; `discounts[0].description` gold <missing> vs ('tax',); `discounts[0].kind` gold <missing> vs amount; and 2 more

</details>

<details><summary>Student: generative: 30 of 30 documents not exact</summary>

- **ood-01** (no output): `supplier` gold ('Novatone AV Rentals Pte. Ltd.',) vs <missing>; `quote_number` gold ('NVT/AV/2611-07',) vs <missing>; `date` gold ('2026-11-03',) vs <missing>; `currency` gold ('SGD',) vs <missing>; `subtotal` gold ('1323.50',) vs <missing>; `total` gold ('1442.62',) vs <missing>; and 17 more
- **ood-02**: `date` gold ('2026-11-09',) vs not_stated; `subtotal` gold ('701.30',) vs not_stated; `total` gold ('741.48',) vs ('701.30',); `discounts[0].description` gold ('Loyalty discount 3%',) vs ('Loyalty discount',); `discounts[0].kind` gold percent vs amount
- **ood-03**: `payment_terms` gold ('payment within 7 days of delivery',) vs not_stated; `line_items[1].description` gold ('Insulated food carrier 20L',) vs ('Insulated food carrier 20L;6 each',); `line_items[1].quantity` gold ('6',) vs ('1',); `line_items[1].unit` gold ('each',) vs ('box',)
- **ood-04**: `quote_number` gold ('CLD-2026-1144',) vs not_stated; `subtotal` gold ('3260.00',) vs not_stated; `gst.rate` gold ('9',) vs not_stated
- **ood-05** (no output): `supplier` gold ('Greenhook Garden Centre',) vs <missing>; `quote_number` gold not_stated vs <missing>; `date` gold not_stated vs <missing>; `currency` gold not_stated vs <missing>; `subtotal` gold not_stated vs <missing>; `total` gold ('271.00',) vs <missing>; and 23 more
- **ood-06**: `payment_terms` gold ('100% within 30 days of installation',) vs not_stated; `line_items[2].quantity` gold ('1',) vs not_stated; `line_items[2].unit_price` gold ('320.00',) vs not_stated; `discounts[0].description` gold ('Special discount',) vs ('Special discount -200.00',)
- **ood-07** (schema-invalid): `quote_number` gold ('SEH-4471',) vs not_stated; `subtotal` gold ('1739.00',) vs not_stated; `total` gold ('1912.90',) vs ('1739.00',); `payment_terms` gold ('a 20% deposit confirms the booking; the balance is due 7 days before the event',) vs not_stated; `line_items[0].description` gold ('Supply and erect 6x12 m marquee',) vs ('Marquee hire, Spring Fair',); `line_items[2].line_total` gold ('95.00',) vs ('95.00.00',)
- **ood-08**: `payment_terms` gold ('cod',) vs not_stated
- **ood-09**: `payment_terms` gold ('payment 14 days',) vs not_stated; `gst.treatment` gold inclusive vs exclusive; `line_items[0].unit` gold not_stated vs ('month',); `line_items[1].quantity` gold ('1',) vs not_stated; `line_items[1].unit` gold not_stated vs ('lot',); `line_items[1].unit_price` gold ('1480.00',) vs not_stated
- **ood-10** (no output): `supplier` gold ('Tea Tree Office Furniture Pty Ltd',) vs <missing>; `quote_number` gold ('TT-77310',) vs <missing>; `date` gold ('2026-11-03',) vs <missing>; `currency` gold ('AUD',) vs <missing>; `subtotal` gold ('1024.00',) vs <missing>; `total` gold ('1070.08',) vs <missing>; and 27 more
- **ood-11**: `supplier` gold ('BLUEWREN MARINE ELECTRONICS PTY LTD',) vs ('BLUEWREN MARINE ELECTRONICS PTY LTD — EXPORT QUOTATION',); `payment_terms` gold ('payment by telegraphic transfer before shipment',) vs not_stated; `gst.treatment` gold not_charged vs not_stated
- **ood-12** (schema-invalid): `quote_number` gold ('KCC-2210',) vs ('QUOTE KCC-2210',); `date` gold ('2026-11-01',) vs not_stated; `payment_terms` gold ('eft on order',) vs not_stated; `line_items[0].quantity` gold ('5',) vs ('74.90',); `line_items[0].unit_price` gold ('74.90',) vs ('374.50',); `line_items[0].line_total` gold ('374.50',) vs ('99.50',); and 5 more
- **ood-13** (schema-invalid): `quote_number` gold ('FGC-P-118',) vs not_stated; `date` gold ('2026-11-05',) vs not_stated; `subtotal` gold ('2639.00',) vs not_stated; `validity` gold ('P30D',) vs not_stated; `payment_terms` gold ('invoices are payable on the 20th of the month following',) vs not_stated
- **ood-14**: `quote_number` gold ('KK-3020',) vs ('Quote KK-3020',); `payment_terms` gold ('payment on the 20th of the following month',) vs not_stated; `gst.treatment` gold inclusive vs exclusive; `line_items[0].unit` gold not_stated vs ('each',); `line_items[1].unit` gold not_stated vs ('each',); `line_items[2].unit` gold not_stated vs ('lot',)
- **ood-15** (schema-invalid): `quote_number` gold ('TTS-6602',) vs ('QUOTE TTS-6602',); `payment_terms` gold ('booking confirmed on payment',) vs not_stated; `line_items[0].unit` gold not_stated vs ('person',); `line_items[1].unit` gold not_stated vs ('person',); `discounts[0].description` gold ('10% group discount',) vs ('Less 10% group discount',)
- **ood-16**: `date` gold ('2026-11-12',) vs not_stated; `subtotal` gold ('528.00',) vs not_stated; `total` gold ('607.20',) vs ('528.00',); `payment_terms` gold ('payment 7 days',) vs not_stated
- **ood-17** (schema-invalid): `quote_number` gold ('PS-2026-552',) vs ('Quote 2026-552',); `date` gold ('2026-11-06',) vs not_stated; `payment_terms` gold ('payment 50% upfront, 50% on install',) vs not_stated; `line_items[0].unit` gold not_stated vs ('at',); `line_items[1].unit` gold not_stated vs ('each',); `line_items[2].unit` gold not_stated vs ('each',)
- **ood-18** (no output): `supplier` gold ('Rimu Valley Auto Electrical Ltd',) vs <missing>; `quote_number` gold ('RVA-0087',) vs <missing>; `date` gold ('2026-11-10',) vs <missing>; `currency` gold ('NZD',) vs <missing>; `subtotal` gold ('2310.00',) vs <missing>; `total` gold ('2656.50',) vs <missing>; and 23 more
- **ood-19** (no output): `supplier` gold ('Cendana Lab Glassware Sdn. Bhd.',) vs <missing>; `quote_number` gold ('CLG-SH-26-212',) vs <missing>; `date` gold ('2026-11-05',) vs <missing>; `currency` gold ('MYR',) vs <missing>; `subtotal` gold not_stated vs <missing>; `total` gold ('859.00',) vs <missing>; and 23 more
- **ood-20** (no output): `supplier` gold ('Kenanga Industrial Pumps Sdn Bhd',) vs <missing>; `quote_number` gold ('KIP/Q/2026/0778',) vs <missing>; `date` gold ('2026-11-09',) vs <missing>; `currency` gold ('MYR',) vs <missing>; `subtotal` gold ('4260.00',) vs <missing>; `total` gold ('4110.00',) vs <missing>; and 21 more
- **ood-21** (no output): `supplier` gold ('Teratai Stationery & Packaging Enterprise',) vs <missing>; `quote_number` gold ('TSP-1904',) vs <missing>; `date` gold ('2026-11-11',) vs <missing>; `currency` gold ('MYR',) vs <missing>; `subtotal` gold not_stated vs <missing>; `total` gold ('685.00',) vs <missing>; and 17 more
- **ood-22**: `quote_number` gold ('MSS-PQ-0093',) vs not_stated; `payment_terms` gold ('irrevocable l/c at sight',) vs not_stated
- **ood-23**: `supplier` gold ('Seri Pandan Food Ingredients Sdn Bhd',) vs ('PRICE CONFIRMATION',); `quote_number` gold ('SPF-PC-4410',) vs not_stated; `payment_terms` gold ('payment 14 days from delivery',) vs not_stated
- **ood-24** (schema-invalid): `quote_number` gold ('RSR/26/115',) vs ('SRR/26/115',); `date` gold ('2026-11-10',) vs not_stated; `currency` gold ('MYR',) vs not_stated; `validity` gold ('P10D',) vs ('P4W',); `payment_terms` gold ('payment in advance',) vs not_stated
- **ood-25** (no output): `supplier` gold ('Bayou Bend Office Tech LLC',) vs <missing>; `quote_number` gold ('BB-104417',) vs <missing>; `date` gold ('2026-11-04',) vs <missing>; `currency` gold ('USD',) vs <missing>; `subtotal` gold ('1768.92',) vs <missing>; `total` gold ('1768.92',) vs <missing>; and 23 more
- **ood-26** (no output): `supplier` gold ('Prairie Lark Fastener Supply Inc.',) vs <missing>; `quote_number` gold ('PLF-77-2091',) vs <missing>; `date` gold ('2026-11-09',) vs <missing>; `currency` gold ('USD',) vs <missing>; `subtotal` gold not_stated vs <missing>; `total` gold ('316.50',) vs <missing>; and 23 more
- **ood-27**: `subtotal` gold ('6420.00',) vs not_stated; `validity` gold ('P45D',) vs not_stated; `payment_terms` gold ('progress billing, net 15',) vs not_stated; `discounts[0].amount` gold ('481.50',) vs not_stated
- **ood-28**: `quote_number` gold ('CHM-Q-56012',) vs ('Quotation CHM-Q-56012',); `date` gold ('2026-11-10',) vs not_stated
- **ood-29**: `date` gold ('2026-11-06',) vs not_stated; `payment_terms` gold ('monthly in advance, net 15',) vs not_stated; `line_items[0].quantity` gold ('1',) vs not_stated; `line_items[0].unit_price` gold ('1200.00',) vs not_stated
- **ood-30**: `quote_number` gold ('RSF-EXP-0442',) vs ('EXPORT QUOTE RSF-EXP-0442',); `date` gold ('2026-11-12',) vs not_stated; `payment_terms` gold ('wire transfer in advance',) vs not_stated

</details>

### Hand-written seeds (5 documents)

| Model | Per-field exact match | Line-item F1 | Arithmetic agrees with gold | Whole document exact | Latency per doc (CPU) |
|---|---|---|---|---|---|
| Teacher: Claude Haiku (pilot run) | 156/157 (99.4%) | 1.000 | 5/5 (100.0%) | 3/5 (60.0%) | not measured |
| Student: encoder tagger | 108/193 (56.0%) | 0.800 | 4/5 (80.0%) | 1/5 (20.0%) | 58 ms median |
| Student: generative | 80/157 (51.0%) | 0.615 | 2/5 (40.0%) | 1/5 (20.0%) | 14.9 s median |

Whole-document exact by locale:

| Locale | n | Teacher: Claude Haiku (pilot run) | Student: encoder tagger | Student: generative |
|---|---|---|---|---|
| AU | 1 | 1/1 (100.0%) | 0/1 (0.0%) | 1/1 (100.0%) |
| MY | 1 | 1/1 (100.0%) | 0/1 (0.0%) | 0/1 (0.0%) |
| NZ | 1 | 0/1 (0.0%) | 0/1 (0.0%) | 0/1 (0.0%) |
| SG | 1 | 0/1 (0.0%) | 0/1 (0.0%) | 0/1 (0.0%) |
| US | 1 | 1/1 (100.0%) | 1/1 (100.0%) | 0/1 (0.0%) |

<details><summary>Teacher: Claude Haiku (pilot run): 2 of 5 documents not exact</summary>

- **seed-01**: `discounts[0].description` gold ('5% project disount',) vs ('Less 5% project disount',)
- **seed-05**: `payment_terms` gold ('the 20th of the month following, and you can take 2.5% off if paid within 7 days of invoice',) vs ('account terms are the 20th of the month following, and you can take 2.5% off if paid within 7 days of invoice',)

</details>

<details><summary>Student: encoder tagger: 4 of 5 documents not exact</summary>

- **seed-01**: `quote_number` gold ('KLH-Q-26-0417',) vs ('M9-0000417-X',); `validity` gold ('P14D',) vs not_stated; `payment_terms` gold ('net 30 days',) vs ('from',); `line_items[0].description` gold ('Cordless drill 18V, 2 batteries',) vs (')',); `line_items[0].quantity` gold ('2',) vs not_stated; `line_items[0].unit` gold ('each',) vs not_stated; and 19 more
- **seed-02**: `gst.treatment` gold exclusive vs not_charged
- **seed-03**: `payment_terms` gold not_stated vs ('stock',); `line_items[0].description` gold ('Galvinised pipe 25mm x 6m',) vs ('fittings',); `line_items[0].quantity` gold ('40',) vs not_stated; `line_items[0].unit` gold ('length',) vs not_stated; `line_items[0].unit_price` gold ('38.50',) vs not_stated; `line_items[0].line_total` gold ('1540.00',) vs not_stated; and 17 more
- **seed-05**: `quote_number` gold not_stated vs ('09',); `date` gold ('2026-10-20',) vs not_stated; `validity` gold ('2026-10-31',) vs not_stated; `payment_terms` gold ('the 20th of the month following, and you can take 2.5% off if paid within 7 days of invoice',) vs ('account',); `line_items[0].description` gold ('H3.2 treated pine 90x45 in 4.8m lengths',) vs ('ing',); `line_items[0].quantity` gold ('24',) vs not_stated; and 31 more

</details>

<details><summary>Student: generative: 4 of 5 documents not exact</summary>

- **seed-01** (no output): `supplier` gold ('KESTREL LANE HARDWARE PTE. LTD.',) vs <missing>; `quote_number` gold ('KLH-Q-26-0417',) vs <missing>; `date` gold ('2026-10-18',) vs <missing>; `currency` gold ('SGD',) vs <missing>; `subtotal` gold ('494.90',) vs <missing>; `total` gold ('470.15',) vs <missing>; and 27 more
- **seed-03**: `supplier` gold ('Sri Kenanga Trading',) vs ('Lim W.K.',); `subtotal` gold not_stated vs ('1669.00',); `total` gold ('1669.00',) vs not_stated
- **seed-04** (no output): `supplier` gold ('HARROWGATE INSTRUMENTS INC.',) vs <missing>; `quote_number` gold ('HI-26-1015-B',) vs <missing>; `date` gold ('2026-10-15',) vs <missing>; `currency` gold ('USD',) vs <missing>; `subtotal` gold ('609.00',) vs <missing>; `total` gold ('609.00',) vs <missing>; and 35 more
- **seed-05** (schema-invalid): `payment_terms` gold ('the 20th of the month following, and you can take 2.5% off if paid within 7 days of invoice',) vs ('20th of the month following',); `gst.treatment` gold exclusive vs not_stated; `line_items[1].description` gold ('decking screws',) vs ('Decking screws, three boxes (200 per box) at 14.90 a box',); `line_items[1].quantity` gold ('3',) vs ('44.70',)

</details>
<!-- ood:end -->

## What it shows

Scored 2026-11-10 by run [42787629414](https://github.com/Chi944/quote-distill/actions/runs/42787629414), using the same ONNX files the demo loads.

- **Both students fail off the generator's layouts.** Neither gets a single one of the 30 documents fully right (0/30 each), against 299/300 and 278/300 on the in-distribution test set. Per-field exact match falls to 565/888 (63.6%) for the tagger and 450/780 (57.7%) for the generative model.
- **The tagger keeps the header and loses the rows.** It finds the date in 30/30 and the total in 24/30, but line-item F1 is 0.452 (38 of 75 gold lines found exactly) and it leaves 101 stated values as not stated. Payment terms are right in only 4/30, because the new wordings don't look like the generator's.
- **The generative model breaks its output.** 21/30 outputs parse as JSON and 15/30 are schema-valid. When it does answer, it invents a value where the document has none in 11/156 cases (the tagger in 15/156).
- **Seeds agree.** On the 5 hand-written seeds the teacher gets 156/157 fields (99.4%) and 3/5 documents, the tagger 1/5 and the generative model 1/5.

The in-distribution scores measure how well the students copy the generator, not how well they read quotations. The way to improve them is to train on more varied synthetic layouts and wording ([generator-v2.md](generator-v2.md)), then score on this frozen set again. Don't add these 30 documents to training, or the check stops meaning anything.
