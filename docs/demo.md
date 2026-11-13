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
demo/public/models/tagger/        config.json, tokenizer files, onnx/model.onnx             (from tagger-onnx.zip)
demo/public/models/generative/    config.json, tokenizer files, onnx/model_q4.onnx + onnx/model_q4.onnx_data
```

Until they're there, each panel says its model isn't published yet. To try the page with the tiny test models:

```bash
cd demo && npm ci --ignore-scripts
mkdir -p public/models && cp -r fixtures/models/tiny-tagger public/models/tagger && cp -r fixtures/models/tiny-generative public/models/generative
npm run dev
```

The browser test runs with `npm test` when the tiny models and Chromium (`CHROMIUM_PATH`) are present; CI has neither, so it builds the page and skips that test.

## Part 4: publishing

**Step.** GitHub Pages serves the built page ([`.github/workflows/pages.yml`](../.github/workflows/pages.yml)), and the models come from a public Hugging Face repo. GitHub can't hold them: the float32 tagger is 128 MB, over GitHub's 100 MB file limit, and Pages doesn't serve Git LFS files. Hugging Face serves model files to any page, free and without a key.

The build reads `VITE_MODEL_BASE`, the URL above the two model folders, for example `https://huggingface.co/<user>/<repo>/resolve/main/`. The page then fetches `<base>tagger/...` and `<base>generative/...` instead of `models/` next to itself. Without it, the page reads `models/` as before. The workflow takes the URL from the repository variable `MODEL_BASE`.

To publish, once: make the model repo public; under Settings > Pages set the source to GitHub Actions; under Settings > Secrets and variables > Actions > Variables add `MODEL_BASE`. Then run the workflow, or push to main.

**It worked when** a build with `VITE_MODEL_BASE` loads both models from under that URL in a browser. **Result: passes** with the tiny models served from a stand-in path ([`demo/test/page.test.ts`](../demo/test/page.test.ts)). The live check is opening the published page.

## Part 5: memory

**Step.** The published page crashed the tab when the generative model ran (reported 23 October 2026). With a stand-in of the same shape and size (SmolLM2-360M, random weights, the same 4-bit export, 387 MB) in headless Chromium, the tab's renderer peaked at about 2.0 GB just starting the model. Two changes that leave the weights untouched bring that down:

| Generative model only, renderer peak | MB |
|---|---|
| One 387 MB file (as published) | 2,033 |
| Weights in `onnx/model_q4.onnx_data` beside a 1.4 MB graph | 1,484 |
| ... and no weight repacking at load (`disable_prepacking`) | 1,320 |
| The int8 file, for comparison (scores 69/100 on dev, so not used) | 1,593 |
| WebGPU (SwiftShader) instead of the CPU: renderer, plus 1.3 GB in the GPU process | 2,480 |

The whole page (tagger, then the generative model) now peaks at 1,459 MB, against about 2,100 MB before. Generation speed is unchanged (64 new tokens: 121 s against 122 s, one CPU thread). `python -m quote_distill.student.generative <dir>/onnx/model_q4.onnx` splits an existing export in place; `export_onnx` now writes the split layout.

**It worked when** the tiny models still give Python's exact outputs in Node and in the browser with the split file (`npm test`, 31/31), and the stand-in's renderer peak drops. **Result: passes** for both. What it doesn't fix: devices with less memory than about 1.5 GB to spare for one tab, and the time (one CPU thread, since GitHub Pages can't send the headers that allow more).

## Part 6: more than one CPU thread

**Step.** WebAssembly can only use more than one thread on a cross-origin isolated page, which needs two response headers (COOP and COEP) that GitHub Pages can't send. [`public/isolate-sw.js`](../demo/public/isolate-sw.js) is a small service worker that adds them to the page's own responses. A script at the top of `index.html` registers it and reloads once, on the first visit, when it takes control. Requests to Hugging Face don't go through the worker: they are CORS fetches, which COEP `require-corp` allows. The page then gives onnxruntime-web up to 4 threads, leaving one core free (`main.ts`), and each result line says how many it used. If anything fails (an old browser, or storage blocked), the page still works on one thread, as before.

**It worked when** the built page turns `crossOriginIsolated` on after one reload, still fetches from another origin, doesn't reload in a loop (`test/isolation.test.ts`, which CI now runs against the preinstalled Chrome), the tiny models still give Python's exact outputs in the isolated page (`test/page.test.ts`, local), and generation gets faster. **Result: passes.** A stand-in with the published model's shape and size (SmolLM2-360M layout, random weights, the same split 4-bit export), timed in headless Chromium on a 4-core machine: a 300-token prompt, then 32 new tokens.

| Threads | Prompt (300 tokens) | Per new token |
|---|---|---|
| 1 (before) | 8.8 s | 952 ms |
| 2 (onnxruntime-web's default here: half the cores) | 5.8 s | 586 ms |
| 4 | 4.7 s | 376 ms |

That is about 2.5 times faster on this machine; how much faster on yours depends on its cores. What it doesn't change: memory, and the first visit's single extra reload.

## Part 7: timed in a browser

**Step.** Time both students on the published page in a real browser, not the Python CPU timings in the results table. [`demo/scripts/browser-latency.mjs`](../demo/scripts/browser-latency.mjs) opens the live demo in headless Chromium, runs each of the page's 20 sample quotations one at a time, and reads the seconds the page itself shows. That is the model call only, after the model has loaded once. It writes [`results/students/browser-latency.json`](../results/students/browser-latency.json) with every sample's time, its outcome, the page's thread count, and whether the page was cross-origin isolated.

```bash
cd demo && CHROMIUM_PATH=<chrome> node scripts/browser-latency.mjs https://chi944.github.io/quote-distill/ ../results/students/browser-latency.json
```

**It worked when** all 20 samples finish with no page errors and the page reports its thread count. **Result: passes.** The run used Chromium 153 (headless) on d's PC, a 12th Gen Intel Core i5-12400 (6 cores, 12 threads, 32 GB RAM), on 14 November 2026. The page was cross-origin isolated and reported 4 CPU threads on every sample.

| Student | n | Median per document | p95 |
|---|---|---|---|
| Encoder tagger | 20 | 0.09 s | 0.18 s |
| Generative | 20 | 66.9 s | 108.3 s |

Before Part 6, on one thread, an earlier run on the same machine timed 18 of the same 20 samples before it was cut off: the tagger took 0.29 s median and the generative student 222 s. With 4 threads, the same 18 samples took 0.09 s and 65.0 s, about 3.4 times faster. The single-thread rows are in [`results/students/browser-latency-1-thread.jsonl`](../results/students/browser-latency-1-thread.jsonl).

The generative student's output wasn't valid quotation JSON for 2 of the 20 samples, `seed-01` and `seed-04`, two of the five hand-written seeds. `seed-01` fails the same way in Python with the same q4 file, so that failure is the model's, not the browser's. The tagger read all 20.

## Next part

- **Publishing:** put the trained models where the page can fetch them, deploy to GitHub Pages, and link it from the README.
