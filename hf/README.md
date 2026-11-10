---
license: other
license_name: mit-and-apache-2.0
language:
  - en
library_name: transformers.js
pipeline_tag: token-classification
tags:
  - onnx
  - information-extraction
  - document-extraction
  - quotations
  - knowledge-distillation
  - synthetic-data
base_model:
  - jhu-clsp/ettin-encoder-32m
  - HuggingFaceTB/SmolLM2-360M-Instruct
---

# Quote Distill students

Two small models that extract supplier quotations into structured JSON in the browser, with no API key and no server. They are the students in [Quote Distill](https://github.com/Chi944/quote-distill), a teacher-versus-student study, and they power the [live demo](https://chi944.github.io/quote-distill/).

| Folder | Model | Base | What it does | File the demo loads |
|---|---|---|---|---|
| `tagger/` | Encoder tagger, 32M parameters | [jhu-clsp/ettin-encoder-32m](https://huggingface.co/jhu-clsp/ettin-encoder-32m) (MIT) | Marks each field's span in the text; deterministic code turns the spans into JSON | `onnx/model.onnx`, float32, 128 MB |
| `generative/` | Generative, 362M parameters | [HuggingFaceTB/SmolLM2-360M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct) (Apache-2.0) | Writes the JSON directly | `onnx/model_q4.onnx` with `model_q4.onnx_data`, 4-bit, 387 MB |

The output follows the [quotation schema v1.0.0](https://github.com/Chi944/quote-distill/blob/main/docs/schema.md): supplier, quote number, date, currency, line items, discounts, GST, subtotal, total, validity and payment terms. Each field is either stated, with its normalised value, or explicitly not stated. Money values are exact two-decimal strings.

## Results

These are scored on the frozen 300-document test set by the project's own metrics, which count every field and every line item. The full tables and the failure gallery are in [docs/evaluation.md](https://github.com/Chi944/quote-distill/blob/main/docs/evaluation.md).

| Model | Per-field exact | Whole document exact | Median latency (CPU, onnxruntime) |
|---|---|---|---|
| Teacher: Claude Haiku | 11172/11208 (99.7%) | 260/300 (86.7%) | not measured |
| Tagger | 11208/11208 (100.0%) | 299/300 (99.7%) | 30 ms |
| Generative (4-bit) | 11066/11208 (98.7%) | 278/300 (92.7%) | 12.5 s |

**Read these with care.** The test set comes from the same synthetic generator as the training data. It has its own random streams and shares no texts with training, but its layouts and wording are the same. That favours the students. A hand-written out-of-distribution check is in [docs/ood.md](https://github.com/Chi944/quote-distill/blob/main/docs/ood.md).

## Use

The demo's loaders are the reference: [`demo/src/models/`](https://github.com/Chi944/quote-distill/tree/main/demo/src/models) for transformers.js and [`src/quote_distill/student/`](https://github.com/Chi944/quote-distill/tree/main/src/quote_distill/student) for Python with onnxruntime. Neither model is usable with a stock pipeline alone. The tagger needs the repository's tokenisation (punctuation split before BPE) and its span decoder. The generative model needs its training prompt, greedy decoding and the JSON expansion. Tests show the Python and TypeScript code give the same results on 1,020 documents.

## Licence

The repository's code and the tagger are MIT. The generative weights are a fine-tune of SmolLM2-360M-Instruct, so they keep its Apache-2.0 licence and notice.

## Training data

Everything is synthetic: 10,000 generated training quotations and 1,000 for validation, across five locales (Singapore, Australia, New Zealand, Malaysia, United States) and five layouts. They include hard cases such as GST-inclusive prices, line and document discounts, half-cent rounding ties, credits and free-of-charge rows, missing fields and supplier arithmetic errors. Labels come from the generator and are verified by deterministic arithmetic checks. No real suppliers, prices or documents are used. Training ran on one consumer GPU; the notebooks are in the repository.

## Limits

- The models are trained on one generator's quotations. Expect lower accuracy on real documents, other layouts and other languages.
- The tagger reads the first 1,024 tokens. The generative model writes at most 768 new tokens.
- The schema's tax field is GST. Malaysia's SST and US sales tax are not modelled.
- `not_stated` means the document doesn't print the value. The models are trained not to infer values, but they can still be wrong. Check the output against the document before relying on it.

## Files not used by the demo

`tagger/onnx/model_quantized.onnx` (int8) scores 32/1000 on dev documents, because dynamic quantisation breaks this model. Don't use it. `generative/onnx/model_quantized.onnx` (int8) scored 69/100 on dev documents and isn't loaded by the demo.
