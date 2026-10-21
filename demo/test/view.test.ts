import { describe, expect, it } from "vitest";
import { checkArithmetic } from "../src/core/arithmetic";
import { SAMPLES } from "../src/page/samples";
import { badges, escape, fields, summary } from "../src/page/view";

const clone = <T>(x: T): T => JSON.parse(JSON.stringify(x));

describe("the page's view of a label", () => {
  it("has all 20 pilot documents as samples", () => {
    expect(SAMPLES.map((s) => s.id).slice(0, 5)).toEqual(["seed-01", "seed-02", "seed-03", "seed-04", "seed-05"]);
    expect(SAMPLES).toHaveLength(20);
  });

  it("counts every value as matching when the label is the answer key", () => {
    for (const s of SAMPLES) {
      const { agreement } = fields(s.key, s.key);
      // 8 top fields + 3 GST + one per line item and discount
      expect(agreement).toEqual({ same: 11 + s.key.line_items.length + s.key.discounts.length, of: 11 + s.key.line_items.length + s.key.discounts.length });
    }
  });

  it("counts a changed value, a missing line and an extra line against the student", () => {
    const key = SAMPLES[0]!.key;
    const wrong = clone(key);
    wrong.total = { state: "stated", value: "1.00", raw: "1.00" };
    const n = 11 + key.line_items.length + key.discounts.length;
    expect(fields(wrong, key).agreement).toEqual({ same: n - 1, of: n });
    const short = clone(key);
    short.line_items.pop();
    expect(fields(short, key).agreement).toEqual({ same: n - 1, of: n });
    const long = clone(key);
    long.line_items.push(clone(key.line_items[0]));
    expect(fields(long, key).agreement).toEqual({ same: n, of: n + 1 });
  });

  it("shows no marks without an answer key, and escapes the document's text", () => {
    const label = clone(SAMPLES[0]!.key);
    label.supplier = { state: "stated", value: "<img src=x onerror=alert(1)>", raw: "" };
    const { html, agreement } = fields(label);
    expect(agreement).toBeNull();
    expect(html).not.toContain("<img");
    expect(html).not.toContain('class="mark');
    expect(escape(`a<b>"c"&'d'`)).toBe("a&#60;b&#62;&#34;c&#34;&#38;&#39;d&#39;");
  });

  it("labels the arithmetic checks as the gold label's results", () => {
    const seed4 = SAMPLES.find((s) => s.id === "seed-04")!; // the supplier's line 2 total is wrong on purpose
    const result = checkArithmetic(seed4.key);
    expect(result.failures).toEqual(["line[1].line_total"]);
    expect(badges(result)).toContain(`<span class="badge fail" title="Doesn't add up: the document or the extraction has an error">Line 2 total</span>`);
    expect(summary(result)).toMatch(/^\d+ of \d+ checks add up/);
    expect(summary({ passes: [], failures: [], skips: ["total"] })).toBe("nothing could be checked");
  });
});
