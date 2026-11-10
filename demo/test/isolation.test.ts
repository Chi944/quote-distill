// The built page isolates itself with isolate-sw.js (multi-threaded WebAssembly), and still reaches a model host on
// another origin, as it does Hugging Face. Needs Chromium (CHROMIUM_PATH, or Playwright's bundled one) and skips
// without it, as in CI.
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";
import { build, preview } from "vite";
import { afterAll, describe, expect, it } from "vitest";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const CHROMIUM = [process.env.CHROMIUM_PATH, "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"].find((p) => p && existsSync(p));

describe.skipIf(CHROMIUM === undefined)("cross-origin isolation", () => {
  const out = mkdtempSync(join(tmpdir(), "qd-isolate-"));
  afterAll(() => rmSync(out, { recursive: true, force: true }));

  it("turns on after one reload, and keeps CORS fetches to another origin working", async () => {
    await build({ root: ROOT, logLevel: "warn", build: { outDir: out, emptyOutDir: true } });
    const server = await preview({ root: ROOT, logLevel: "warn", build: { outDir: out }, preview: { port: 0 } });
    const url = server.resolvedUrls!.local[0]!;
    // Stands in for huggingface.co: another origin that answers with CORS headers and nothing else.
    const hub = createServer((_, res) => {
      res.writeHead(200, { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" });
      res.end('{"ok":true}');
    });
    await new Promise<void>((r) => hub.listen(0, "127.0.0.1", r));
    const hubUrl = `http://127.0.0.1:${(hub.address() as { port: number }).port}/config.json`;
    const browser = await chromium.launch({ executablePath: CHROMIUM });
    try {
      const page = await browser.newPage();
      const errors: string[] = [];
      page.on("pageerror", (e) => errors.push(String(e)));
      await page.goto(url);
      await page.waitForFunction(() => window.crossOriginIsolated === true, undefined, { timeout: 20_000 });
      expect(await page.evaluate(() => typeof SharedArrayBuffer)).toBe("function");
      expect(await page.evaluate((u) => fetch(u).then((r) => r.json()), hubUrl)).toEqual({ ok: true });
      // The sample text still loads, so the page's own scripts survived the reload.
      expect((await page.inputValue("#text")).length).toBeGreaterThan(50);
      // Reloading again doesn't loop: the worker already controls the page.
      await page.reload();
      expect(await page.evaluate(() => window.crossOriginIsolated)).toBe(true);
      expect(errors).toEqual([]);
    } finally {
      await browser.close();
      await new Promise((r) => hub.close(r));
      await new Promise((r) => server.httpServer.close(r));
    }
  }, 120_000);
});
