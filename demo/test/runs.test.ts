// The prediction loop behind `npm run predict`: one row per document, in order, timed, extras kept.
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { median, parseArgs, predictAll, readDocs } from "../scripts/runs";

describe("predictAll", () => {
  it("keeps input order, times each document and merges extras", async () => {
    let t = 0;
    const now = () => t;
    const rows = await predictAll(
      [{ id: "a", text: "one" }, { id: "b", text: "three" }],
      async (text) => {
        t += text.length * 10; // a fake clock: 10 ms per character
        return { label: text === "one" ? { supplier: { state: "not_stated" } } : null, extra: { raw: text } };
      },
      now,
    );
    expect(rows).toEqual([
      { id: "a", output: { supplier: { state: "not_stated" } }, latency_ms: 30, raw: "one" },
      { id: "b", output: null, latency_ms: 50, raw: "three" },
    ]);
  });
});

describe("helpers", () => {
  it("takes the median of odd and even lists", () => {
    expect(median([3, 1, 2])).toBe(2);
    expect(median([4, 1, 3, 2])).toBe(2.5);
    expect(median([])).toBeNull();
  });

  it("reads id and text from JSONL and honours a limit", () => {
    const path = join(mkdtempSync(join(tmpdir(), "runs-")), "docs.jsonl");
    writeFileSync(path, '{"id":"x","text":"t1","label":{}}\n\n{"id":"y","text":"t2"}\n');
    expect(readDocs(path)).toEqual([{ id: "x", text: "t1" }, { id: "y", text: "t2" }]);
    expect(readDocs(path, 1)).toEqual([{ id: "x", text: "t1" }]);
  });

  it("parses --name value pairs and rejects a dangling flag", () => {
    expect(parseArgs(["--model", "tagger", "--limit", "5"])).toEqual({ model: "tagger", limit: "5" });
    expect(() => parseArgs(["--model"])).toThrow();
  });
});
