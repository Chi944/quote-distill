// Port of checks.check_arithmetic: the canonical formulas in docs/schema.md, for the demo's arithmetic badges.
import { Dec, HUNDRED, roundMoney } from "./decimal";
import type { Label } from "./expand";

export interface Arithmetic {
  failures: string[];
  passes: string[];
  skips: string[];
}

const stated = (f: Label) => f.state === "stated";
const dec = (f: Label) => Dec.parse(String(f.value));
const ZERO = new Dec(0n, 0);

export function checkArithmetic(label: Label): Arithmetic {
  const failures: string[] = [];
  const passes: string[] = [];
  const skips: string[] = [];
  const compare = (name: string, expected: Dec, f: Label) => {
    if (stated(f)) (dec(f).eq(expected) ? passes : failures).push(name);
    else skips.push(name);
  };

  const lines: Label[] = label.line_items;
  lines.forEach((line, i) => {
    const name = `line[${i}].line_total`;
    if (!(stated(line.quantity) && stated(line.unit_price))) {
      skips.push(name);
      return;
    }
    const gross = roundMoney(dec(line.quantity).mul(dec(line.unit_price)));
    const disc = line.discount;
    let cut = ZERO;
    if (stated(disc)) {
      const v = Dec.parse(String(disc.value));
      cut = disc.kind === "percent" ? gross.mul(v).divRound(HUNDRED, 2) : v;
    }
    compare(name, gross.sub(cut), line.line_total);
  });

  const allTotals = lines.every((l) => stated(l.line_total));
  const lineSum = allTotals ? lines.reduce<Dec>((s, l) => s.add(dec(l.line_total)), ZERO) : null;
  if (lineSum !== null) compare("subtotal", lineSum, label.subtotal);
  else skips.push("subtotal");
  let base: Dec | null = stated(label.subtotal) ? dec(label.subtotal) : lineSum;

  let discountTotal = ZERO;
  (label.discounts as Label[]).forEach((d, i) => {
    const name = `discounts[${i}].amount`;
    if (d.kind === "percent" && stated(d.rate) && base !== null) compare(name, base.mul(dec(d.rate)).divRound(HUNDRED, 2), d.amount);
    else skips.push(name);
    if (stated(d.amount)) discountTotal = discountTotal.add(dec(d.amount));
    else if (base !== null && d.kind === "percent" && stated(d.rate)) discountTotal = discountTotal.add(base.mul(dec(d.rate)).divRound(HUNDRED, 2));
    else base = null; // an unknown deduction makes everything below it uncheckable
  });

  const gst = label.gst;
  const total = label.total;
  const taxable = base === null ? null : base.sub(discountTotal);
  if (gst.treatment === "exclusive" && stated(gst.rate) && taxable !== null) {
    compare("gst.amount", taxable.mul(dec(gst.rate)).divRound(HUNDRED, 2), gst.amount);
  } else if (gst.treatment === "inclusive" && stated(gst.rate) && stated(total)) {
    const rate = dec(gst.rate);
    compare("gst.amount", dec(total).mul(rate).divRound(HUNDRED.add(rate), 2), gst.amount);
  } else {
    skips.push("gst.amount");
  }

  if (taxable === null || (gst.treatment === "exclusive" && !stated(gst.amount))) skips.push("total");
  else compare("total", taxable.add(gst.treatment === "exclusive" ? dec(gst.amount) : ZERO), total);
  return { failures, passes, skips };
}
