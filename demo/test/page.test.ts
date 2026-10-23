// The built page, in a real browser, with the tiny models: it must show the answers the Node runners give for the
// same text, and fetch nothing from outside the page. Needs the tiny models (tests/demo_models.py) and Chromium
// (CHROMIUM_PATH, or Playwright's bundled one), so it skips when either is missing, as in CI.
import { cpSync, existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { env } from "@huggingface/transformers";
import { chromium } from "playwright-core";
import { build, preview } from "vite";
import { afterAll, describe, expect, it } from "vitest";
import { loadGenerative } from "../src/models/generative";
import { loadTagger } from "../src/models/tagger";
import { SAMPLES } from "../src/page/samples";

const ROOT = fileURLToPath(new URL("..", import.meta.url));
const MODELS = fileURLToPath(new URL("../fixtures/models/", import.meta.url));
const CHROMIUM = [process.env.CHROMIUM_PATH, "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"].find((p) => p && existsSync(p));
const ready = existsSync(join(MODELS, "tiny-tagger")) && existsSync(join(MODELS, "tiny-generative")) && CHROMIUM !== undefined;

env.localModelPath = MODELS;
env.allowRemoteModels = false;

describe.skipIf(!ready)("the page in a browser", () => {
  const out = mkdtempSync(join(tmpdir(), "qd-page-"));
  afterAll(() => rmSync(out, { recursive: true, force: true }));

  it("shows both students' answers for a sample, matching Node, with no outside requests", async () => {
    await build({ root: ROOT, logLevel: "warn", build: { outDir: out, emptyOutDir: true } });
    cpSync(join(MODELS, "tiny-tagger"), join(out, "models", "tagger"), { recursive: true });
    cpSync(join(MODELS, "tiny-generative"), join(out, "models", "generative"), { recursive: true });
    const server = await preview({ root: ROOT, logLevel: "warn", build: { outDir: out }, preview: { port: 0 } });
    const url = server.resolvedUrls!.local[0]!;
    const browser = await chromium.launch({ executablePath: CHROMIUM });
    try {
      const page = await browser.newPage();
      const outside: string[] = [];
      const errors: string[] = [];
      page.on("request", (r) => {
        if (!r.url().startsWith(url) && !r.url().startsWith("data:") && !r.url().startsWith("blob:")) outside.push(r.url());
      });
      page.on("pageerror", (e) => errors.push(String(e)));
      await page.goto(url);
      const sample = SAMPLES[0]!;
      await page.selectOption("#sample", sample.id);
      await page.click("#run");
      await page.waitForSelector("#generative .status.done, #generative .status.bad", { timeout: 120_000 });
      const tagger = await page.getAttribute("#tagger", "data-label");
      const output = await page.getAttribute("#generative", "data-output");
      if (process.env.SCREENSHOT) await page.screenshot({ path: process.env.SCREENSHOT, fullPage: true });

      expect(await page.textContent("#tagger .status")).toBe("Done.");
      expect(JSON.parse(tagger!)).toEqual((await (await loadTagger("tiny-tagger", "fp32")).extract(sample.text)).label);
      expect(output).toBe((await (await loadGenerative("tiny-generative", "q4")).extract(sample.text)).output);
      expect(await page.textContent("#tagger .meta")).toMatch(/values match the answer key/);
      expect(outside).toEqual([]);
      expect(errors).toEqual([]);
    } finally {
      await browser.close();
      await new Promise((r) => server.httpServer.close(r));
    }
  }, 300_000);

  it("loads the models from VITE_MODEL_BASE when the build sets it", async () => {
    // Stands in for a Hugging Face repo: the model folders under <base>/{tagger,generative}/ on another path.
    const port = 4179;
    const base = `http://localhost:${port}/hub/user/repo/resolve/main/`;
    process.env.VITE_MODEL_BASE = base;
    try {
      await build({ root: ROOT, logLevel: "warn", build: { outDir: out, emptyOutDir: true } });
    } finally {
      delete process.env.VITE_MODEL_BASE;
    }
    const hub = join(out, "hub", "user", "repo", "resolve", "main");
    cpSync(join(MODELS, "tiny-tagger"), join(hub, "tagger"), { recursive: true });
    cpSync(join(MODELS, "tiny-generative"), join(hub, "generative"), { recursive: true });
    const server = await preview({ root: ROOT, logLevel: "warn", build: { outDir: out }, preview: { port, strictPort: true } });
    const browser = await chromium.launch({ executablePath: CHROMIUM });
    try {
      const page = await browser.newPage();
      const models: string[] = [];
      page.on("request", (r) => {
        if (r.url().includes("/hub/")) models.push(new URL(r.url()).pathname);
      });
      await page.goto(`http://localhost:${port}/`);
      await page.click("#run");
      await page.waitForSelector("#generative .status.done, #generative .status.bad", { timeout: 120_000 });
      expect(await page.textContent("#tagger .status")).toBe("Done.");
      expect(models).toContain("/hub/user/repo/resolve/main/tagger/onnx/model.onnx");
      expect(models).toContain("/hub/user/repo/resolve/main/generative/onnx/model_q4.onnx");
    } finally {
      await browser.close();
      await new Promise((r) => server.httpServer.close(r));
    }
  }, 300_000);
});
