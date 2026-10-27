# Final evaluation

The teacher and both students on the frozen 300-document [test set](test-set.md), scored by the same [`metrics.py`](../src/quote_distill/metrics.py) as the pilot. The README's results table comes from here.

## The step and how we know it worked

**Step.** Run the teacher and both students once over the 300 test documents and score them side by side.

**It worked when** every system has an output row for each of the 300 documents (an error is an empty row, scored as wrong), the test set matches its manifest, the hand check covers all 300, and the tables below and in the README were written by `python -m quote_distill.evaluation`, not by hand.

## Before it runs

- **Hand check done.** [`docs/test-set.md`](test-set.md) records all 300 documents as checked, and any corrections have been re-frozen. The command counts the table and refuses below 300.
- **Students trained.** The two notebooks' `tagger-onnx.zip` and `generative-onnx.zip` are unzipped into `demo/public/models/tagger/` and `demo/public/models/generative/`, the files the page serves ([demo.md](demo.md)).
- **Prompt frozen.** The teacher's prompt is the pilot's (`prompt_sha256` `ce5021cd37bf…`). It is not changed after looking at any test result.

## 1. Teacher

The teacher runs in a cloud session, as the pilot did ([teacher-session.md](teacher-session.md), added by PR #5; until #5 is merged it is on the `build/teacher-session` branch). Read the credit meter, then paste:

```text
Run the Quote Distill teacher evaluation. Follow docs/teacher-session.md exactly; do not change any file under src/ or docs/schema.md.

1. git checkout build/teacher-session (until PR #5 is merged, that branch has the session runner), pip install -e ".[dev]" and run: python -m quote_distill.teacher.session prepare --job test-session-haiku-1 --docs data/test/docs.jsonl --evaluation
2. For every file runs/test-session-haiku-1/tasks/<id>.txt, start one Agent subagent with model "haiku" whose prompt is the file's full contents, unchanged. Run them in parallel batches of 5. Do not read data/test labels or give the subagent anything else.
3. Save each subagent's final reply verbatim, with no edits or reformatting, to results/teacher/test-session-haiku-1/outputs/<id>.txt. If a subagent errors, save nothing for that id and say which.
4. Run: python -m quote_distill.teacher.session collect --job test-session-haiku-1. Do not run the score command or look at the scores.
5. Commit results/teacher/test-session-haiku-1/ on a new branch, push, and open a pull request.
```

Read the meter again and log the job in [`spend.md`](spend.md). The teacher's latency isn't measured: subagents run five at a time and the session doesn't time them.

## 2. Students

Both run on CPU through onnxruntime with the same model files the page loads (float32 tagger, 4-bit generative), one document at a time ([`student/evaluate.py`](../src/quote_distill/student/evaluate.py), [student-eval.md](student-eval.md)):

```bash
python -m quote_distill.student.evaluate --docs data/test/docs.jsonl --evaluation --tagger out/tagger-onnx --out results/students/tagger
python -m quote_distill.student.evaluate --docs data/test/docs.jsonl --evaluation --generative out/generative-onnx --out results/students/generative
```

Each writes `predictions-<student>.jsonl` with a `latency_ms` per document, and `summary.json`, which records the model file's SHA-256. The latency is that machine's CPU with model loading excluded. A browser runs the same files in WebAssembly, usually slower, so the number is a floor for the demo, not a measurement of it. Run on dev documents with `--limit 5` first.

## 3. Score

```bash
python -m quote_distill.evaluation \
  --teacher results/teacher/test-session-haiku-1/predictions.jsonl \
  --tagger results/students/tagger/predictions-tagger.jsonl \
  --generative results/students/generative/predictions-generative.jsonl \
  --teacher-cost-usd <the teacher job's credit draw from spend.md>
```

It refuses when the test set differs from its manifest, when the hand check is short of 300, when a file's ids aren't exactly the 300 test ids, or when the teacher job wasn't prepared with `--evaluation`. Then it writes the section below and the README table. `--draft PATH` writes the same report to PATH alone without the hand-check refusal, to check the pipeline; a draft is never quoted as a result.

After this run the test set doesn't change and the scores stand, whatever they are.

## Results

<!-- results:start -->
Scored 2026-10-23 on all 300 test documents (`docs.jsonl` SHA-256 `1b6f94b8120e`).
Every rate is numerator/denominator; a missing or unparseable output counts as wrong in every field.

### Summary

| Model | Per-field exact match | Line-item F1 | Arithmetic agrees with gold | Whole document exact | Latency per doc (CPU) | Cost per doc |
|---|---|---|---|---|---|---|
| Teacher: Claude Haiku in a Claude Code subagent | 11172/11208 (99.7%) | 0.997 | 299/300 (99.7%) | 260/300 (86.7%) | not measured | not measured |
| Student: encoder tagger (in browser) | 11208/11208 (100.0%) | 1.000 | 300/300 (100.0%) | 299/300 (99.7%) | 30 ms median | $0 (runs in the browser) |
| Student: generative (in browser) | 11066/11208 (98.7%) | 0.989 | 293/300 (97.7%) | 278/300 (92.7%) | 12.5 s median | $0 (runs in the browser) |

Per-field exact match counts every document-level field and every line-item field by position. Line-item F1 counts a line only when all six of its fields match. Latency is the median per document from the run's own timing; the students' runs are onnxruntime on a CPU, and in a browser (one CPU thread) the generative student is several times slower.

### Measures

| Measure | Teacher: Claude Haiku in a Claude Code subagent | Student: encoder tagger (in browser) | Student: generative (in browser) |
|---|---|---|---|
| Parsed | 300/300 (100.0%) | 300/300 (100.0%) | 297/300 (99.0%) |
| Schema-valid | 299/300 (99.7%) | 300/300 (100.0%) | 297/300 (99.0%) |
| Critical fields exact | 2670/2700 (98.9%) | 2700/2700 (100.0%) | 2664/2700 (98.7%) |
| Per-field exact | 11172/11208 (99.7%) | 11208/11208 (100.0%) | 11066/11208 (98.7%) |
| Line items: precision | 1314/1318 (99.7%) | 1318/1318 (100.0%) | 1298/1306 (99.4%) |
| Line items: recall | 1314/1318 (99.7%) | 1318/1318 (100.0%) | 1298/1318 (98.5%) |
| Line items: F1 | 0.997 | 1.000 | 0.989 |
| Document discounts: F1 | 0.857 | 0.987 | 0.987 |
| Invented values (gold not_stated, predicted stated) | 13/2384 (0.5%) | 0/2384 (0.0%) | 0/2384 (0.0%) |
| Omitted values (gold stated, predicted not_stated) | 16 | 1 | 4 |
| Arithmetic agrees with gold | 299/300 (99.7%) | 300/300 (100.0%) | 293/300 (97.7%) |
| Arithmetic internally consistent | 273/300 (91.0%) | 274/300 (91.3%) | 267/300 (89.0%) |
| Whole document exact | 260/300 (86.7%) | 299/300 (99.7%) | 278/300 (92.7%) |

Critical fields are `supplier`, `quote_number`, `date`, `currency`, `subtotal`, `gst.treatment`, `gst.rate`, `gst.amount`, `total`. A supplier's printed arithmetic mistake is kept in the gold label, so a model that "fixes" it fails *agrees with gold*; *internally consistent* can't reach 100% on this set.

### Per field

| Field | Teacher: Claude Haiku in a Claude Code subagent | Student: encoder tagger (in browser) | Student: generative (in browser) |
|---|---|---|---|
| `supplier` | 300/300 (100.0%) | 300/300 (100.0%) | 297/300 (99.0%) |
| `quote_number` | 300/300 (100.0%) | 300/300 (100.0%) | 297/300 (99.0%) |
| `date` | 296/300 (98.7%) | 300/300 (100.0%) | 293/300 (97.7%) |
| `currency` | 299/300 (99.7%) | 300/300 (100.0%) | 297/300 (99.0%) |
| `subtotal` | 289/300 (96.3%) | 300/300 (100.0%) | 297/300 (99.0%) |
| `total` | 297/300 (99.0%) | 300/300 (100.0%) | 297/300 (99.0%) |
| `validity` | 299/300 (99.7%) | 300/300 (100.0%) | 295/300 (98.3%) |
| `payment_terms` | 299/300 (99.7%) | 300/300 (100.0%) | 297/300 (99.0%) |
| `gst.treatment` | 299/300 (99.7%) | 300/300 (100.0%) | 293/300 (97.7%) |
| `gst.rate` | 300/300 (100.0%) | 300/300 (100.0%) | 297/300 (99.0%) |
| `gst.amount` | 290/300 (96.7%) | 300/300 (100.0%) | 296/300 (98.7%) |
| `line.description` (by position) | 1315/1318 (99.8%) | 1318/1318 (100.0%) | 1302/1318 (98.8%) |
| `line.quantity` (by position) | 1318/1318 (100.0%) | 1318/1318 (100.0%) | 1303/1318 (98.9%) |
| `line.unit` (by position) | 1317/1318 (99.9%) | 1318/1318 (100.0%) | 1298/1318 (98.5%) |
| `line.unit_price` (by position) | 1318/1318 (100.0%) | 1318/1318 (100.0%) | 1302/1318 (98.8%) |
| `line.discount` (by position) | 1318/1318 (100.0%) | 1318/1318 (100.0%) | 1303/1318 (98.9%) |
| `line.line_total` (by position) | 1318/1318 (100.0%) | 1318/1318 (100.0%) | 1302/1318 (98.8%) |

### By hard case

Whole-document exact match among the test documents with each feature.

| Documents with | n | Teacher: Claude Haiku in a Claude Code subagent | Student: encoder tagger (in browser) | Student: generative (in browser) |
|---|---|---|---|---|
| `all_lump_sum` | 15 | 13/15 (86.7%) | 15/15 (100.0%) | 13/15 (86.7%) |
| `bare_dollar` | 60 | 54/60 (90.0%) | 60/60 (100.0%) | 51/60 (85.0%) |
| `conditional_discount` | 40 | 34/40 (85.0%) | 40/40 (100.0%) | 38/40 (95.0%) |
| `customer_ref_decoy` | 162 | 137/162 (84.6%) | 162/162 (100.0%) | 148/162 (91.4%) |
| `description_typo` | 76 | 69/76 (90.8%) | 76/76 (100.0%) | 69/76 (90.8%) |
| `doc_discount` | 62 | 53/62 (85.5%) | 61/62 (98.4%) | 58/62 (93.5%) |
| `doc_discount_amount_unprinted` | 15 | 12/15 (80.0%) | 15/15 (100.0%) | 15/15 (100.0%) |
| `gst:exclusive` | 88 | 85/88 (96.6%) | 88/88 (100.0%) | 82/88 (93.2%) |
| `gst:inclusive` | 50 | 46/50 (92.0%) | 49/50 (98.0%) | 48/50 (96.0%) |
| `gst:not_charged` | 57 | 40/57 (70.2%) | 57/57 (100.0%) | 51/57 (89.5%) |
| `gst:not_stated` | 105 | 89/105 (84.8%) | 105/105 (100.0%) | 97/105 (92.4%) |
| `gst_plus_unpriced` | 22 | 21/22 (95.5%) | 22/22 (100.0%) | 18/22 (81.8%) |
| `gst_rate_unprinted` | 18 | 18/18 (100.0%) | 18/18 (100.0%) | 13/18 (72.2%) |
| `half_cent_tie` | 21 | 21/21 (100.0%) | 21/21 (100.0%) | 20/21 (95.2%) |
| `header_typos` | 83 | 66/83 (79.5%) | 83/83 (100.0%) | 76/83 (91.6%) |
| `layout:email_list` | 60 | 55/60 (91.7%) | 59/60 (98.3%) | 56/60 (93.3%) |
| `layout:fixed_table` | 60 | 54/60 (90.0%) | 60/60 (100.0%) | 55/60 (91.7%) |
| `layout:item_blocks` | 60 | 58/60 (96.7%) | 60/60 (100.0%) | 54/60 (90.0%) |
| `layout:pipe_table` | 60 | 58/60 (96.7%) | 60/60 (100.0%) | 58/60 (96.7%) |
| `layout:prose_email` | 60 | 35/60 (58.3%) | 60/60 (100.0%) | 55/60 (91.7%) |
| `line:credit` | 28 | 27/28 (96.4%) | 28/28 (100.0%) | 24/28 (85.7%) |
| `line:decimal_qty` | 104 | 95/104 (91.3%) | 104/104 (100.0%) | 94/104 (90.4%) |
| `line:foc` | 35 | 34/35 (97.1%) | 35/35 (100.0%) | 31/35 (88.6%) |
| `line:line_discount_amount` | 56 | 49/56 (87.5%) | 55/56 (98.2%) | 48/56 (85.7%) |
| `line:line_discount_percent` | 59 | 52/59 (88.1%) | 59/59 (100.0%) | 50/59 (84.7%) |
| `line:lump_sum` | 126 | 106/126 (84.1%) | 126/126 (100.0%) | 114/126 (90.5%) |
| `line:qty_in_words` | 61 | 45/61 (73.8%) | 61/61 (100.0%) | 55/61 (90.2%) |
| `line:sub_cent_price` | 26 | 25/26 (96.2%) | 25/26 (96.2%) | 22/26 (84.6%) |
| `line:supplier_error` | 26 | 21/26 (80.8%) | 26/26 (100.0%) | 23/26 (88.5%) |
| `locale:AU` | 60 | 59/60 (98.3%) | 59/60 (98.3%) | 55/60 (91.7%) |
| `locale:MY` | 60 | 41/60 (68.3%) | 60/60 (100.0%) | 55/60 (91.7%) |
| `locale:NZ` | 60 | 56/60 (93.3%) | 60/60 (100.0%) | 59/60 (98.3%) |
| `locale:SG` | 60 | 55/60 (91.7%) | 60/60 (100.0%) | 57/60 (95.0%) |
| `locale:US` | 60 | 49/60 (81.7%) | 60/60 (100.0%) | 52/60 (86.7%) |
| `missing:date` | 33 | 28/33 (84.8%) | 33/33 (100.0%) | 30/33 (90.9%) |
| `missing:payment_terms` | 58 | 51/58 (87.9%) | 58/58 (100.0%) | 53/58 (91.4%) |
| `missing:quote_number` | 39 | 32/39 (82.1%) | 38/39 (97.4%) | 36/39 (92.3%) |
| `missing:subtotal` | 49 | 41/49 (83.7%) | 49/49 (100.0%) | 44/49 (89.8%) |
| `missing:total` | 57 | 49/57 (86.0%) | 57/57 (100.0%) | 51/57 (89.5%) |
| `missing:validity` | 59 | 53/59 (89.8%) | 58/59 (98.3%) | 53/59 (89.8%) |
| `relative_validity` | 43 | 37/43 (86.0%) | 43/43 (100.0%) | 40/43 (93.0%) |
| `supplier_error` | 26 | 21/26 (80.8%) | 26/26 (100.0%) | 23/26 (88.5%) |

### Failure gallery

<details><summary>Teacher: Claude Haiku in a Claude Code subagent: 40 of 300 documents not exact</summary>

- **test-candidates-s1-000010**: `date` gold ('2026-12-09',) vs not_stated; `validity` gold ('2026-12-31',) vs not_stated
- **test-candidates-s1-000163**: `gst.amount` gold not_stated vs ('0.00',)
- **test-candidates-s1-000213**: `gst.amount` gold not_stated vs ('0.00',)
- **test-candidates-s1-000427**: `subtotal` gold ('2666.86',) vs not_stated; `line_items[0].description` gold ('A4 copy paper 80gsm, 5 reams',) vs ('A4 copy paper 80gsm',)
- **test-candidates-s1-000488**: `gst.amount` gold not_stated vs ('0.00',); `discounts[0].description` gold ('Discount 2.5%',) vs ('Discount 2.5% applies',)
- **test-candidates-s1-000514**: `date` gold ('2026-12-09',) vs not_stated
- **test-candidates-s1-000677**: `gst.amount` gold not_stated vs ('0.00',); `discounts[0].description` gold ('Less 10% project discount',) vs ('10% project discount',)
- **test-candidates-s1-000714**: `date` gold ('2026-05-12',) vs not_stated
- **test-candidates-s1-000843**: `discounts[0].description` gold ('2.5% trade discount',) vs ('trade discount',)
- **test-candidates-s1-000876**: `subtotal` gold ('2808.54',) vs not_stated
- **test-candidates-s1-000924**: `gst.amount` gold not_stated vs ('0.00',)
- **test-candidates-s1-000982**: `subtotal` gold ('360.00',) vs not_stated
- **test-candidates-s1-001009**: `payment_terms` gold ('cod',) vs ('payemnt terms: cod',)
- **test-candidates-s1-001027**: `gst.amount` gold not_stated vs ('0.00',)
- **test-candidates-s1-001048**: `discounts[0].description` gold ('Less 5% project discount',) vs ('5% project discount',)
- **test-candidates-s1-001073**: `subtotal` gold ('3587.63',) vs not_stated
- **test-candidates-s1-001078**: `line_items[1].description` gold ('A4 copy paper 80gsm, 5 reams',) vs ('A4 copy paper 80gsm',)
- **test-candidates-s1-001188**: `date` gold ('2026-08-12',) vs ('2026-12-08',)
- **test-candidates-s1-001192**: `discounts[0].description` gold ('Less 5% project discount',) vs ('5% project discount',)
- **test-candidates-s1-001206**: `discounts[0].description` gold ('Less special discount',) vs ('special discount',)
- **test-candidates-s1-001207**: `discounts[0].description` gold ('Discount 7.5%',) vs ('Discount',)
- **test-candidates-s1-001270**: `gst.amount` gold not_stated vs ('0.00',)
- **test-candidates-s1-001375**: `subtotal` gold ('1612.07',) vs not_stated
- **test-candidates-s1-001551**: `currency` gold ('MYR',) vs not_stated; `subtotal` gold ('5043.10',) vs not_stated
- **test-candidates-s1-001554**: `discounts[0].description` gold ('Less 2.5% project discount',) vs ('Less 2.5% project discount applies',)
- **test-candidates-s1-001602**: `line_items[5].description` gold ('Galvanised pipe 25mm x 6m',) vs ('Galvinised pipe 25mm x 6m',)
- **test-candidates-s1-001629**: `line_items[0].unit` gold ('m',) vs ('length',)
- **test-candidates-s1-001822**: `subtotal` gold ('642.30',) vs not_stated
- **test-candidates-s1-002003**: `discounts[0].description` gold ('Less special discount',) vs ('special discount',)
- **test-candidates-s1-002015**: `subtotal` gold ('1164.31',) vs not_stated; `total` gold not_stated vs ('1164.31',)
- **test-candidates-s1-002153**: `discounts[0].description` gold ('Discount 2.5%',) vs ('Discount 2.5% applies',)
- **test-candidates-s1-002286**: `gst.amount` gold not_stated vs ('0.00',)
- **test-candidates-s1-002312**: `subtotal` gold ('1945.29',) vs not_stated
- **test-candidates-s1-002338** (schema-invalid): `gst.treatment` gold not_stated vs <missing>
- **test-candidates-s1-002499**: `subtotal` gold ('1405.73',) vs not_stated
- **test-candidates-s1-002522**: `gst.amount` gold not_stated vs ('0.00',)
- **test-candidates-s1-002645**: `subtotal` gold ('1145.98',) vs not_stated; `total` gold not_stated vs ('1145.98',)
- **test-candidates-s1-002795**: `total` gold not_stated vs ('307.18',)
- **test-candidates-s1-002807**: `gst.amount` gold not_stated vs ('0.00',)
- **test-candidates-s1-002908**: `discounts[0].description` gold ('Discount',) vs ('Discount applies',)

</details>

<details><summary>Student: encoder tagger (in browser): 1 of 300 documents not exact</summary>

- **test-candidates-s1-000258**: `discounts[0].rate` gold ('10',) vs not_stated

</details>

<details><summary>Student: generative (in browser): 22 of 300 documents not exact</summary>

- **test-candidates-s1-000010**: `date` gold ('2026-12-09',) vs ('2026-09-12',); `validity` gold ('2026-12-31',) vs ('2026-09-30',)
- **test-candidates-s1-000495**: `line_items[7].discount` gold ('amount', '50.00') vs not_stated
- **test-candidates-s1-000714**: `date` gold ('2026-05-12',) vs ('2026-12-05',)
- **test-candidates-s1-000751**: `validity` gold ('2027-01-15',) vs ('2027-01-01',)
- **test-candidates-s1-000817**: `gst.treatment` gold exclusive vs not_stated
- **test-candidates-s1-000897**: `line_items[3].description` gold ('Digital multimeter, CAT IV',) vs ('Silicone sealant, clear 300g',); `line_items[3].quantity` gold ('1',) vs ('14',); `line_items[3].unit_price` gold ('219.59',) vs ('13.93',); `line_items[3].line_total` gold ('219.59',) vs ('195.02',); `line_items[4].description` gold ('Silicone sealant, clear 300g',) vs ('Decking screws 10g x 65mm, box of 200',); `line_items[4].unit` gold ('each',) vs ('box',); and 18 more
- **test-candidates-s1-000982**: `gst.amount` gold ('29.72',) vs not_stated
- **test-candidates-s1-001188**: `date` gold ('2026-08-12',) vs ('2026-12-08',)
- **test-candidates-s1-001216**: `line_items[5].discount` gold ('amount', '50.00') vs not_stated
- **test-candidates-s1-001351**: `line_items[4].unit` gold ('m',) vs ('each',)
- **test-candidates-s1-001402** (no output): `supplier` gold ('Merrow Facilities Services Inc.',) vs <missing>; `quote_number` gold ('MF97321',) vs <missing>; `date` gold ('2026-09-07',) vs <missing>; `currency` gold ('USD',) vs <missing>; `subtotal` gold ('280.00',) vs <missing>; `total` gold ('280.00',) vs <missing>; and 11 more
- **test-candidates-s1-001447** (no output): `supplier` gold ('Merrow Facilities Services Sdn Bhd',) vs <missing>; `quote_number` gold ('MF-Q-26-8688',) vs <missing>; `date` gold not_stated vs <missing>; `currency` gold ('MYR',) vs <missing>; `subtotal` gold ('543.87',) vs <missing>; `total` gold ('489.48',) vs <missing>; and 39 more
- **test-candidates-s1-001539**: `line_items[8].unit` gold ('m',) vs ('each',)
- **test-candidates-s1-001594**: `line_items[8].unit` gold ('box',) vs ('sheet',)
- **test-candidates-s1-001944**: `gst.treatment` gold exclusive vs not_stated
- **test-candidates-s1-002028**: `gst.treatment` gold exclusive vs not_stated
- **test-candidates-s1-002268** (no output): `supplier` gold ('Wattlebank Civil Supplies Sdn. Bhd.',) vs <missing>; `quote_number` gold ('Q26/4804',) vs <missing>; `date` gold ('2026-10-01',) vs <missing>; `currency` gold ('MYR',) vs <missing>; `subtotal` gold ('3476.70',) vs <missing>; `total` gold ('3302.86',) vs <missing>; and 39 more
- **test-candidates-s1-002408**: `line_items[5].discount` gold ('amount', '20.00') vs not_stated
- **test-candidates-s1-002645**: `date` gold ('2026-09-10',) vs ('2026-10-09',)
- **test-candidates-s1-002705**: `line_items[0].unit` gold ('m',) vs ('each',)
- **test-candidates-s1-002807**: `line_items[2].unit` gold ('l',) vs ('each',)
- **test-candidates-s1-002990**: `gst.treatment` gold exclusive vs not_stated

</details>

### Sources

- Teacher: Claude Haiku in a Claude Code subagent: `results/teacher/test-session-haiku-1/predictions.jsonl`
- Student: encoder tagger (in browser): `results/students/tagger/predictions-tagger.jsonl`
- Student: generative (in browser): `results/students/generative/predictions-generative.jsonl`
<!-- results:end -->

## Reading the results

- **Where the students' labels came from.** Both students trained on the generator's gold labels, not on Claude's outputs ([teacher role A](student-data.md), decided 19 October 2026). So Claude here is the system the students are compared with, not their source, and a student scoring above it is possible.
- **Claude's retries.** The first collect had 19 documents with no reply saved; those were re-run in four retry batches (280 → 299 parsed of 300). One reply that came back with prose before its JSON (000817) was re-run once with the unchanged prompt (PR #20). With that document's first reply, Claude scores 259/300 whole documents exact instead of 260/300. The students had one try per document.
- **Latency.** The students' times are onnxruntime on a CPU in Python. In the browser the page has one CPU thread (GitHub Pages can't send the headers that allow more), so the generative student takes minutes per document there; see [demo.md](demo.md), Part 5.
- **Cost.** Claude's cost per document comes from the credit meter readings around its session, logged in [spend.md](spend.md).

