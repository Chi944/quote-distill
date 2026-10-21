// Turns a schema label into the page's HTML: fields, line items, the arithmetic badges and, for a sample, whether
// each value agrees with the sample's answer key. Pure string functions, so they're tested without a browser.
import { type Arithmetic, checkArithmetic } from "../core/arithmetic";
import { LINE_ORDER, type Label } from "../core/expand";

const TOP: [key: string, name: string][] = [
  ["supplier", "Supplier"], ["quote_number", "Quote number"], ["date", "Date"], ["currency", "Currency"],
  ["subtotal", "Subtotal"], ["total", "Total"], ["validity", "Valid until"], ["payment_terms", "Payment terms"],
];
const LINE_NAMES = ["Description", "Qty", "Unit", "Unit price", "Discount", "Line total"];

export function escape(s: string): string {
  return s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}

const shown = (f: Label | undefined): string => (f?.state === "stated" ? String(f.value) : "");
/** Same value as the answer key: both not stated, or both stated with the same normalised value. */
export const same = (a: Label | undefined, b: Label | undefined): boolean => shown(a) === shown(b) && a?.state === b?.state;

function cell(f: Label | undefined): string {
  if (f?.state !== "stated") return `<span class="missing">not stated</span>`;
  if (f.value === null || f.value === undefined) return escape(String(f.raw ?? "")); // stated but not normalised
  return escape(String(f.value) + (f.kind === "percent" ? "%" : ""));
}

function mark(ok: boolean | null): string {
  if (ok === null) return "";
  return ok ? `<td class="mark ok" title="Matches the answer key">✓</td>` : `<td class="mark bad" title="Differs from the answer key">✗</td>`;
}

export interface Agreement {
  same: number;
  of: number;
}

/** Fields, line items, discounts and GST as tables; with `key`, a ✓ or ✗ beside each against the answer key. */
export function fields(label: Label, key?: Label): { html: string; agreement: Agreement | null } {
  let ok = 0;
  let of = 0;
  // Counts one comparison against the answer key; null (no mark) when there is no key.
  const judge = (agrees: () => boolean): boolean | null => {
    if (!key) return null;
    of++;
    const s = agrees();
    if (s) ok++;
    return s;
  };
  const row = (x: Label | undefined, cols: readonly string[]) => (x ? JSON.stringify(cols.map((c) => [x[c]?.state, shown(x[c])])) : null);

  const top = TOP.map(([k, name]) => `<tr><th>${name}</th><td>${cell(label[k])}</td>${mark(judge(() => same(label[k], key![k])))}</tr>`);
  const gst = label.gst as Label;
  top.push(`<tr><th>GST treatment</th><td>${escape(String(gst.treatment).replace("_", " "))}</td>${mark(judge(() => gst.treatment === key!.gst.treatment))}</tr>`);
  top.push(`<tr><th>GST rate</th><td>${cell(gst.rate)}</td>${mark(judge(() => same(gst.rate, key!.gst.rate)))}</tr>`);
  top.push(`<tr><th>GST amount</th><td>${cell(gst.amount)}</td>${mark(judge(() => same(gst.amount, key!.gst.amount)))}</tr>`);

  const lines = (label.line_items as Label[]).map((line, i) => {
    const agrees = judge(() => row(line, LINE_ORDER) === row(key!.line_items[i], LINE_ORDER));
    return `<tr>${mark(agrees)}${LINE_ORDER.map((c) => `<td>${cell(line[c])}</td>`).join("")}</tr>`;
  });
  const DISC = ["description", "rate", "amount"];
  const discounts = (label.discounts as Label[]).map((d, i) => {
    const want: Label | undefined = key?.discounts[i];
    const agrees = judge(() => want !== undefined && d.kind === want.kind && row(d, DISC) === row(want, DISC));
    return `<tr><td>${cell(d.description)}</td><td>${escape(String(d.kind))}</td><td>${cell(d.rate)}</td><td>${cell(d.amount)}</td>${mark(agrees)}</tr>`;
  });
  // Lines and discounts the student missed count against it too.
  if (key) of += Math.max(0, key.line_items.length - label.line_items.length) + Math.max(0, key.discounts.length - label.discounts.length);

  const html = [
    `<table class="fields"><tbody>${top.join("")}</tbody></table>`,
    `<h4>Line items (${label.line_items.length})</h4>`,
    `<div class="scroll"><table class="lines"><thead><tr>${key ? "<th></th>" : ""}${LINE_NAMES.map((n) => `<th>${n}</th>`).join("")}</tr></thead><tbody>${lines.join("")}</tbody></table></div>`,
    discounts.length
      ? `<h4>Document discounts</h4><div class="scroll"><table class="lines"><thead><tr><th>Description</th><th>Kind</th><th>Rate</th><th>Amount</th>${key ? "<th></th>" : ""}</tr></thead><tbody>${discounts.join("")}</tbody></table></div>`
      : "",
  ].join("");
  return { html, agreement: key ? { same: ok, of } : null };
}

const CHECK_NAMES: Record<string, string> = { subtotal: "Subtotal", "gst.amount": "GST amount", total: "Total" };
function checkName(name: string): string {
  const line = /^line\[(\d+)\]\.line_total$/.exec(name);
  if (line) return `Line ${Number(line[1]) + 1} total`;
  const disc = /^discounts\[(\d+)\]\.amount$/.exec(name);
  if (disc) return `Discount ${Number(disc[1]) + 1}`;
  return CHECK_NAMES[name] ?? name;
}

/** One badge per arithmetic check: adds up, doesn't add up, or can't be checked from what was extracted. */
export function badges(result: Arithmetic): string {
  const b = (cls: string, title: string, names: string[]) =>
    names.map((n) => `<span class="badge ${cls}" title="${title}">${escape(checkName(n))}</span>`).join("");
  return [
    b("pass", "Adds up", result.passes),
    b("fail", "Doesn't add up: the document or the extraction has an error", result.failures),
    b("skip", "Can't be checked from the extracted values", result.skips),
  ].join("");
}

export function summary(result: Arithmetic): string {
  const n = result.passes.length + result.failures.length;
  if (n === 0) return "nothing could be checked";
  return `${result.passes.length} of ${n} checks add up${result.skips.length ? `, ${result.skips.length} can't be checked` : ""}`;
}

export { checkArithmetic };
