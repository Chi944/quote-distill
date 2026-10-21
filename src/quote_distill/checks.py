"""Deterministic label checks: schema, provenance, normalisation and arithmetic.

A label is kept only when it is schema-valid, every `raw` is a verbatim substring of its document,
every value re-derives from its `raw`, and its failed arithmetic checks equal its intended failures.
"""

import calendar
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

from .money import round_money
from .normalise import (
    CURRENCY_TOKENS,
    DATE_FORMATS,
    FREE_WORDS,
    NUMBER_WORDS,
    UNIT_BY_RAW,
    collapse,
    normalise_payment_terms,
)
from .schema import schema_errors

NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
NUMERIC_LEAVES = {"quantity", "unit_price", "line_total", "subtotal", "total", "amount", "rate"}
VERBATIM_LEAVES = {"supplier", "quote_number", "description"}
RELATIVE_END_OF_MONTH = re.compile(r"end of (this|the) month", re.IGNORECASE)


@dataclass
class CheckResult:
    keep: bool
    schema: list[str] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    passes: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    skips: list[str] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)


def stated(f: dict) -> bool:
    return f["state"] == "stated"


def dec(f: dict) -> Decimal:
    return Decimal(f["value"])


def render_date(d: date, fmt: str, pad: bool = True) -> str:
    """strftime with optional unpadded day and month, the way people actually write dates."""
    if not pad:
        fmt = fmt.replace("%d", str(d.day)).replace("%m", str(d.month))
    return d.strftime(fmt)


def date_spellings(d: date, locale: str | None) -> set[str]:
    formats = DATE_FORMATS[locale] if locale else sorted({f for fs in DATE_FORMATS.values() for f in fs})
    return {render_date(d, f, pad) for f in formats for pad in (True, False)}


def number_in(raw: str) -> Decimal | None:
    text = raw.strip().lower()
    if text in FREE_WORDS:
        return Decimal("0")
    if text in NUMBER_WORDS:
        return Decimal(NUMBER_WORDS[text])
    match = NUMBER.search(raw)
    return Decimal(match.group().replace(",", "")) if match else None


def iter_fields(node, path="$"):
    """Yield (path, field) for every field object in a label."""
    if isinstance(node, dict):
        if "state" in node:
            yield path, node
            return
        for key, value in node.items():
            yield from iter_fields(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from iter_fields(value, f"{path}[{i}]")


def check_provenance(label: dict, text: str, locale: str | None) -> tuple[list[str], list[str]]:
    problems, unverified = [], []
    collapsed_text = collapse(text)
    quote_date = date.fromisoformat(label["date"]["value"]) if stated(label["date"]) else None
    for path, f in iter_fields(label):
        if not stated(f):
            continue
        raw = f.get("raw")
        if raw is None:
            problems.append(f"{path}: gold label is missing raw")
            continue
        if raw not in text and collapse(raw) not in collapsed_text:
            problems.append(f"{path}: raw {raw!r} not found in document")
            continue
        value, leaf = f["value"], path.rsplit(".", 1)[-1]
        if leaf in VERBATIM_LEAVES:
            if value != collapse(raw):
                problems.append(f"{path}: value {value!r} is not raw with whitespace collapsed")
        elif leaf == "payment_terms":
            if value != normalise_payment_terms(raw):
                problems.append(f"{path}: value {value!r} is not normalised raw")
        elif leaf in NUMERIC_LEAVES or (leaf == "discount" and "kind" in f):
            found = number_in(raw)
            if found is None:
                unverified.append(f"{path}: no number in raw {raw!r}")
            elif Decimal(value) != found:
                problems.append(f"{path}: value {value} != number in raw {raw!r}")
        elif leaf == "unit":
            if UNIT_BY_RAW.get(raw.strip().lower()) != value:
                problems.append(f"{path}: unit {value!r} does not map from raw {raw!r}")
        elif leaf == "currency":
            if CURRENCY_TOKENS.get(raw.strip()) != value:
                problems.append(f"{path}: currency {value!r} does not map from raw {raw!r}")
        elif leaf == "date" or (leaf == "validity" and not value.startswith("P")):
            d = date.fromisoformat(value)
            if leaf == "validity" and RELATIVE_END_OF_MONTH.search(raw):
                if quote_date is None:
                    problems.append(f"{path}: relative validity without a stated quote date")
                elif d != quote_date.replace(day=calendar.monthrange(quote_date.year, quote_date.month)[1]):
                    problems.append(f"{path}: {value} is not the end of the quote month")
            elif not any(s in raw for s in date_spellings(d, locale)):
                problems.append(f"{path}: {value} is not written in raw {raw!r} in a {locale or 'known'} date format")
        elif leaf == "validity":
            days = value[1:-1]
            if not re.search(rf"(?<!\d){days}(?!\d)", raw) or "day" not in raw.lower():
                problems.append(f"{path}: {value} does not match raw {raw!r}")
        else:
            unverified.append(f"{path}: {leaf} mapping from raw {raw!r} not machine-checked")
    return problems, unverified


def check_arithmetic(label: dict) -> tuple[list[str], list[str], list[str]]:
    """Return (failures, passes, skips) using the canonical formulas in docs/schema.md."""
    failures, passes, skips = [], [], []

    def compare(name, expected, f):
        if stated(f):
            (passes if dec(f) == expected else failures).append(name)
        else:
            skips.append(name)

    lines = label["line_items"]
    for i, line in enumerate(lines):
        name = f"line[{i}].line_total"
        if not (stated(line["quantity"]) and stated(line["unit_price"])):
            skips.append(name)
            continue
        gross = round_money(dec(line["quantity"]) * dec(line["unit_price"]))
        disc = line["discount"]
        cut = Decimal("0")
        if stated(disc):
            rate_or_amount = Decimal(disc["value"])
            cut = round_money(gross * rate_or_amount / 100) if disc["kind"] == "percent" else rate_or_amount
        compare(name, gross - cut, line["line_total"])

    all_totals = all(stated(line["line_total"]) for line in lines)
    line_sum = sum((dec(line["line_total"]) for line in lines), Decimal("0")) if all_totals else None
    if line_sum is not None:
        compare("subtotal", line_sum, label["subtotal"])
    else:
        skips.append("subtotal")
    base = dec(label["subtotal"]) if stated(label["subtotal"]) else line_sum

    discount_total = Decimal("0")
    for i, d in enumerate(label["discounts"]):
        name = f"discounts[{i}].amount"
        if d["kind"] == "percent" and stated(d["rate"]) and base is not None:
            compare(name, round_money(base * dec(d["rate"]) / 100), d["amount"])
        else:
            skips.append(name)
        if stated(d["amount"]):
            discount_total += dec(d["amount"])
        elif base is not None and d["kind"] == "percent" and stated(d["rate"]):
            discount_total += round_money(base * dec(d["rate"]) / 100)
        else:
            base = None  # an unknown deduction makes everything below it uncheckable

    gst, total = label["gst"], label["total"]
    taxable = None if base is None else base - discount_total
    if gst["treatment"] == "exclusive" and stated(gst["rate"]) and taxable is not None:
        compare("gst.amount", round_money(taxable * dec(gst["rate"]) / 100), gst["amount"])
    elif gst["treatment"] == "inclusive" and stated(gst["rate"]) and stated(total):
        rate = dec(gst["rate"])
        compare("gst.amount", round_money(dec(total) * rate / (100 + rate)), gst["amount"])
    else:
        skips.append("gst.amount")

    if taxable is None or (gst["treatment"] == "exclusive" and not stated(gst["amount"])):
        skips.append("total")
    else:
        added = dec(gst["amount"]) if gst["treatment"] == "exclusive" else Decimal("0")
        compare("total", taxable + added, total)
    return failures, passes, skips


def check_label(label: dict, text: str, locale: str | None = None, expected_failures: list[str] | None = None) -> CheckResult:
    schema = schema_errors(label)
    if schema:
        return CheckResult(keep=False, schema=schema)
    provenance, unverified = check_provenance(label, text, locale)
    failures, passes, skips = check_arithmetic(label)
    unexpected = sorted(set(failures) ^ set(expected_failures or []))
    keep = not provenance and not unexpected
    return CheckResult(keep, schema, provenance, unverified, passes, failures, skips, unexpected)


def check_seeds(seeds_dir: Path) -> int:
    manifest = json.loads((seeds_dir / "manifest.json").read_text(encoding="utf-8"))
    kept = 0
    for entry in manifest["seeds"]:
        sid = entry["id"]
        label = json.loads((seeds_dir / f"{sid}.label.json").read_text(encoding="utf-8"))
        text = (seeds_dir / f"{sid}.doc.txt").read_text(encoding="utf-8")
        r = check_label(label, text, entry.get("locale"), entry["expected_check_failures"])
        kept += r.keep
        print(f"{sid}: {'KEEP' if r.keep else 'REJECT'}  arithmetic {len(r.passes)} pass / {len(r.failures)} fail / "
              f"{len(r.skips)} skipped; intended failures {entry['expected_check_failures'] or 'none'}")
        for line in r.schema + r.provenance + [f"unexpected arithmetic result: {u}" for u in r.unexpected]:
            print("   !", line)
        for line in r.unverified:
            print("   ~", line)
    print(f"{kept}/{len(manifest['seeds'])} seeds kept")
    return 0 if kept == len(manifest["seeds"]) else 1


if __name__ == "__main__":
    sys.exit(check_seeds(Path(sys.argv[1] if len(sys.argv) > 1 else "data/seeds")))
