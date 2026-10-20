// The browser runners must get the same answers Python gets from the same ONNX files. The tiny random models and
// Python's answers come from `python tests/demo_models.py tagger|generative` (needs torch, so CI skips this file).
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { env } from "@huggingface/transformers";
import { describe, expect, it } from "vitest";
import { loadGenerative } from "../src/models/generative";
import { PROMPT } from "../src/models/generative";
import { type Dtype as TaggerDtype, loadTagger } from "../src/models/tagger";

const DIR = new URL("../fixtures/models/", import.meta.url);
env.localModelPath = fileURLToPath(DIR);
env.allowRemoteModels = false;

const DTYPE: Record<string, "fp32" | "q8" | "q4"> = { "model.onnx": "fp32", "model_quantized.onnx": "q8", "model_q4.onnx": "q4" };
const json = (name: string) => JSON.parse(readFileSync(new URL(name, DIR), "utf-8"));
const has = (name: string) => existsSync(new URL(name, DIR));

describe.skipIf(!has("tagger-expected.json"))("tagger runner matches Python", () => {
  const cases: { file: string; text: string; label: unknown }[] = has("tagger-expected.json") ? json("tagger-expected.json") : [];
  for (const file of new Set(cases.map((c) => c.file))) {
    it(`gives Python's labels with ${file}`, async () => {
      const tagger = await loadTagger("tiny-tagger", DTYPE[file] as TaggerDtype);
      const mine = cases.filter((c) => c.file === file);
      for (const c of mine) expect((await tagger.extract(c.text)).label).toEqual(c.label);
    });
  }
});

describe.skipIf(!has("generative-expected.json"))("generative runner matches Python", () => {
  const expected: { prompt: string; max_new_tokens: number; cases: { file: string; text: string; output: string }[] } =
    has("generative-expected.json") ? json("generative-expected.json") : { prompt: "", max_new_tokens: 0, cases: [] };
  it("uses the training prompt", () => expect(PROMPT).toBe(expected.prompt));
  for (const file of new Set(expected.cases.map((c) => c.file))) {
    it(`gives Python's greedy output with ${file}`, async () => {
      const model = await loadGenerative("tiny-generative", DTYPE[file]!);
      for (const c of expected.cases.filter((c) => c.file === file)) {
        let streamed = "";
        const r = await model.extract(c.text, { maxNewTokens: expected.max_new_tokens, onText: (t) => (streamed = t) });
        expect(r.output).toBe(c.output);
        expect(streamed).toBe(c.output);
      }
    }, 60_000);
  }
});
