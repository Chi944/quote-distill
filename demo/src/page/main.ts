// Wires the page: pick or paste a quotation, load each model on first use, run both, show what they extracted.
import { env, type ProgressInfo } from "@huggingface/transformers";
import type { Label } from "../core/expand";
import { type Generative, loadGenerative } from "../models/generative";
import { type Tagger, loadTagger } from "../models/tagger";
import { SAMPLES } from "./samples";
import ortMjs from "onnxruntime-web/ort-wasm-simd-threaded.asyncify.mjs?url";
import ortWasm from "onnxruntime-web/ort-wasm-simd-threaded.asyncify.wasm?url";
import { badges, checkArithmetic, escape, fields, summary } from "./view";
import "./style.css";

// Model files are static files next to the page: models/tagger/ and models/generative/ (see docs/demo.md).
// A path, not a full URL: transformers.js only fetches "local" models from paths on the page's own host.
env.localModelPath = new URL("models/", location.href).pathname;
env.allowLocalModels = true;
env.allowRemoteModels = false;
// The ONNX runtime from this page too; transformers.js would otherwise fetch it from a CDN.
env.backends.onnx.wasm!.wasmPaths = { mjs: ortMjs, wasm: ortWasm };

const $ = <T extends HTMLElement>(sel: string) => document.querySelector<T>(sel)!;
const select = $<HTMLSelectElement>("#sample");
const textarea = $<HTMLTextAreaElement>("#text");
const button = $<HTMLButtonElement>("#run");
const note = $<HTMLSpanElement>("#note");

for (const s of SAMPLES) select.add(new Option(s.name, s.id));
select.add(new Option("My own text", ""));
const showSample = () => {
  const s = SAMPLES.find((x) => x.id === select.value);
  if (s) textarea.value = s.text;
};
select.addEventListener("change", showSample);
textarea.addEventListener("input", () => {
  if (SAMPLES.find((x) => x.id === select.value)?.text !== textarea.value) select.value = "";
});
showSample();

/** The answer key, only while the text is exactly a sample's. */
const answerKey = (text: string): Label | undefined => SAMPLES.find((s) => s.text === text)?.key;

function panel(id: string) {
  const root = $<HTMLElement>(`#${id}`);
  const status = root.querySelector<HTMLElement>(".status")!;
  const out = root.querySelector<HTMLElement>(".out")!;
  return {
    root,
    say(msg: string, cls = "") {
      status.textContent = msg;
      status.className = `status ${cls}`;
    },
    show(html: string) {
      out.innerHTML = html;
    },
  };
}

function progress(p: ReturnType<typeof panel>) {
  return (info: ProgressInfo) => {
    if (info.status === "progress" && info.total > 1_000_000) {
      p.say(`Downloading the model: ${(info.loaded / 1e6).toFixed(0)} of ${(info.total / 1e6).toFixed(0)} MB`);
    }
  };
}

// A model that fails to load (usually: its files aren't published yet) stays failed until the page reloads.
let tagger: Promise<Tagger> | null = null;
let generative: Promise<Generative> | null = null;

function result(label: Label, key: Label | undefined, ms: number, extra: string): string {
  const arithmetic = checkArithmetic(label);
  const { html, agreement } = fields(label, key);
  const agree = agreement ? ` · ${agreement.same} of ${agreement.of} values match the answer key` : "";
  return `<p class="meta">${(ms / 1000).toFixed(2)} s${extra}${agree}</p>
    <div class="checks"><h4>Arithmetic: ${summary(arithmetic)}</h4>${badges(arithmetic)}</div>${html}`;
}

async function runTagger(text: string, key: Label | undefined) {
  const p = panel("tagger");
  p.show("");
  p.say("Loading the model…");
  try {
    tagger ??= loadTagger("tagger", "fp32", progress(p));
    const model = await tagger;
    p.say("Extracting…");
    const t0 = performance.now();
    const r = await model.extract(text);
    const ms = performance.now() - t0;
    p.root.dataset.label = JSON.stringify(r.label);
    p.say(r.truncated ? `Done. The text was ${r.tokens} tokens, so only the first 1,024 were read.` : "Done.", "done");
    p.show(result(r.label, key, ms, ` · ${r.tokens} tokens`));
  } catch (e) {
    tagger = null;
    failed(p, "tagger", e);
  }
}

async function runGenerative(text: string, key: Label | undefined) {
  const p = panel("generative");
  p.show("");
  p.say("Loading the model…");
  try {
    generative ??= loadGenerative("generative", "q4", progress(p));
    const model = await generative;
    p.say("Writing JSON…");
    const t0 = performance.now();
    const r = await model.extract(text, {
      onText: (soFar) => p.show(`<pre class="stream">${escape(soFar)}</pre>`),
    });
    const ms = performance.now() - t0;
    p.root.dataset.output = r.output;
    const raw = `<details><summary>Raw output</summary><pre>${escape(r.output)}</pre></details>`;
    if (r.label === null) {
      p.say("Done, but the output isn't valid quotation JSON, so nothing could be read from it.", "bad");
      p.show(`<p class="meta">${(ms / 1000).toFixed(2)} s</p>${raw}`);
      return;
    }
    p.root.dataset.label = JSON.stringify(r.label);
    p.say("Done.", "done");
    p.show(result(r.label, key, ms, "") + raw);
  } catch (e) {
    generative = null;
    failed(p, "generative", e);
  }
}

function failed(p: ReturnType<typeof panel>, dir: string, e: unknown) {
  console.error((e as Error)?.stack ?? e);
  const msg = String((e as Error)?.message ?? e);
  const missing = /404|not found|could not locate|failed to fetch/i.test(msg);
  p.say(missing ? `This model's files aren't published yet (expected under models/${dir}/).` : `Something went wrong: ${msg}`, "bad");
}

button.addEventListener("click", async () => {
  const text = textarea.value;
  if (!text.trim()) {
    note.textContent = "Paste a quotation first.";
    return;
  }
  note.textContent = "";
  button.disabled = true;
  const key = answerKey(text);
  // One after the other: both share the device, and the tagger is quick.
  await runTagger(text, key);
  await runGenerative(text, key);
  button.disabled = false;
});
