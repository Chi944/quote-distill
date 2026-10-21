// Exact decimals for money, as Python's Decimal is used in src/quote_distill/money.py. No floats anywhere.

export class Dec {
  constructor(
    readonly int: bigint,
    readonly scale: number,
  ) {}

  static parse(text: string): Dec {
    const m = /^([+-]?)(\d*)(?:\.(\d*))?$/.exec(text.trim());
    if (!m || (m[2] === "" && (m[3] ?? "") === "")) throw new Error(`not a decimal: ${text}`);
    const frac = m[3] ?? "";
    const digits = BigInt((m[2] || "0") + frac);
    return new Dec(m[1] === "-" ? -digits : digits, frac.length);
  }

  static of(n: number): Dec {
    return Dec.parse(String(n));
  }

  private rescaled(scale: number): bigint {
    return this.int * 10n ** BigInt(scale - this.scale);
  }

  add(o: Dec): Dec {
    const s = Math.max(this.scale, o.scale);
    return new Dec(this.rescaled(s) + o.rescaled(s), s);
  }

  sub(o: Dec): Dec {
    return this.add(o.neg());
  }

  mul(o: Dec): Dec {
    return new Dec(this.int * o.int, this.scale + o.scale);
  }

  neg(): Dec {
    return new Dec(-this.int, this.scale);
  }

  cmp(o: Dec): number {
    const s = Math.max(this.scale, o.scale);
    const a = this.rescaled(s);
    const b = o.rescaled(s);
    return a < b ? -1 : a > b ? 1 : 0;
  }

  eq(o: Dec): boolean {
    return this.cmp(o) === 0;
  }

  /** this / o, rounded half away from zero (Python's ROUND_HALF_UP) to `places` decimals. */
  divRound(o: Dec, places: number): Dec {
    if (o.int === 0n) throw new Error("division by zero");
    // this / o = (this.int * 10^o.scale) / (o.int * 10^this.scale); scale the numerator up by `places`.
    let num = this.int * 10n ** BigInt(o.scale + places);
    let den = o.int * 10n ** BigInt(this.scale);
    if (den < 0n) {
      num = -num;
      den = -den;
    }
    const neg = num < 0n;
    const a = neg ? -num : num;
    let q = a / den;
    if (2n * (a % den) >= den) q += 1n;
    return new Dec(neg ? -q : q, places);
  }

  /** Python's quantize(Decimal(10) ** -places, ROUND_HALF_UP). */
  roundHalfUp(places: number): Dec {
    return this.divRound(new Dec(1n, 0), places);
  }

  /** Python's f"{x:f}": every stored digit, no exponent. */
  toPlain(): string {
    const neg = this.int < 0n;
    let digits = (neg ? -this.int : this.int).toString();
    if (this.scale <= 0) return (neg ? "-" : "") + digits + "0".repeat(-this.scale);
    digits = digits.padStart(this.scale + 1, "0");
    const cut = digits.length - this.scale;
    return `${neg ? "-" : ""}${digits.slice(0, cut)}.${digits.slice(cut)}`;
  }

  /** Python's f"{x:.{places}f}" on a Decimal, which rounds half to even. */
  toFixedHalfEven(places: number): string {
    if (this.scale <= places) return new Dec(this.rescaled(places), places).toPlain();
    const div = 10n ** BigInt(this.scale - places);
    const neg = this.int < 0n;
    const a = neg ? -this.int : this.int;
    let q = a / div;
    const r2 = 2n * (a % div);
    if (r2 > div || (r2 === div && q % 2n === 1n)) q += 1n;
    return new Dec(neg ? -q : q, places).toPlain();
  }
}

export const HUNDRED = new Dec(100n, 0);

/** money.round_money: half-up to cents. */
export function roundMoney(x: Dec): Dec {
  return x.roundHalfUp(2);
}

/** money.money_value: exactly two decimals, no separators. */
export function moneyValue(x: Dec): string {
  return roundMoney(x).toPlain();
}

/** money.price_value: two to four decimals, trailing zeros beyond two removed. */
export function priceValue(x: Dec): string {
  const [whole, frac = ""] = x.toFixedHalfEven(4).split(".");
  return `${whole}.${frac.replace(/0+$/, "").padEnd(2, "0")}`;
}

/** money.decimal_value: no trailing zeros, no exponent. */
export function decimalValue(x: Dec): string {
  let text = x.toPlain();
  if (text.includes(".")) text = text.replace(/0+$/, "").replace(/\.$/, "");
  return text;
}
