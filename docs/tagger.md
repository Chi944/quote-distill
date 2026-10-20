# Encoder tagger

The first student is a token classifier. It marks where each field is printed and predicts two document-level classes, and [`student/decode.py`](../src/quote_distill/student/decode.py) turns those marks into a schema label. It's scored with the same metrics as the teacher.

## The step and how we know it worked

**Step.** Fine-tune a small encoder on the 10,000 training documents, score it on the 1,000 validation documents, and export it to ONNX for the browser.

**It worked when** the notebook runs top to bottom on a free T4 GPU and writes `tagger-results.json` and `tagger-onnx.zip`, the tokenizer ceiling is 1000/1000, and the int8 ONNX model scores the same as the PyTorch model or reports the difference. A good tagger score is the goal, but it isn't the test of this step: whatever it scores is reported with its denominator.

## Run it

Open [`notebooks/train_tagger.ipynb`](../notebooks/train_tagger.ipynb) in Colab (*File → Open notebook → GitHub*, `Chi944/quote-distill`) or Kaggle, choose a T4 GPU and *Run all*. It needs no key and costs nothing. Download the two output files and attach them in the project thread.

## Labels

[`student/tokens.py`](../src/quote_distill/student/tokens.py) turns each document's character spans into one label per token. A token is labelled `B-<tag>` if it starts a field, `I-<tag>` if it continues one, or `O` otherwise. There are 19 tags, so 39 span labels.

The two document classes are one combined label on the first special token (`[CLS]`): four GST treatments times two date orders makes 8 labels. That keeps the model a plain token classifier, which exports to ONNX and runs in transformers.js without custom code. Whitespace-only tokens are left unlabelled and don't break a field.

## Tokenizer ceiling

A tagger can only mark whole tokens. If a token straddles a field boundary, the field can't be marked exactly. Byte-level BPE tokenizers keep runs of punctuation together, so `S$.` in "Amounts are in S$." holds the currency and the full stop in one token.

I measured this on the 1,000 validation documents with stand-in tokenizers. The real tokenizer can't be downloaded in this build environment. The result is gold labels, read back and decoded, compared with gold.

| Stand-in tokenizer | Documents exact |
|---|---|
| Words, numbers and each punctuation mark split apart | 1,000/1,000 |
| GPT-2-style, punctuation runs kept together | 922/1,000 |

The 78 losses are currency (64) and discount descriptions (16).

So `load_tokenizer` adds one pre-tokenizer step: every punctuation mark becomes its own piece before byte-level BPE. The vocabulary is unchanged, because every single character is already a token. The step is saved in `tokenizer.json`, so the browser tokenizes the same way. The notebook measures the ceiling again with the real tokenizer before training.

## Model

Default: [`jhu-clsp/ettin-encoder-32m`](https://huggingface.co/jhu-clsp/ettin-encoder-32m), a 32M-parameter ModernBERT encoder with an MIT licence and an 8K-token context. A community ONNX build of the base model exists, so transformers.js supports the architecture.

| Option | Download in the browser (int8, estimated) | Trade-off |
|---|---|---|
| Ettin 32M (default) | about 35 MB | Fast to load and run; the smallest model that might fit this task |
| Ettin 68M | about 70 MB | Likely more accurate; slower first load |

Recommendation: start with 32M, and move to 68M only if the validation score falls short. The swap is one line in the notebook, `BASE`.

## What was checked here

The build environment has no GPU and can't reach the Hugging Face Hub, so it can't train the real model. It ran everything else.

- **Label round trip:** [`tests/test_tokens.py`](../tests/test_tokens.py) checks that gold labels read back exact on all 20 pilot documents. It also checks that a punctuation run costs the currency, that whitespace tokens don't split a field, and that the document class is read from `[CLS]`.
- **Pipeline smoke test:** [`tests/test_tagger_smoke.py`](../tests/test_tagger_smoke.py) trains a 2-layer random ModernBERT for 3 steps, using a byte-level BPE tokenizer trained on the documents. It then predicts, scores and exports to ONNX. The exported model must match PyTorch within 1e-3 on padded batches and on single unpadded documents. Its predictions must be identical. CI skips this test because torch isn't installed there. Run it with `pip install -e ".[dev,train]"`.
- **Notebook dry run:** I ran the notebook's code cells with the stand-in tokenizer and tiny model on 60 training and 30 validation documents, and it wrote both output files.
