// Port of decode.parse_date: Python's strptime for the formats in DATE_FORMATS, in the same order.
import { DATE_FORMATS, collapse } from "./normalise";

export interface YMD {
  y: number;
  m: number;
  d: number;
}

const MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];
const ABBR = MONTHS.map((m) => m.slice(0, 3));
const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"];

// The regexes CPython's _strptime uses for these directives (C locale).
const DIRECTIVE: Record<string, string> = {
  d: "(?<d>3[01]|[12]\\d|0[1-9]|[1-9]| [1-9])",
  m: "(?<m>1[0-2]|0[1-9]|[1-9])",
  Y: "(?<Y>\\d\\d\\d\\d)",
  b: `(?<b>${ABBR.join("|")})`,
  B: `(?<B>${MONTHS.join("|")})`,
  a: `(?<a>${DAYS.join("|")})`,
};

function compile(format: string): RegExp {
  let out = "";
  for (let i = 0; i < format.length; i++) {
    const c = format[i]!;
    if (c === "%") {
      out += DIRECTIVE[format[++i]!];
    } else if (/\s/.test(c)) {
      while (i + 1 < format.length && /\s/.test(format[i + 1]!)) i++;
      out += "\\s+";
    } else {
      out += c.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }
  }
  return new RegExp(`^(?:${out})`, "i");
}

const COMPILED = new Map<string, RegExp>();

function strptime(text: string, format: string): YMD | null {
  let re = COMPILED.get(format);
  if (!re) COMPILED.set(format, (re = compile(format)));
  const m = re.exec(text);
  if (!m || m[0].length !== text.length) return null;
  const g = m.groups ?? {};
  const y = Number(g.Y);
  const mo = g.m ? Number(g.m) : g.b ? ABBR.indexOf(g.b.toLowerCase()) + 1 : MONTHS.indexOf(g.B!.toLowerCase()) + 1;
  const d = Number(g.d!.trim());
  const probe = new Date(Date.UTC(y, mo - 1, d));
  if (probe.getUTCFullYear() !== y || probe.getUTCMonth() !== mo - 1 || probe.getUTCDate() !== d) return null;
  return { y, m: mo, d };
}

function formats(monthFirst: boolean): string[] {
  const us = DATE_FORMATS.US!;
  const rest = [...new Set(Object.entries(DATE_FORMATS).filter(([k]) => k !== "US").flatMap(([, fs]) => fs))].sort();
  return monthFirst ? [...us, ...rest] : [...rest, ...us];
}

const INSIDE = /[A-Za-z]{3}, \d{1,2} [A-Za-z]{3,9} \d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{1,2} [A-Za-z]{3,9} \d{4}|[A-Za-z]{3,9} \d{1,2}, \d{4}/g;

/** The first format that reads the whole raw text, or a date inside it ("Prices valid until 30/07/2026"). */
export function parseDate(raw: string, monthFirst: boolean): YMD | null {
  const text = collapse(raw);
  const candidates = [text, ...Array.from(text.matchAll(INSIDE), (m) => m[0])];
  for (const c of candidates) {
    for (const f of formats(monthFirst)) {
      const d = strptime(c, f);
      if (d) return d;
    }
  }
  return null;
}

export function iso({ y, m, d }: YMD): string {
  return `${String(y).padStart(4, "0")}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

export function endOfMonth({ y, m }: YMD): YMD {
  return { y, m, d: new Date(Date.UTC(y, m, 0)).getUTCDate() };
}
