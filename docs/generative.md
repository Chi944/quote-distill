# Generative student

The second student is a small language model. It reads the document and writes the compact target from [student-data.md](student-data.md#target-format), which `expand` turns into a schema label. It's scored with the same metrics as the teacher and the tagger, and output that isn't valid compact JSON counts as unparsed.

## The step and how we know it worked

**Step.** Fine-tune a model under 500M parameters on the 10,000 training documents, score it on the 1,000 validation documents, and export it to ONNX with a KV cache for the browser.

**It worked when** the notebook runs top to bottom on a free T4 and writes `generative-results.json` and `generative-onnx.zip`. The results must include the validation score with denominators, the quantised models' score on 100 of those documents next to PyTorch on the same 100, and CPU latency per document.

## Run it

Open [`notebooks/train_generative.ipynb`](../notebooks/train_generative.ipynb) in Colab or Kaggle, choose a T4 GPU and *Run all*. Training two epochs takes roughly an hour, and scoring the 1,000 documents about 15 more minutes. Download the two output files and attach them in the project thread.

## Prompt and target

```text
Extract the supplier quotation below as compact JSON.
### Quotation
<document text>
### JSON
<compact target><end of text>
```

Loss is on the target only. The demo must send exactly this prompt, so it is fixed in [`student/generative.py`](../src/quote_distill/student/generative.py) as `PROMPT`. Decoding is greedy with at most 768 new tokens. The longest validation target is 1,183 characters.

## Model

Default: [`HuggingFaceTB/SmolLM2-360M-Instruct`](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct). It has 362M parameters, an Apache-2.0 licence, and transformers.js already runs it.

| Option | Parameters | Trade-off |
|---|---|---|
| SmolLM2-360M (default) | 362M | The largest well-supported browser model under the 500M limit |
| SmolLM2-135M | 135M | About 3 times faster per token in the browser; likely less accurate |

Qwen3-0.6B was ruled out: it has 752M parameters, which is over the 500M limit.

A generative model writes one token at a time, so it will be much slower in the browser than the tagger. The demo will measure both.

## Versions

ONNX export with a KV cache goes through `optimum-onnx` 0.1.0, which requires transformers below 4.58. So this notebook installs the `generative` extra (transformers 4.57) rather than `train`. The tagger code also runs on 4.57.

## What was checked here

The build environment has no GPU and can't reach the Hugging Face Hub, so I ran everything else.

- **Pipeline smoke test:** [`tests/test_generative_smoke.py`](../tests/test_generative_smoke.py) trains a 2-layer random Llama (SmolLM2's architecture) for 3 steps with a stand-in tokenizer. It then generates, scores, and exports float32, int8 and 4-bit ONNX in the transformers.js layout. The float32 ONNX model with its KV cache must produce exactly the same greedy outputs as PyTorch, and both quantised files must load and generate. CI skips this test because torch isn't installed there.
- **Output parsing:** `parse` accepts one compact JSON object and nothing else. A code fence counts as unparsed, as it did for the teacher.
- **Notebook dry run:** I ran the notebook's code cells from a fresh clone, using the stand-in tokenizer and the tiny model on 60 training and 30 validation documents. It wrote both output files.
