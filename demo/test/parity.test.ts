// The TypeScript port must give exactly what the Python code gives, on every fixture document.
// Fixtures: python -m quote_distill.student.fixtures --data data/generated/student/dev.jsonl --out demo/fixtures/dev.jsonl
import { existsSync, readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { checkArithmetic } from "../src/core/arithmetic";
import { decode, type Span } from "../src/core/decode";
import { expand, parseOutput } from "../src/core/expand";
import { spansOf, type Offset } from "../src/core/tokens";

interface Fixture {
  id: string;
  text: string;
  target: string;
  spans: Span[];
  classes: { gst_treatment: string; month_first: boolean };
  expanded: unknown;
  decoded: unknown;
  decoded_guess_date_order: unknown;
  arithmetic_failures: string[];
  offsets: Offset[];
  labels: number[];
  read_spans: Span[];
}

const PATH = new URL("../fixtures/dev.jsonl", import.meta.url);
if (!existsSync(PATH)) throw new Error("Missing demo/fixtures/dev.jsonl; build it with python -m quote_distill.student.fixtures (see this file's header).");
const fixtures: Fixture[] = readFileSync(PATH, "utf-8").trim().split("\n").map((l) => JSON.parse(l));

describe(`parity with Python on ${fixtures.length} documents`, () => {
  it("has the pilot and dev documents", () => {
    expect(fixtures.length).toBeGreaterThanOrEqual(1020);
  });

  it("expands every compact target the same way", () => {
    const bad = fixtures.filter((f) => JSON.stringify(sortKeys(expand(JSON.parse(f.target)))) !== JSON.stringify(sortKeys(f.expanded)));
    expect(bad.map((f) => f.id)).toEqual([]);
  });

  it("decodes gold spans with the date-order class the same way", () => {
    const bad = fixtures.filter((f) => !same(decode(f.text, f.spans, f.classes.gst_treatment, f.classes.month_first), f.decoded));
    expect(bad.map((f) => f.id)).toEqual([]);
  });

  it("decodes gold spans without the date-order class the same way", () => {
    const bad = fixtures.filter((f) => !same(decode(f.text, f.spans, f.classes.gst_treatment, null), f.decoded_guess_date_order));
    expect(bad.map((f) => f.id)).toEqual([]);
  });

  it("finds the same arithmetic failures", () => {
    const bad = fixtures.filter((f) => !same(checkArithmetic(f.expanded as never).failures, f.arithmetic_failures));
    expect(bad.map((f) => f.id)).toEqual([]);
  });

  it("reads the same spans from token labels", () => {
    const bad = fixtures.filter((f) => !same(spansOf(f.text, f.offsets, f.labels), f.read_spans));
    expect(bad.map((f) => f.id)).toEqual([]);
  });

  it("rejects what Python's parse rejects", () => {
    const t = fixtures[0]!.target;
    expect(parseOutput(t)).not.toBeNull();
    expect(parseOutput("```json\n" + t + "\n```")).toBeNull();
    expect(parseOutput('{"supplier": "x"}')).toBeNull();
    expect(parseOutput("[]")).toBeNull();
  });
});

function sortKeys(v: unknown): unknown {
  if (Array.isArray(v)) return v.map(sortKeys);
  if (v && typeof v === "object") return Object.fromEntries(Object.keys(v).sort().map((k) => [k, sortKeys((v as Record<string, unknown>)[k])]));
  return v;
}

function same(a: unknown, b: unknown): boolean {
  return JSON.stringify(sortKeys(a)) === JSON.stringify(sortKeys(b));
}
