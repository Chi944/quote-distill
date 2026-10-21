# Browser demo

The demo is a static TypeScript page. It runs both students in the browser with transformers.js and needs no key, server or paid service. This page records how it's built. It's being built in parts.

## Part 1: building answers in TypeScript

**Step.** Port everything that turns a model's raw output into a schema label to TypeScript. That covers the tagger's decoder, the generative student's `expand`, the token-label reader and the arithmetic check behind the badges.

**It worked when** the TypeScript gives exactly the Python result on every validation and pilot document. **Result: 1,020/1,020 on all five checks** (1,000 dev and 20 pilot documents):

| Check | Python source | Same result |
|---|---|---|
| Compact target to label | `student/data.py` `expand` | 1,020/1,020 |
| Gold spans to label, with the date-order class | `student/decode.py` `decode` | 1,020/1,020 |
| Gold spans to label, date order guessed from currency | `decode(..., None)` | 1,020/1,020 |
| Arithmetic failures of the gold label (62 documents have intended failures) | `checks.check_arithmetic` | 1,020/1,020 |
| Token labels back to spans | `student/tokens.py` `spans_of` | 1,020/1,020 |

Money uses an exact BigInt decimal ([`demo/src/core/decimal.ts`](../demo/src/core/decimal.ts)) with Python's rounding rules. That means half-up for amounts, and half-even only where Python's string formatting applies it. Dates use a port of CPython's `strptime` patterns for the formats in `normalise.py`.

The fixtures are generated, not committed. CI rebuilds them from the Python code on every push and runs the TypeScript tests against them:

```bash
python -m quote_distill.student.data --out data/generated/student
python -m quote_distill.student.fixtures --data data/generated/student/dev.jsonl --out demo/fixtures/dev.jsonl
cd demo && npm ci --ignore-scripts && npm test
```

## Part 2: running the models

**Step.** Load the exported ONNX files with transformers.js 4.3.1 and get answers from them in the browser: [`demo/src/models/tagger.ts`](../demo/src/models/tagger.ts) and [`demo/src/models/generative.ts`](../demo/src/models/generative.ts).

**It worked when** the browser tokenizes exactly as Python does, and the browser runners get exactly Python's answers from the same model files. **Result: all checks pass.**

| Check | Same result |
|---|---|
| Token ids, stand-in byte-level tokenizer with punctuation isolated | 1,020/1,020 documents |
| Token offsets (the characters each token covers) | 1,020/1,020 documents |
| Tagger labels, float32 `model.onnx` | 10/10 documents |
| Tagger labels, int8 `model_quantized.onnx` | 10/10 documents |
| Generative greedy output (24 new tokens), float32 `model.onnx` | 4/4 documents |
| Generative greedy output (24 new tokens), 4-bit `model_q4.onnx` | 4/4 documents |

How the tagger gets offsets: the browser tokenizer returns token ids and token strings but no character offsets, and the tagger needs to know which characters each token covers. Each byte-level token string maps back to its UTF-8 bytes through GPT-2's byte table, so walking the tokens along the text gives the offsets ([`demo/src/core/offsets.ts`](../demo/src/core/offsets.ts)). It throws if the tokens don't spell the text, rather than guess.

The model checks use tiny random models (two layers, 32 wide) in the real export layout, built by the same export code the notebooks use. Their answers are nonsense; the point is that the browser gets the same nonsense from the same files. The generative model is initialised with large weights so its outputs vary instead of repeating one token. Building them needs torch, so CI skips these two checks and runs the tokenizer checks; run them locally with:

```bash
pip install -e ".[train]" && python tests/demo_models.py tagger
pip install -e ".[generative]" && python tests/demo_models.py generative   # optimum-onnx needs transformers < 4.58
cd demo && npm ci --ignore-scripts && npm test
```

The real tokenizers (Ettin's and SmolLM2's) are checked the same way once the notebooks' exports are attached: `python -m quote_distill.student.fixtures ... --tokenizer <unpacked export>`, then `npm test`. They can't be fetched in the build environment, where Hugging Face downloads are blocked.

## Part 3: the page

**Step.** A static page ([`demo/index.html`](../demo/index.html), [`demo/src/page/`](../demo/src/page/)). Pick one of the 20 pilot quotations or paste your own, and both students run one after the other. Each shows its fields, line items and discounts, one arithmetic badge per check (adds up, doesn't add up, or can't be checked), and how long it took. For a sample, each value is marked against the sample's answer key, with a count such as "24 of 26 values match". That count is a quick per-value comparison for the page, not the evaluation metric; the reported results come from `metrics.py`. The generative student's text streams in as it's written, and its raw output stays one click away.

**It worked when** the built page, in Chromium, shows the same answers the Node runners give for the same text, and fetches nothing from outside the page. **Result: passes** with the tiny models ([`demo/test/page.test.ts`](../demo/test/page.test.ts)). Two fixes came out of it: transformers.js only reads "local" models from a path on the page's own host, not a full URL; and it fetches its ONNX runtime from a CDN unless told otherwise, so the page now serves that runtime itself. Layout was checked at desktop width and at 390 px (phone), where wide tables scroll inside their panel.

Model files are static files next to the page, which the page fetches once:

```
demo/public/models/tagger/        config.json, tokenizer files, onnx/model_quantized.onnx   (from tagger-onnx.zip)
demo/public/models/generative/    config.json, tokenizer files, onnx/model_q4.onnx          (from generative-onnx.zip)
```

Until they're there, each panel says its model isn't published yet. To try the page with the tiny test models:

```bash
cd demo && npm ci --ignore-scripts
mkdir -p public/models && cp -r fixtures/models/tiny-tagger public/models/tagger && cp -r fixtures/models/tiny-generative public/models/generative
npm run dev
```

The browser test runs with `npm test` when the tiny models and Chromium (`CHROMIUM_PATH`) are present; CI has neither, so it builds the page and skips that test.

## Next part

- **Publishing:** put the trained models where the page can fetch them, deploy to GitHub Pages, and link it from the README.
