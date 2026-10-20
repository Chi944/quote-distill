// Run a student over a JSONL of documents with the page's own runners and model files, timing each document.
//
//   npm run predict -- --model tagger --docs ../data/test/docs.jsonl --out ../results/students/tagger
//
// Writes predictions.jsonl ({id, output, latency_ms, ...}: the format quote_distill.metrics scores) and run.json
// (model files and their hashes, machine, totals). It reads only the --docs file it is given. Latency is
// onnxruntime-node on this machine's CPU, after one warm-up document; a browser runs the same files in WebAssembly,
// usually slower. --limit N runs the first N documents only, for a smoke test.
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { arch, cpus, platform } from "node:os";
import { join, resolve } from "node:path";
import { env } from "@huggingface/transformers";
import { loadGenerative } from "../src/models/generative";
import { loadTagger } from "../src/models/tagger";
import { type Extraction, median, parseArgs, predictAll, readDocs } from "./runs";

type Student = "tagger" | "generative";
// The dtypes the page loads (src/page/main.ts), so the scores are the page's.
const DTYPE = { tagger: "q8", generative: "q4" } as const;
const ONNX_FILE = { tagger: "model_quantized.onnx", generative: "model_q4.onnx" } as const;
const WARM_UP = "Quotation Q-1\nDrill bit set (19 pc)  3 x $24.55\nTotal: $73.65";

async function extractor(student: Student): Promise<(text: string) => Promise<Extraction>> {
  if (student === "tagger") {
    const tagger = await loadTagger(student, DTYPE.tagger);
    return async (text) => {
      const r = await tagger.extract(text);
      return { label: r.label, extra: { tokens: r.tokens, truncated: r.truncated } };
    };
  }
  const model = await loadGenerative(student, DTYPE.generative);
  return async (text) => {
    const r = await model.extract(text);
    return { label: r.label, extra: { raw: r.output } };
  };
}

const sha256 = (path: string) => createHash("sha256").update(readFileSync(path)).digest("hex");

async function main(argv: string[]): Promise<void> {
  const a = parseArgs(argv);
  const student = a.model as Student;
  if (student !== "tagger" && student !== "generative") throw new Error("--model must be tagger or generative");
  if (!a.docs || !a.out) throw new Error("--docs and --out are required");
  const modelsDir = resolve(a["models-dir"] ?? "public/models");
  env.localModelPath = modelsDir + "/";
  env.allowRemoteModels = false;

  const modelDir = join(modelsDir, student);
  const onnx = join(modelDir, "onnx", ONNX_FILE[student]);
  if (!existsSync(onnx)) throw new Error(`no model at ${onnx}: unzip ${student}-onnx.zip there (docs/demo.md)`);

  const docs = readDocs(a.docs, a.limit === undefined ? undefined : Number(a.limit));
  const extract = await extractor(student);
  await extract(WARM_UP);
  const started = new Date().toISOString();
  const rows = await predictAll(docs, extract);

  const files = Object.fromEntries(readdirSync(modelDir).filter((f) => f.endsWith(".json")).map((f) => [f, sha256(join(modelDir, f))]));
  files[`onnx/${ONNX_FILE[student]}`] = sha256(onnx);
  const latencies = rows.map((r) => r.latency_ms);
  const run = {
    student, dtype: DTYPE[student], docs: a.docs, docs_sha256: sha256(a.docs), documents: rows.length,
    parsed: rows.filter((r) => r.output !== null).length, started, finished: new Date().toISOString(),
    latency_ms: { median: median(latencies), max: latencies.length ? Math.max(...latencies) : null },
    runtime: { node: process.version, platform: `${platform()} ${arch()}`, cpu: cpus()[0]?.model ?? "unknown", backend: "onnxruntime-node" },
    model_files: files,
  };
  mkdirSync(a.out, { recursive: true });
  writeFileSync(join(a.out, "predictions.jsonl"), rows.map((r) => JSON.stringify(r)).join("\n") + "\n");
  writeFileSync(join(a.out, "run.json"), JSON.stringify(run, null, 2) + "\n");
  console.log(`${student}: ${run.parsed}/${run.documents} parsed, median ${run.latency_ms.median} ms per document; wrote ${a.out}`);
}

main(process.argv.slice(2)).catch((e) => {
  console.error(e instanceof Error ? e.message : e);
  process.exit(1);
});
