// The demo's sample quotations: the 20 pilot documents (5 hand-written, 15 generated), all synthetic, each with its
// answer key. Read from data/pilot at build time, so they stay the hash-checked files.
import pilot from "../../../data/pilot/pilot-20.jsonl?raw";
import type { Label } from "../core/expand";

export interface Sample {
  id: string;
  name: string;
  text: string;
  key: Label;
}

const LOCALES: Record<string, string> = { AU: "Australia", NZ: "New Zealand", SG: "Singapore", MY: "Malaysia", US: "United States" };

export const SAMPLES: Sample[] = pilot
  .trim()
  .split("\n")
  .map((line) => JSON.parse(line))
  .map((r) => ({
    id: r.id,
    name: `${r.meta.family === "hand-written seed" ? "Hand-written" : r.meta.family}, ${LOCALES[r.meta.locale] ?? r.meta.locale} (${r.id})`,
    text: r.text,
    key: r.label,
  }));
