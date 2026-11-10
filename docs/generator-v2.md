# Generator v2: wider layouts and wording

The published students score 299/300 and 278/300 on the generator's own test set, and 0/30 on 30 quotations written by hand in new layouts ([ood.md](ood.md)). They learned the generator's five layouts and its fixed words, not quotations in general. Generator v2 is the attempt to fix that: the same schema and the same label rules, but more ways of printing a quotation.

**It worked when** every v2 document passes the label checks, the tagger's spans align on every one, v1 output stays byte-identical, no v2 training document shares a line with the hand-written set, and students retrained on v2 score better on the frozen 30 without losing much on the original test set. The first four are tested in CI (`tests/test_generator.py`). The last needs a retraining run and is reported below once it exists.

## What changed

`python -m quote_distill.generator.build --style v2` (or `generate(..., style="v2")`) samples from the v1 vocabulary plus [`generator/vocab_v2.py`](../src/quote_distill/generator/vocab_v2.py), and renders with ten layouts instead of five:

| Added | Examples |
|---|---|
| 5 layouts | `kv_table` (key: value header, shuffled and renamed columns), `delimited` (comma or tab rows pasted from a spreadsheet), `totals_first` (summary above an itemised breakdown), `numbered_lines` ("1) Desc - 4 ea @ $5.00 = $20.00"), `bare_columns` (aligned columns with no heading row) |
| Header words | Title as Quote, Price Quote, Estimate, Proposal, Offer or Pro Forma Quote; totals as Grand total, Total payable, Amount due, Nett total and others; also synonyms for Description, Subtotal, Discount, Quantity, Validity and Payment. About a third of documents keep each v1 word |
| Header shapes | Shuffled key: value fields (Ref, Doc no., Dated, Issue date, Bill to, Prepared for and others), title above or below the supplier |
| Vocabulary | 24 more supplier name words and 24 trades, 36 more items (printing, events, IT, catering, lab, roofing, solar, cleaning, furniture, packaging and others), 10 more lump sums, 12 more payment terms, 8 more customers |
| Values | All four of each locale's date formats (v1 uses three), 5 more quote number shapes, 6 more validity phrasings and 5 more "valid until" leads |

The schema, the units, the currencies and the arithmetic are unchanged, so labels mean exactly what they did. Style v1 draws the same random numbers in the same order as before, so the test set, the pilot and the published students' training data are untouched.

## Training data

`python -m quote_distill.student.data --generator v2 --out data/generated/student` builds 12,000 training and 1,000 validation documents (seeds 3 and 4; v1 used 1 and 2). Both pass every label check, every target round-trips exactly, and every document's spans align for the tagger (12,000/12,000 and 1,000/1,000). Text length is close to v1's: median 646 characters against 672.

On top of the test-set and pilot filters, any document that shares a line of 30 or more characters with a hand-written out-of-distribution document is dropped. None did: 0 of 13,000. The seeds aren't in that filter, because the v1 vocabulary was first drawn from them and an address line is shared by design.

**A limit to keep in mind.** The same author (Claude, in this project) wrote both the hand-written set and v2. v2 was written from general variation axes, not from those 30 documents, and no line is shared, but some words overlap: "Estimate", "Proposal" and "Grand total" are common words that appear in both. So a gain on the frozen 30 is partly a gain on wording we chose to add. A fair confirmation would be a second hand-written set, written after training by someone who hasn't seen v2.

## Retraining (free)

1. Open [`notebooks/train_tagger.ipynb`](../notebooks/train_tagger.ipynb) in Colab with a T4 GPU (or Kaggle, or your PC). `GENERATOR = "v2"` is already set. Run all: about 10 minutes.
2. Do the same with [`notebooks/train_generative.ipynb`](../notebooks/train_generative.ipynb). This one takes about an hour and a half. Keep the tab active so Colab doesn't disconnect.
3. In each notebook, either set `UPLOAD = True` in the last cell (with a Hugging Face write token saved as the Colab secret `HF_TOKEN`), or download the zip and the results file and attach them in the project thread. Uploads go to `v2/tagger/` and `v2/generative/`, beside the published models, so the demo is unchanged.
4. On GitHub, run the `ood` workflow with `folder = v2` and `test_set` ticked. It scores the new students on the frozen 30, the seeds and the 300-document test set, and pushes the predictions to a `results/ood-<run>` branch.

The demo moves to the v2 models only if they do better on the frozen 30 without a large loss on the test set. That's a separate change, decided with the numbers in hand.

## Results

Not run yet.
