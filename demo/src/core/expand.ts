// Port of student/data.py expand(): the generative student's compact JSON back to a schema-shaped label.
/* eslint-disable @typescript-eslint/no-explicit-any */

export const LINE_ORDER = ["description", "quantity", "unit", "unit_price", "discount", "line_total"] as const;
const TOP = ["supplier", "quote_number", "date", "currency", "subtotal", "total", "validity", "payment_terms"] as const;

export type Label = Record<string, any>;

function isObject(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function need(c: unknown, key: string): any {
  if (!isObject(c) || !(key in c)) throw new Error(`missing ${key}`);
  return c[key];
}

function unpack(v: unknown): Label {
  if (v === null) return { state: "not_stated" };
  if (isObject(v)) return { state: "stated", ...v };
  return { state: "stated", value: v };
}

function rows(v: unknown, what: string): unknown[] {
  if (!Array.isArray(v)) throw new Error(`${what} is not a list`);
  return v;
}

/** Throws on a malformed input, which the caller scores as unparsed, as Python's expand raises. */
export function expand(c: unknown): Label {
  const label: Label = { schema_version: "1.0.0" };
  for (const k of TOP) label[k] = unpack(need(c, k));
  label.line_items = rows(need(c, "line_items"), "line_items").map((row) => {
    const cells = rows(row, "a line item");
    if (cells.length !== LINE_ORDER.length) throw new Error(`line item has ${cells.length} cells, expected ${LINE_ORDER.length}`);
    return Object.fromEntries(LINE_ORDER.map((k, i) => [k, unpack(cells[i])]));
  });
  label.discounts = rows(need(c, "discounts"), "discounts").map((d) => ({
    description: unpack(need(d, "description")),
    kind: need(d, "kind"),
    rate: unpack(need(d, "rate")),
    amount: unpack(need(d, "amount")),
  }));
  const gst = need(c, "gst");
  label.gst = { treatment: need(gst, "treatment"), rate: unpack(need(gst, "rate")), amount: unpack(need(gst, "amount")) };
  return label;
}

/** generative.parse: a label from generated text, or null when it isn't one compact JSON object. */
export function parseOutput(output: string): Label | null {
  try {
    return expand(JSON.parse(output.trim()));
  } catch {
    return null;
  }
}
