// Port of src/quote_distill/normalise.py and checks.number_in. Keep the tables identical to the Python ones.
import { Dec } from "./decimal";

export const UNIT_SYNONYMS: Record<string, string[]> = {
  each: ["ea", "each", "pcs", "pc", "units", "nos"],
  pair: ["pr", "pair", "pairs"],
  box: ["box", "bx", "boxes"],
  pack: ["pk", "pack", "packs"],
  set: ["set", "sets"],
  sheet: ["sheet", "sheets", "sht", "sh"],
  length: ["length", "lengths", "lgth"],
  roll: ["roll", "rolls"],
  bag: ["bag", "bags"],
  m: ["m", "lm", "metre", "metres"],
  m2: ["m2", "m²", "sqm"],
  m3: ["m3", "m³", "cu m"],
  kg: ["kg", "kgs"],
  tonne: ["t", "tonne", "tonnes"],
  l: ["l", "litre", "litres"],
  hour: ["hr", "hrs", "hour", "hours"],
  day: ["day", "days"],
  week: ["wk", "week", "weeks"],
  month: ["mth", "month", "months"],
  lot: ["lot", "l/s", "lump sum", "flat"],
};
export const UNIT_BY_RAW = new Map(Object.entries(UNIT_SYNONYMS).flatMap(([unit, raws]) => raws.map((r) => [r, unit] as const)));

// Only codes, prefixed symbols and names are stated currency; a bare "$" never is.
export const CURRENCY_TOKENS = new Map<string, string>([
  ["SGD", "SGD"], ["S$", "SGD"], ["Singapore dollars", "SGD"], ["Singapore dollars (S$)", "SGD"],
  ["AUD", "AUD"], ["A$", "AUD"], ["Australian dollars", "AUD"],
  ["NZD", "NZD"], ["NZ$", "NZD"], ["New Zealand dollars", "NZD"],
  ["MYR", "MYR"], ["RM", "MYR"], ["Ringgit", "MYR"],
  ["USD", "USD"], ["US$", "USD"], ["US dollars", "USD"],
]);

export const DATE_FORMATS: Record<string, string[]> = {
  SG: ["%d %b %Y", "%d %B %Y", "%d/%m/%Y", "%a, %d %b %Y"],
  AU: ["%d/%m/%Y", "%d %B %Y", "%d %b %Y", "%a, %d %b %Y"],
  NZ: ["%d %B %Y", "%d/%m/%Y", "%d %b %Y", "%a, %d %b %Y"],
  MY: ["%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%a, %d %b %Y"],
  US: ["%B %d, %Y", "%m/%d/%Y", "%b %d, %Y", "%a, %d %b %Y"],
};

const NUMBER_WORDS = new Map("zero one two three four five six seven eight nine ten eleven twelve".split(" ").map((w, i) => [w, i]));
const FREE_WORDS = new Set(["foc", "free", "n/c", "no charge"]);
const NUMBER = /-?\d[\d,]*(?:\.\d+)?/;

/** Python's " ".join(text.split()). */
export function collapse(text: string): string {
  return text.split(/\s+/).filter(Boolean).join(" ");
}

export function normalisePaymentTerms(raw: string): string {
  return collapse(raw).toLowerCase().replace(/\.+$/, "");
}

/** checks.number_in: the first number in raw, or a number word, or 0 for "FOC". */
export function numberIn(raw: string): Dec | null {
  const text = raw.trim().toLowerCase();
  if (FREE_WORDS.has(text)) return new Dec(0n, 0);
  const word = NUMBER_WORDS.get(text);
  if (word !== undefined) return Dec.of(word);
  const m = NUMBER.exec(raw);
  return m ? Dec.parse(m[0].replaceAll(",", "")) : null;
}
