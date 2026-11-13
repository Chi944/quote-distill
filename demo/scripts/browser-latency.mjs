// Times both students in a real browser on the published demo: each of the page's 20 sample quotations, one at a
// time, reading the seconds the page itself shows (model call only, after the model has loaded). Writes a JSON
// summary with medians, p95s and every sample's time.
//   CHROMIUM_PATH=<chrome> [ONLY_IDS=a,b] node scripts/browser-latency.mjs [url] [out.json]
import { writeFileSync } from "node:fs";
import os from "node:os";
import { chromium } from "playwright-core";

const url = process.argv[2] ?? "https://chi944.github.io/quote-distill/";
const out = process.argv[3] ?? "browser-latency.json";
const seconds = (text) => Number(/([\d.]+) s/.exec(text ?? "")?.[1]);

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH });
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto(url);
const only = process.env.ONLY_IDS?.split(",");  // to finish an interrupted run
const ids = (await page.$$eval("#sample option", (os) => os.map((o) => o.value).filter(Boolean))).filter((id) => !only || only.includes(id));
const rows = [];
for (const id of ids) {
  await page.selectOption("#sample", id, { timeout: 10 * 60_000 });
  await page.click("#run", { timeout: 10 * 60_000 });
  await page.waitForFunction(() => !document.querySelector("#run").disabled, null, { timeout: 30 * 60_000 });
  const row = {
    id,
    tagger_s: seconds(await page.textContent("#tagger .meta")),
    threads: Number(/(\d+) CPU thread/.exec((await page.textContent("#tagger .meta")) ?? "")?.[1]),
    tagger_status: (await page.textContent("#tagger .status"))?.trim(),
    generative_s: seconds(await page.textContent("#generative .meta")),
    generative_status: (await page.textContent("#generative .status"))?.trim(),
  };
  rows.push(row);
  console.log(JSON.stringify(row));
}
const stats = (xs) => {
  const s = xs.filter(Number.isFinite).sort((a, b) => a - b);
  return { n: s.length, median_s: s[Math.floor(s.length / 2)], p95_s: s[Math.floor(0.95 * (s.length - 1))] };
};
const summary = {
  url, date: new Date().toISOString(), browser: `Chromium ${browser.version()} (headless)`,
  machine: `${os.cpus()[0].model}, ${os.cpus().length} threads, ${Math.round(os.totalmem() / 2 ** 30)} GB RAM`,
  cross_origin_isolated: await page.evaluate(() => globalThis.crossOriginIsolated),
  threads: [...new Set(rows.map((r) => r.threads))],
  tagger: stats(rows.map((r) => r.tagger_s)), generative: stats(rows.map((r) => r.generative_s)),
  page_errors: errors, samples: rows,
};
await browser.close();
writeFileSync(out, JSON.stringify(summary, null, 1));
console.log(JSON.stringify({ tagger: summary.tagger, generative: summary.generative, errors: errors.length }));
