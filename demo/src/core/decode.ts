// Port of student/decode.py: the tagger's spans and two document classes back to a schema label.
import { Dec, decimalValue, moneyValue, priceValue } from "./decimal";
import { endOfMonth, iso, parseDate, type YMD } from "./dates";
import type { Label } from "./expand";
import { CURRENCY_TOKENS, UNIT_BY_RAW, collapse, normalisePaymentTerms, numberIn } from "./normalise";

export const DOC_TAGS = ["supplier", "quote_number", "date", "currency", "subtotal", "total", "validity", "payment_terms", "gst.rate", "gst.amount"];
export const LINE_TAGS = ["description", "quantity", "unit", "unit_price", "discount", "line_total"];
export const DISCOUNT_TAGS = ["description", "rate", "amount"];
export const TAGS = [...DOC_TAGS, ...LINE_TAGS.map((t) => `line_items.${t}`), ...DISCOUNT_TAGS.map((t) => `discounts.${t}`)];
export const TREATMENTS = ["exclusive", "inclusive", "not_charged", "not_stated"];

export type Span = [start: number, end: number, tag: string];

const NS: Label = { state: "not_stated" };
// Longest first, so "NZ$" wins over a bare "$" and "Singapore dollars (S$)" over "S$".
const CURRENCY = [...CURRENCY_TOKENS.keys()].sort((a, b) => b.length - a.length);
const PERCENT = /(\d+(?:\.\d+)?)\s*%/;
const RELATIVE_END_OF_MONTH = /end of (this|the) month/i;

const stated = (value: string | null, raw: string): Label => (value !== null ? { state: "stated", value, raw } : NS);

function number(raw: string): Dec | null {
  let n = numberIn(raw);
  if (n !== null && /\(\s*[^)]*\d[^)]*\)/.test(raw) && n.cmp(new Dec(0n, 0)) > 0) n = n.neg(); // accounting brackets
  return n;
}
const money = (raw: string) => {
  const n = number(raw);
  return n === null ? null : moneyValue(n);
};
const price = (raw: string) => {
  const n = number(raw);
  return n === null ? null : priceValue(n);
};
const decimal = (raw: string) => {
  const n = numberIn(raw);
  return n === null ? null : decimalValue(n);
};

const escape = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
function currencyIn(raw: string): string | null {
  return CURRENCY.find((t) => new RegExp(`(?<![A-Za-z])${escape(t)}(?![A-Za-z])`).test(raw)) ?? null;
}

function validity(raw: string, quoteDate: YMD | null, monthFirst: boolean): string | null {
  if (RELATIVE_END_OF_MONTH.test(raw)) return quoteDate === null ? null : iso(endOfMonth(quoteDate));
  const days = /(\d+)\s*days?/i.exec(raw);
  if (days) return `P${Number(days[1])}D`;
  const d = parseDate(raw, monthFirst);
  return d ? iso(d) : null;
}

const bySpan = (a: Span, b: Span) => a[0] - b[0] || a[1] - b[1] || (a[2] < b[2] ? -1 : a[2] > b[2] ? 1 : 0);
const lineStart = (text: string, pos: number) => (pos === 0 ? 0 : text.lastIndexOf("\n", pos - 1) + 1);

/** Each description opens a group; every other span joins the description whose region holds it. */
function group(text: string, spans: Span[], prefix: string): Map<string, [number, number]>[] {
  const descs = spans.filter(([, , t]) => t === `${prefix}.description`).map(([s, e]) => [s, e] as [number, number]);
  descs.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const starts: number[] = [];
  let prevEnd = 0;
  for (const [s, e] of descs) {
    const line = lineStart(text, s);
    starts.push(line >= prevEnd ? line : s);
    prevEnd = e;
  }
  const groups = descs.map((d) => new Map([["description", d]]));
  for (const [s, e, t] of [...spans].sort(bySpan)) {
    if (!t.startsWith(`${prefix}.`) || t === `${prefix}.description`) continue;
    let k: number | null = null;
    starts.forEach((st, i) => {
      if (st <= s) k = i;
    });
    if (k === null) {
      if (groups.length === 0) groups.push(new Map());
      k = 0;
    }
    const field = t.slice(prefix.length + 1);
    const g = groups[k]!;
    if (!g.has(field)) g.set(field, [s, e]);
  }
  return groups;
}

const texts = (text: string, g: Map<string, [number, number]>) => new Map([...g].map(([k, [s, e]]) => [k, text.slice(s, e)]));

/** spans: [start, end, tag] with tags from TAGS; treatment: one of TREATMENTS; monthFirst: the date-order class,
 * or null to guess it from the currency (US dollars). */
export function decode(text: string, spans: Span[], treatment: string, monthFirst: boolean | null = null): Label {
  const raw = new Map<string, string>();
  for (const [s, e, t] of [...spans].sort(bySpan)) if (DOC_TAGS.includes(t) && !raw.has(t)) raw.set(t, text.slice(s, e));

  const moneyRaws = spans.filter(([, , t]) => /(amount|total|subtotal|unit_price)$/.test(t)).map(([s, e]) => text.slice(s, e));
  const currencyRaw = raw.get("currency") || moneyRaws.map(currencyIn).find((c) => c) || null;
  const currency = currencyRaw ? (CURRENCY_TOKENS.get(currencyRaw.trim()) ?? null) : null;
  const mf = monthFirst ?? currency === "USD";

  const dateRaw = raw.get("date");
  const quoteDate = dateRaw !== undefined ? parseDate(dateRaw, mf) : null;
  const supplier = raw.get("supplier");
  const quoteNumber = raw.get("quote_number");
  const label: Label = {
    schema_version: "1.0.0",
    supplier: supplier !== undefined ? stated(collapse(supplier), supplier) : NS,
    quote_number: quoteNumber !== undefined ? stated(collapse(quoteNumber), quoteNumber) : NS,
    date: stated(quoteDate ? iso(quoteDate) : null, dateRaw ?? ""),
    currency: stated(currency, currencyRaw ?? ""),
  };

  label.line_items = group(text, spans, "line_items").map((g) => {
    const r = texts(text, g);
    let disc: Label = NS;
    const d = r.get("discount");
    if (d !== undefined) {
      const pct = PERCENT.exec(d);
      disc = pct ? { state: "stated", kind: "percent", value: decimalValue(Dec.parse(pct[1]!)), raw: d } : { state: "stated", kind: "amount", value: money(d), raw: d };
    }
    const f = (k: string, conv: (raw: string) => string | null) => {
      const v = r.get(k);
      return v !== undefined ? stated(conv(v), v) : NS;
    };
    return {
      description: f("description", collapse),
      quantity: f("quantity", decimal),
      unit: f("unit", (v) => UNIT_BY_RAW.get(v.trim().toLowerCase()) ?? null),
      unit_price: f("unit_price", price),
      discount: disc,
      line_total: f("line_total", money),
    };
  });

  label.discounts = group(text, spans, "discounts").map((g) => {
    const r = texts(text, g);
    const desc = r.get("description") ?? "";
    const rateRaw = r.get("rate") || PERCENT.exec(desc)?.[0] || null;
    const amount = r.get("amount");
    return {
      description: desc ? stated(collapse(desc), desc) : NS,
      kind: rateRaw ? "percent" : "amount",
      rate: rateRaw ? stated(decimal(rateRaw), rateRaw) : NS,
      amount: amount !== undefined ? stated(money(amount), amount) : NS,
    };
  });

  let gstRateRaw = raw.get("gst.rate") ?? null;
  if (gstRateRaw === null && (treatment === "exclusive" || treatment === "inclusive")) {
    // A rate printed inside a GST label ("GST 9%: 38.82", "include 10% GST") that the tagger can't mark alone.
    const cue = /(\d+(?:\.\d+)?%)[ \t]*GST|GST[^\n\d]{0,20}?(\d+(?:\.\d+)?%)/.exec(text);
    gstRateRaw = cue ? (cue[1] ?? cue[2] ?? null) : null;
  }
  const gstAmount = raw.get("gst.amount");
  label.gst = {
    treatment,
    rate: gstRateRaw ? stated(decimal(gstRateRaw), gstRateRaw) : NS,
    amount: gstAmount !== undefined ? stated(money(gstAmount), gstAmount) : NS,
  };
  for (const k of ["subtotal", "total"]) {
    const v = raw.get(k);
    label[k] = v !== undefined ? stated(money(v), v) : NS;
  }
  const v = raw.get("validity");
  label.validity = v !== undefined ? stated(validity(v, quoteDate, mf), v) : NS;
  const p = raw.get("payment_terms");
  label.payment_terms = p !== undefined ? stated(normalisePaymentTerms(p), p) : NS;
  return label;
}
