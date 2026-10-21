// Character offsets for byte-level BPE tokens. The browser tokenizer (transformers.js) returns token strings but no
// offsets, and the tagger needs to know which characters each token covers. Each byte-level token string maps back
// to its UTF-8 bytes (GPT-2's bytes_to_unicode table); walking them through the text gives the offsets.
import type { Offset } from "./tokens";

/** GPT-2's bytes_to_unicode, inverted: the printable character standing for each byte, back to the byte. */
const CHAR_TO_BYTE: Map<string, number> = (() => {
  const bytes: number[] = [];
  for (let b = 33; b <= 126; b++) bytes.push(b);
  for (let b = 161; b <= 172; b++) bytes.push(b);
  for (let b = 174; b <= 255; b++) bytes.push(b);
  const chars = [...bytes];
  let n = 0;
  for (let b = 0; b < 256; b++) {
    if (!bytes.includes(b)) {
      bytes.push(b);
      chars.push(256 + n++);
    }
  }
  return new Map(bytes.map((b, i) => [String.fromCodePoint(chars[i]!), b]));
})();

function byteLength(token: string): number {
  let n = 0;
  for (const ch of token) {
    if (!CHAR_TO_BYTE.has(ch)) throw new Error(`not a byte-level token: ${JSON.stringify(token)}`);
    n++;
  }
  return n;
}

/** Offsets in `text` (string indices) for each token; special tokens get [0, 0]. Throws if the tokens don't spell
 * the text byte for byte, which would mean a normalizer changed it and offsets can't be trusted. A token that ends
 * inside a multi-byte character covers that whole character, as Hugging Face tokenizers report it. */
export function byteLevelOffsets(text: string, tokens: string[], special: Set<string>): Offset[] {
  const utf8 = new TextEncoder().encode(text);
  // charAt[byte] = index in `text` of the character that byte belongs to.
  const charAt = new Int32Array(utf8.length + 1);
  let b = 0;
  for (let i = 0; i < text.length; i++) {
    const cp = text.codePointAt(i)!;
    const len = cp < 0x80 ? 1 : cp < 0x800 ? 2 : cp < 0x10000 ? 3 : 4;
    for (let k = 0; k < len; k++) charAt[b++] = i;
    if (cp > 0xffff) i++;
  }
  charAt[utf8.length] = text.length;

  const out: Offset[] = [];
  let pos = 0;
  for (const t of tokens) {
    if (special.has(t)) {
      out.push([0, 0]);
      continue;
    }
    const n = byteLength(t);
    for (const [k, ch] of [...t].entries()) {
      if (utf8[pos + k] !== CHAR_TO_BYTE.get(ch)) throw new Error(`token ${JSON.stringify(t)} does not match the text at byte ${pos + k}`);
    }
    const start = charAt[pos]!;
    const last = charAt[pos + n - 1]!;
    out.push([start, last + (text.codePointAt(last)! > 0xffff ? 2 : 1)]);
    pos += n;
  }
  if (pos !== utf8.length) throw new Error(`tokens cover ${pos} of ${utf8.length} bytes`);
  return out;
}
