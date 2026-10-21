// Port of student/tokens.py's reading side: one label per token back to character spans, and logits to a label.
import { TAGS, TREATMENTS, decode, type Span } from "./decode";
import type { Label } from "./expand";

export const SPAN_LABELS = ["O", ...TAGS.flatMap((t) => [`B-${t}`, `I-${t}`])];
export const DOC_LABELS = TREATMENTS.flatMap((t) => [false, true].map((mf) => `DOC-${t}-${mf ? "M" : "D"}`));
export const LABELS = [...SPAN_LABELS, ...DOC_LABELS];

export type Offset = [start: number, end: number];

/** A token's offsets without surrounding whitespace (byte-level BPE tokens may carry a leading space). */
function trim(text: string, s: number, e: number): Offset {
  while (s < e && /\s/.test(text[s]!)) s++;
  while (e > s && /\s/.test(text[e - 1]!)) e--;
  return [s, e];
}

/** Special tokens have offsets (0, 0); whitespace-only tokens are skipped; an I- that doesn't continue opens a span. */
export function spansOf(text: string, offsets: Offset[], labelIds: number[]): Span[] {
  const out: Span[] = [];
  let cur: Span | null = null;
  offsets.forEach(([s0, e0], i) => {
    if (s0 === e0) return;
    const [s, e] = trim(text, s0, e0);
    if (s === e) return;
    const id = labelIds[i]!;
    const name = id >= 0 && id < SPAN_LABELS.length ? SPAN_LABELS[id]! : "O";
    if (name === "O") {
      cur = null;
      return;
    }
    const dash = name.indexOf("-");
    const kind = name.slice(0, dash);
    const tag = name.slice(dash + 1);
    if (kind === "I" && cur !== null && cur[2] === tag) {
      cur[1] = e;
      return;
    }
    cur = [s, e, tag];
    out.push(cur);
  });
  return out;
}

function argmax(row: ArrayLike<number>, from: number, to: number): number {
  let best = from;
  for (let j = from + 1; j < to; j++) if (row[j]! > row[best]!) best = j;
  return best;
}

/** A schema label from one document's logits (tokens x LABELS), as tokens.read does. */
export function read(text: string, offsets: Offset[], logits: ArrayLike<number>[]): Label {
  const nSpan = SPAN_LABELS.length;
  const ids = logits.map((row) => argmax(row, 0, nSpan));
  const special = offsets.findIndex(([s, e]) => s === e);
  let treatment = "not_stated";
  let monthFirst: boolean | null = null;
  if (special >= 0) {
    const [, t, mf] = LABELS[argmax(logits[special]!, nSpan, LABELS.length)]!.split("-");
    treatment = t!;
    monthFirst = mf === "M";
  }
  return decode(text, spansOf(text, offsets, ids), treatment, monthFirst);
}
