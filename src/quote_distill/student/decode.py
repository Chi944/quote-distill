"""Turn the encoder tagger's output back into a schema label.

The tagger marks stretches of text with a field type (`supplier`, `line_items.quantity`, `discounts.amount`, ...)
and predicts two document-level classes that are never a stretch of text: the GST treatment, and whether numeric
dates are written month first (US) or day first. `decode` groups the
stretches into line items and discounts, turns each printed text into its schema value with the same tables the
generator and checker use, and recovers values that are printed inside another field (a currency symbol inside a
price, a rate inside "10% trade discount"). Anything unmarked is not_stated.
"""

import calendar
import re
from datetime import date, datetime
from decimal import Decimal

from ..checks import NUMBER, RELATIVE_END_OF_MONTH, number_in
from ..money import decimal_value, money_value, price_value
from ..normalise import CURRENCY_TOKENS, DATE_FORMATS, UNIT_BY_RAW, collapse, normalise_payment_terms

DOC_TAGS = ("supplier", "quote_number", "date", "currency", "subtotal", "total", "validity", "payment_terms",
            "gst.rate", "gst.amount")
LINE_TAGS = ("description", "quantity", "unit", "unit_price", "discount", "line_total")
DISCOUNT_TAGS = ("description", "rate", "amount")
TAGS = (*DOC_TAGS, *(f"line_items.{t}" for t in LINE_TAGS), *(f"discounts.{t}" for t in DISCOUNT_TAGS))
TREATMENTS = ("exclusive", "inclusive", "not_charged", "not_stated")
NS = {"state": "not_stated"}

# Longest first, so "NZ$" wins over a bare "$" and "Singapore dollars (S$)" over "S$".
_CURRENCY = sorted(CURRENCY_TOKENS, key=len, reverse=True)
_PERCENT = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def tag_of(path: str) -> str:
    """Field path ("$.line_items[2].quantity") to tag ("line_items.quantity")."""
    return re.sub(r"\[\d+\]", "", path[2:])


def _stated(value: str | None, raw: str) -> dict:
    return {"state": "stated", "value": value, "raw": raw} if value is not None else NS


def _number(raw: str) -> Decimal | None:
    n = number_in(raw)
    if n is not None and re.search(r"\(\s*[^)]*\d[^)]*\)", raw) and n > 0:
        n = -n  # accounting brackets for a credit
    return n


def _money(raw: str) -> str | None:
    n = _number(raw)
    return money_value(n) if n is not None else None


def _price(raw: str) -> str | None:
    n = _number(raw)
    return price_value(n) if n is not None else None


def _decimal(raw: str) -> str | None:
    n = number_in(raw)
    return decimal_value(n) if n is not None else None


def _currency_in(raw: str) -> str | None:
    for token in _CURRENCY:
        if re.search(rf"(?<![A-Za-z]){re.escape(token)}(?![A-Za-z])", raw):
            return token
    return None


def _date_formats(month_first: bool) -> list[str]:
    us = DATE_FORMATS["US"]
    rest = sorted({f for k, fs in DATE_FORMATS.items() if k != "US" for f in fs})
    return us + rest if month_first else rest + us


def parse_date(raw: str, month_first: bool) -> date | None:
    """First format that reads the whole raw text, or a date inside it ("Prices valid until 30/07/2026")."""
    text = collapse(raw)
    candidates = [text, *re.findall(r"[A-Za-z]{3}, \d{1,2} [A-Za-z]{3,9} \d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{4}"
                                    r"|\d{1,2} [A-Za-z]{3,9} \d{4}|[A-Za-z]{3,9} \d{1,2}, \d{4}", text)]
    for c in candidates:
        for fmt in _date_formats(month_first):
            try:
                return datetime.strptime(c, fmt).date()
            except ValueError:
                continue
    return None


def _validity(raw: str, quote_date: date | None, month_first: bool) -> str | None:
    if RELATIVE_END_OF_MONTH.search(raw):
        if quote_date is None:
            return None
        return quote_date.replace(day=calendar.monthrange(quote_date.year, quote_date.month)[1]).isoformat()
    days = re.search(r"(\d+)\s*days?", raw, re.IGNORECASE)
    if days:
        return f"P{int(days.group(1))}D"
    d = parse_date(raw, month_first)
    return d.isoformat() if d else None


def _line_start(text: str, pos: int) -> int:
    return text.rfind("\n", 0, pos) + 1


def _group(text: str, spans: list[tuple[int, int, str]], prefix: str) -> list[dict[str, tuple[int, int]]]:
    """Group a repeated object's spans: each description opens one, and every other span joins the description
    whose region holds it (from the description's line, or the description itself when items share a line)."""
    descs = sorted((s, e) for s, e, t in spans if t == f"{prefix}.description")
    starts, prev_end = [], 0
    for s, e in descs:
        line = _line_start(text, s)
        starts.append(line if line >= prev_end else s)
        prev_end = e
    groups = [{"description": d} for d in descs]
    for s, e, t in sorted(spans):
        if not t.startswith(prefix + ".") or t == f"{prefix}.description":
            continue
        k = max((i for i, st in enumerate(starts) if st <= s), default=None)
        if k is None:
            if not groups:
                groups.append({})
            k = 0
        groups[k].setdefault(t.split(".", 1)[1], (s, e))
    return groups


def decode(text: str, spans: list[tuple[int, int, str]], treatment: str, month_first: bool | None = None) -> dict:
    """spans: (start, end, tag) with tags from TAGS; treatment: one of TREATMENTS; month_first: the date-order
    class, or None to guess it from the currency (US dollars). Returns a schema label."""
    raw = {}
    for s, e, t in sorted(spans):
        if t in DOC_TAGS:
            raw.setdefault(t, text[s:e])

    money_raws = [text[s:e] for s, e, t in spans if t.endswith(("amount", "total", "subtotal", "unit_price"))]
    currency_raw = raw.get("currency") or next((c for c in map(_currency_in, money_raws) if c), None)
    currency = CURRENCY_TOKENS.get(currency_raw.strip()) if currency_raw else None
    if month_first is None:
        month_first = currency == "USD"

    quote_date = parse_date(raw["date"], month_first) if "date" in raw else None
    label = {
        "schema_version": "1.0.0",
        "supplier": _stated(collapse(raw["supplier"]), raw["supplier"]) if "supplier" in raw else NS,
        "quote_number": _stated(collapse(raw["quote_number"]), raw["quote_number"]) if "quote_number" in raw else NS,
        "date": _stated(quote_date.isoformat() if quote_date else None, raw.get("date", "")),
        "currency": _stated(currency, currency_raw or ""),
    }

    lines = []
    for g in _group(text, spans, "line_items"):
        r = {k: text[s:e] for k, (s, e) in g.items()}
        disc = NS
        if "discount" in r:
            pct = _PERCENT.search(r["discount"])
            disc = ({"state": "stated", "kind": "percent", "value": decimal_value(Decimal(pct.group(1))), "raw": r["discount"]}
                    if pct else {"state": "stated", "kind": "amount", "value": _money(r["discount"]), "raw": r["discount"]})
        lines.append({
            "description": _stated(collapse(r["description"]), r["description"]) if "description" in r else NS,
            "quantity": _stated(_decimal(r["quantity"]), r["quantity"]) if "quantity" in r else NS,
            "unit": _stated(UNIT_BY_RAW.get(r["unit"].strip().lower()), r["unit"]) if "unit" in r else NS,
            "unit_price": _stated(_price(r["unit_price"]), r["unit_price"]) if "unit_price" in r else NS,
            "discount": disc,
            "line_total": _stated(_money(r["line_total"]), r["line_total"]) if "line_total" in r else NS,
        })
    label["line_items"] = lines

    discounts = []
    for g in _group(text, spans, "discounts"):
        r = {k: text[s:e] for k, (s, e) in g.items()}
        desc = r.get("description", "")
        rate_raw = r.get("rate") or (m.group(0) if (m := _PERCENT.search(desc)) else None)
        discounts.append({
            "description": _stated(collapse(desc), desc) if desc else NS,
            "kind": "percent" if rate_raw else "amount",
            "rate": _stated(_decimal(rate_raw), rate_raw) if rate_raw else NS,
            "amount": _stated(_money(r["amount"]), r["amount"]) if "amount" in r else NS,
        })
    label["discounts"] = discounts

    gst_rate_raw = raw.get("gst.rate")
    if gst_rate_raw is None and treatment in ("exclusive", "inclusive"):
        # A rate printed inside a GST label ("GST 9%: 38.82", "include 10% GST") that the tagger can't mark alone.
        cue = re.search(r"(\d+(?:\.\d+)?%)\s*GST|GST[^\n\d]{0,20}?(\d+(?:\.\d+)?%)", text)
        gst_rate_raw = (cue.group(1) or cue.group(2)) if cue else None
    label["gst"] = {
        "treatment": treatment,
        "rate": _stated(_decimal(gst_rate_raw), gst_rate_raw) if gst_rate_raw else NS,
        "amount": _stated(_money(raw["gst.amount"]), raw["gst.amount"]) if "gst.amount" in raw else NS,
    }
    for k in ("subtotal", "total"):
        label[k] = _stated(_money(raw[k]), raw[k]) if k in raw else NS
    label["validity"] = (_stated(_validity(raw["validity"], quote_date, month_first), raw["validity"])
                         if "validity" in raw else NS)
    label["payment_terms"] = (_stated(normalise_payment_terms(raw["payment_terms"]), raw["payment_terms"])
                              if "payment_terms" in raw else NS)
    return label


__all__ = ["NUMBER", "TAGS", "TREATMENTS", "decode", "parse_date", "tag_of"]
