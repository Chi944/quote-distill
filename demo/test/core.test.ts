import { describe, expect, it } from "vitest";
import { Dec, decimalValue, moneyValue, priceValue } from "../src/core/decimal";
import { parseDate } from "../src/core/dates";
import { LABELS, SPAN_LABELS, read } from "../src/core/tokens";

describe("Dec matches Python's Decimal", () => {
  it("rounds money half up, away from zero", () => {
    expect(moneyValue(Dec.parse("2.345"))).toBe("2.35");
    expect(moneyValue(Dec.parse("-2.345"))).toBe("-2.35");
    expect(moneyValue(Dec.parse("2.344"))).toBe("2.34");
    expect(moneyValue(Dec.parse("7"))).toBe("7.00");
  });

  it("formats prices to two to four decimals", () => {
    expect(priceValue(Dec.parse("24.5"))).toBe("24.50");
    expect(priceValue(Dec.parse("0.0125"))).toBe("0.0125");
    expect(priceValue(Dec.parse("3.10000"))).toBe("3.10");
  });

  it("drops trailing zeros from quantities and rates", () => {
    expect(decimalValue(Dec.parse("2.50"))).toBe("2.5");
    expect(decimalValue(Dec.parse("10"))).toBe("10");
    expect(decimalValue(Dec.parse("10.0"))).toBe("10");
  });

  it("divides and rounds exactly", () => {
    // 38.82 is the GST inside 470.15 at 9%: 470.15 * 9 / 109 = 38.8197...
    expect(Dec.parse("470.15").mul(Dec.parse("9")).divRound(Dec.parse("109"), 2).toPlain()).toBe("38.82");
  });
});

describe("dates read like strptime", () => {
  it("reads day-first and month-first numeric dates by the class", () => {
    expect(parseDate("05/06/2026", false)).toEqual({ y: 2026, m: 6, d: 5 });
    expect(parseDate("05/06/2026", true)).toEqual({ y: 2026, m: 5, d: 6 });
  });

  it("finds a date inside a sentence and rejects impossible ones", () => {
    expect(parseDate("Prices valid until 30/07/2026", false)).toEqual({ y: 2026, m: 7, d: 30 });
    expect(parseDate("Tue, 3 Nov 2026", false)).toEqual({ y: 2026, m: 11, d: 3 });
    expect(parseDate("31/02/2026", false)).toBeNull();
  });
});

describe("read", () => {
  it("takes the document class from the first special token and spans from the rest", () => {
    const text = "Supplier: Acme Pte Ltd";
    const offsets: [number, number][] = [[0, 0], [0, 8], [8, 9], [9, 14], [14, 18], [18, 22], [0, 0]];
    const tags = ["DOC-not_charged-D", "O", "O", "B-supplier", "I-supplier", "I-supplier", "O"];
    const logits = tags.map((t) => LABELS.map((l) => (l === t ? 1 : 0)));
    const label = read(text, offsets, logits);
    expect(label.supplier).toEqual({ state: "stated", value: "Acme Pte Ltd", raw: "Acme Pte Ltd" });
    expect(label.gst.treatment).toBe("not_charged");
    expect(SPAN_LABELS.length).toBe(39);
    expect(LABELS.length).toBe(47);
  });
});
