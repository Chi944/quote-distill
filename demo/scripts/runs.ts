// The per-document loop behind scripts/predict.ts, kept free of model loading so it can be tested without models.
import { readFileSync } from "node:fs";
import type { Label } from "../src/core/expand";

export interface Doc {
  id: string;
  text: string;
}

export interface Extraction {
  label: Label | null;
  extra?: Record<string, unknown>;
}

export interface Row {
  id: string;
  output: Label | null;
  latency_ms: number;
  [key: string]: unknown;
}

/** One row per document, in input order. `now` is injectable so tests can check the timing. */
export async function predictAll(docs: Doc[], extract: (text: string) => Promise<Extraction>,
                                 now: () => number = () => performance.now()): Promise<Row[]> {
  const rows: Row[] = [];
  for (const doc of docs) {
    const start = now();
    const { label, extra } = await extract(doc.text);
    rows.push({ id: doc.id, output: label, latency_ms: Math.round((now() - start) * 10) / 10, ...extra });
  }
  return rows;
}

export function median(xs: number[]): number | null {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid]! : (s[mid - 1]! + s[mid]!) / 2;
}

export function readDocs(path: string, limit?: number): Doc[] {
  const docs = readFileSync(path, "utf-8").split("\n").filter((l) => l.trim()).map((l) => {
    const r = JSON.parse(l);
    return { id: r.id as string, text: r.text as string };
  });
  return limit === undefined ? docs : docs.slice(0, limit);
}

export function parseArgs(argv: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i]!;
    if (!key.startsWith("--") || argv[i + 1] === undefined) throw new Error(`expected --name value, got ${key}`);
    out[key.slice(2)] = argv[i + 1]!;
  }
  return out;
}
