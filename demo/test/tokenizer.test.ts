// The browser's tokenizer must produce the ids Python produced in training, and offsets that cover the same text.
// Uses the tokenizer the fixtures script writes: a stand-in shaped like the tagger's (punctuation isolated), or a real
// model's tokenizer passed with --tokenizer.
import { existsSync, readFileSync } from "node:fs";
import { Tokenizer } from "@huggingface/tokenizers";
import { describe, expect, it } from "vitest";
import { byteLevelOffsets } from "../src/core/offsets";
import type { Offset } from "../src/core/tokens";

const DIR = new URL("../fixtures/tokenizer/", import.meta.url);
const FIXTURES = new URL("../fixtures/dev.jsonl", import.meta.url);
if (!existsSync(new URL("tokenizer.json", DIR))) throw new Error("Missing demo/fixtures/tokenizer; run the fixtures script with tokenizers installed.");

const tokenizerJSON = JSON.parse(readFileSync(new URL("tokenizer.json", DIR), "utf-8"));
const tokenizer = new Tokenizer(tokenizerJSON, JSON.parse(readFileSync(new URL("tokenizer_config.json", DIR), "utf-8")));
// Whichever tokenizer the fixtures were built with: the stand-in, or a real model's (fixtures --tokenizer).
const special = new Set<string>(tokenizerJSON.added_tokens.filter((t: { special: boolean }) => t.special).map((t: { content: string }) => t.content));
const rows: { id: string; text: string; token_ids: number[]; token_offsets: Offset[] }[] = readFileSync(FIXTURES, "utf-8")
  .trim()
  .split("\n")
  .map((l) => JSON.parse(l));

const trim = (text: string, [s, e]: Offset): Offset => {
  while (s < e && /\s/.test(text[s]!)) s++;
  while (e > s && /\s/.test(text[e - 1]!)) e--;
  return [s, e];
};

describe(`tokenisation matches Python on ${rows.length} documents`, () => {
  it("gives the same token ids", () => {
    const bad = rows.filter((r) => JSON.stringify(tokenizer.encode(r.text).ids) !== JSON.stringify(r.token_ids));
    expect(bad.map((r) => r.id)).toEqual([]);
  });

  it("gives offsets covering the same characters", () => {
    const bad = rows.filter((r) => {
      const ours = byteLevelOffsets(r.text, tokenizer.encode(r.text).tokens, special).map((o) => trim(r.text, o));
      return JSON.stringify(ours) !== JSON.stringify(r.token_offsets.map((o) => trim(r.text, o)));
    });
    expect(bad.map((r) => r.id)).toEqual([]);
  });

  it.skipIf(!tokenizerJSON.pre_tokenizer?.pretokenizers?.[0]?.pattern)("isolates punctuation, so \" S$.\" is three tokens", () => {
    expect(tokenizer.encode("Amounts are in S$.", { add_special_tokens: false }).tokens.slice(-3)).toEqual(["ĠS", "$", "."]);
  });
});
