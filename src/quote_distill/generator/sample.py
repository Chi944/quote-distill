"""Sample one synthetic quotation: canonical values, their printed surface forms, and the gold label.

Values are decided first and computed with the canonical arithmetic (docs/schema.md). Surface strings
(`*_raw`) are decided here too, so every layout prints exactly the strings the label points at.
"""

import calendar
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal as D

from ..checks import render_date
from ..money import decimal_value, grouped, is_half_cent_tie, money_value, price_value, round_money
from ..normalise import DATE_FORMATS, NUMBER_WORDS, UNIT_SYNONYMS, collapse, normalise_payment_terms
from .vocab import CUSTOMERS, HEADER_TYPOS, ITEMS, LOCALES, LUMP_SUMS, NAME_FIRST, NAME_SECOND, PAYMENT_TERMS

LAYOUTS = ["fixed_table", "pipe_table", "item_blocks", "email_list", "prose_email"]
TABLE_LAYOUTS = {"fixed_table", "pipe_table", "item_blocks"}
NUMBER_NAMES = {v: k for k, v in NUMBER_WORDS.items()}


@dataclass
class Line:
    desc: str
    code: str | None = None
    qty: D | None = None
    qty_raw: str | None = None
    unit: str | None = None
    unit_raw: str | None = None
    price: D | None = None
    price_raw: str | None = None
    disc_kind: str | None = None
    disc_value: D | None = None
    disc_raw: str | None = None
    total: D = D("0")
    total_raw: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Quote:
    doc_id: str
    locale: str
    layout: str
    supplier: str
    address: str
    customer: str
    customer_ref: str | None
    quote_no: str | None
    date: date | None
    date_raw: str | None
    currency_raw: str | None
    currency_line: str | None
    prefix: str
    group: bool
    lines: list[Line]
    discounts: list[dict]
    gst: dict
    subtotal: D
    subtotal_raw: str | None
    total: D
    total_raw: str | None
    validity_value: str | None
    validity_raw: str | None
    payment_raw: str | None
    typos: dict[str, str]
    features: set[str]
    expected_failures: list[str]

    def h(self, word: str) -> str:
        """A header word, possibly with this document's typo."""
        return self.typos.get(word, word)


def fmt_amount(x: D, prefix: str, group: bool, places: int = 2) -> str:
    number = grouped(abs(x), places) if group else f"{abs(x):.{places}f}"
    return f"-{number}" if x < 0 else f"{prefix}{number}"


def fmt_price(x: D, prefix: str, group: bool) -> str:
    places = max(2, len(price_value(x).split(".")[1]))
    return fmt_amount(x, prefix, group, places)


def _typo(rng: random.Random, word: str) -> str:
    i = rng.randrange(1, len(word) - 2)
    return word[:i] + word[i + 1] + word[i] + word[i + 2:]


def _description_with_typo(rng: random.Random, desc: str) -> str:
    words = desc.split(" ")
    candidates = [i for i, w in enumerate(words) if w.isalpha() and len(w) >= 6]
    if not candidates:
        return desc
    i = rng.choice(candidates)
    words[i] = _typo(rng, words[i])
    return " ".join(words)


def _money_between(rng: random.Random, lo: str, hi: str) -> D:
    lo_c, hi_c = int(D(lo) * 100), int(D(hi) * 100)
    return D(rng.randint(lo_c, hi_c)) / 100


def _quantity(rng: random.Random, decimal_ok: bool, max_qty: int) -> D:
    if decimal_ok and rng.random() < 0.5:
        step = rng.choice([D("0.5"), D("0.25"), D("0.1")])
        return step * rng.randint(1, int(max_qty / step))
    return D(rng.randint(1, max_qty))


def sample_quote(rng: random.Random, doc_id: str) -> Quote:
    locale = rng.choice(list(LOCALES))
    loc = LOCALES[locale]
    layout = rng.choices(LAYOUTS, weights=[3, 3, 2, 2, 2])[0]
    table = layout in TABLE_LAYOUTS
    features: set[str] = {f"layout:{layout}", f"locale:{locale}"}

    supplier = f"{rng.choice(NAME_FIRST)} {rng.choice(NAME_SECOND)} {rng.choice(loc['suffixes'])}"
    if rng.random() < 0.3:
        supplier = supplier.upper()
    typos = {}
    if rng.random() < 0.3:
        for word in rng.sample(list(HEADER_TYPOS), k=3):
            typos[word] = rng.choice(HEADER_TYPOS[word])
        features.add("header_typos")

    # Currency: stated through a code/name line or a prefixed symbol, or left as a bare "$".
    group = rng.random() < 0.7
    currency_raw = currency_line = None
    if locale in {"SG", "AU", "NZ", "US"} and rng.random() < 0.2:
        prefix = rng.choice(["$", ""])
        features.add("bare_dollar")
    elif rng.random() < 0.5:
        currency_raw = rng.choice(loc["tokens"])
        currency_line = rng.choice(["All prices in {}.", "Currency: {}", "Amounts are in {}."]).format(currency_raw)
        prefix = rng.choice(["$", ""]) if locale != "MY" else rng.choice(["RM", ""])
    else:
        prefix = {"SG": "S$", "AU": "A$", "NZ": "NZ$", "MY": "RM", "US": "US$"}[locale]
        currency_raw = prefix
        prefix = prefix + rng.choice(["", " "])

    # Lines.
    max_lines = 4 if layout == "prose_email" else 5 if layout == "email_list" else 12
    n_lines = min(max_lines, rng.choices(range(1, 13), weights=[6, 10, 12, 12, 10, 8, 6, 4, 3, 2, 2, 2])[0])
    lines: list[Line] = []
    lump_sums = credits = 0
    used: set[str] = set()
    for _ in range(n_lines):
        r = rng.random()
        if r < 0.12 and lump_sums < 2:
            lump_sums += 1
            desc = rng.choice([d for d in LUMP_SUMS if d not in used])
            used.add(desc)
            unit_raw = rng.choice(["L/S", "lump sum", "lot"]) if table else "flat"
            amount = D(rng.randint(4, 120)) * 5
            line = Line(desc=desc, unit="lot", unit_raw=unit_raw, total=amount, tags={"lump_sum"})
            lines.append(line)
            continue
        desc, unit, lo, hi, decimal_ok, max_qty = rng.choice([it for it in ITEMS if it[0] not in used])
        used.add(desc)
        if rng.random() < 0.08:
            desc = _description_with_typo(rng, desc)
            features.add("description_typo")
        qty = _quantity(rng, decimal_ok, max_qty)
        price = _money_between(rng, lo, hi)
        line = Line(desc=desc, qty=qty, unit=unit, price=price)
        if price < 1 and rng.random() < 0.5:
            line.price = price + D(rng.choice([1, 5])) / 1000
            line.tags.add("sub_cent_price")
        if table and rng.random() < 0.15:
            line.code = f"{rng.choice('ABCDEFGHKMNRTX')}{rng.choice('ABCDEFGHKMNRTX')}{rng.randint(100, 999)}"
        if table and rng.random() < 0.04:
            line.price = D("0")
            line.price_raw = rng.choice(["FOC", "Free", "N/C"])
            line.tags.add("foc")
        elif table and credits == 0 and rng.random() < 0.03:
            credits += 1
            line.desc = f"Credit: return of {desc.split(',')[0].lower()}"
            line.price = -line.price
            line.tags.add("credit")
        if not table and qty == int(qty) and int(qty) in NUMBER_NAMES and rng.random() < 0.4:
            line.qty_raw = NUMBER_NAMES[int(qty)]
            line.tags.add("qty_in_words")
        else:
            line.qty_raw = decimal_value(qty) if rng.random() < 0.8 or qty != int(qty) else f"{qty:.2f}"
        if qty != int(qty):
            line.tags.add("decimal_qty")
        gross = round_money(line.qty * line.price)
        if "foc" not in line.tags and "credit" not in line.tags and rng.random() < 0.12:
            if rng.random() < 0.6:
                line.disc_kind, line.disc_value = "percent", rng.choice([D("5"), D("10"), D("12.5"), D("15")])
                line.disc_raw = f"{decimal_value(line.disc_value)}%"
                cut = round_money(gross * line.disc_value / 100)
                line.tags.add("line_discount_percent")
            else:
                line.disc_kind, line.disc_value = "amount", min(rng.choice([D("5"), D("10"), D("20"), D("50")]), gross / 2).quantize(D("1"))
                if line.disc_value <= 0:
                    line.disc_kind = line.disc_value = None
                    cut = D("0")
                else:
                    line.disc_raw = fmt_amount(line.disc_value, prefix, group)
                    cut = line.disc_value
                    line.tags.add("line_discount_amount")
        else:
            cut = D("0")
        line.total = gross - cut
        lines.append(line)

    if not any(l.qty is not None for l in lines):  # noqa: E741
        features.add("all_lump_sum")

    # Supplier arithmetic error on one checkable line, kept as printed.
    expected_failures: list[str] = []
    checkable = [i for i, l in enumerate(lines) if l.qty is not None and l.total >= 10 and not ({"foc", "credit"} & l.tags)]  # noqa: E741
    if checkable and rng.random() < 0.06:
        i = rng.choice(checkable)
        lines[i].total += rng.choice([D("1.00"), D("-1.00"), D("10.00"), D("0.10"), D("-0.10")])
        lines[i].tags.add("supplier_error")
        expected_failures.append(f"line[{i}].line_total")
        features.add("supplier_error")

    for line in lines:
        line.total_raw = fmt_amount(line.total, prefix, group)
        if line.qty is not None and line.price_raw is None:
            line.price_raw = fmt_price(line.price, prefix, group)
        if line.unit and line.unit_raw is None:
            options = UNIT_SYNONYMS[line.unit]
            line.unit_raw = rng.choice([o for o in options if o not in {"l/s", "flat"}] or options)
            if line.unit_raw in {"l", "lot"} and table:
                line.unit_raw = line.unit_raw.upper() if line.unit_raw == "l" else line.unit_raw
        features |= {f"line:{t}" for t in line.tags}

    subtotal = sum((l.total for l in lines), D("0"))  # noqa: E741

    # Document-level discount.
    discounts = []
    if subtotal > 50 and rng.random() < 0.2:
        if rng.random() < 0.7:
            rate = rng.choice([D("2.5"), D("5"), D("7.5"), D("10")])
            exact = subtotal * rate / 100
            amount = round_money(exact)
            if is_half_cent_tie(exact):
                features.add("half_cent_tie")
            desc = rng.choice(["{}% trade discount", "Less {}% project discount", "Discount {}%"]).format(decimal_value(rate))
            discounts.append({"kind": "percent", "rate": rate, "rate_raw": f"{decimal_value(rate)}%", "amount": amount,
                              "desc": desc, "amount_printed": rng.random() < 0.85})
        else:
            amount = min(D(rng.choice([20, 50, 100, 150])), (subtotal / 4).quantize(D("1")))
            discounts.append({"kind": "amount", "rate": None, "rate_raw": None, "amount": amount,
                              "desc": rng.choice(["Loyalty discount", "Less special discount", "Discount"]), "amount_printed": True})
        d = discounts[0]
        d["amount_raw"] = fmt_amount(d["amount"], prefix, group) if d["amount_printed"] else None
        features.add("doc_discount" if d["amount_printed"] else "doc_discount_amount_unprinted")
    taxable = subtotal - sum((d["amount"] for d in discounts), D("0"))

    # GST.
    if loc["gst"] is not None:
        treatment = rng.choices(["exclusive", "inclusive", "not_charged", "not_stated"], weights=[50, 25, 5, 20])[0]
    elif locale == "MY":
        treatment = rng.choices(["not_stated", "not_charged"], weights=[85, 15])[0]
    else:
        treatment = rng.choices(["not_charged", "not_stated"], weights=[60, 40])[0]
    gst = {"treatment": treatment, "rate": None, "rate_raw": None, "amount": None, "amount_raw": None, "phrase": None}
    total_printed = rng.random() < 0.92
    if treatment in {"exclusive", "inclusive"}:
        rate = loc["gst"]
        gst["rate"] = rate
        gst["rate_raw"] = f"{decimal_value(rate)}%" if rng.random() < 0.9 else None
        if treatment == "exclusive":
            exact = taxable * rate / 100
            gst["amount"] = round_money(exact)
            if is_half_cent_tie(exact):
                features.add("half_cent_tie")
            total = taxable + gst["amount"]
            if rng.random() < 0.2:
                total_printed = False
                features.add("gst_plus_unpriced")
            else:
                gst["amount_raw"] = fmt_amount(gst["amount"], prefix, group)
        else:
            total = taxable
            exact = total * rate / (100 + rate)
            gst["amount"] = round_money(exact)
            if rng.random() < 0.6:
                gst["amount_raw"] = fmt_amount(gst["amount"], prefix, group)
    else:
        total = taxable
        if treatment == "not_charged":
            gst["phrase"] = {"MY": "Tax: Nil (not applicable)", "US": "GST/VAT: Not applicable (export)"}.get(
                locale, rng.choice(["GST: Not applicable (supplier not GST-registered)", "No GST charged (zero-rated export)"]))
    features.add(f"gst:{treatment}")
    if gst["rate"] is not None and gst["rate_raw"] is None:
        features.add("gst_rate_unprinted")

    subtotal_printed = rng.random() < 0.8 or bool(discounts) and rng.random() < 0.5
    if layout == "prose_email" and treatment == "exclusive" and not total_printed:
        subtotal_printed = True
    if not subtotal_printed:
        features.add("missing:subtotal")
    if not total_printed:
        features.add("missing:total")

    # Header fields.
    quote_date = date(2026, 1, 1) + timedelta(days=rng.randrange(365)) if rng.random() < 0.9 else None
    date_raw = None
    if quote_date is not None:
        date_raw = render_date(quote_date, rng.choice(DATE_FORMATS[locale][:3]), pad=rng.random() < 0.6)
    else:
        features.add("missing:date")
    quote_no = None
    if rng.random() < 0.88:
        yy = (quote_date or date(2026, 6, 1)).strftime("%y")
        code = "".join(w[0] for w in supplier.split()[:2]).upper()
        quote_no = rng.choice([f"{code}-Q-{yy}-{rng.randint(1, 9999):04d}", f"Q{yy}/{rng.randint(1, 9999):04d}",
                               f"{code}{rng.randint(10000, 99999)}", f"{code}-{yy}{rng.randint(1, 12):02d}-{rng.randint(1, 999):03d}"])
    else:
        features.add("missing:quote_number")
    customer_ref = None
    if rng.random() < 0.5:
        customer_ref = rng.choice([f"PO-{rng.randint(1000, 9999)}", f"Enquiry {rng.randint(100, 9999)}", f"RFQ-{rng.randint(10, 999)}"])
        features.add("customer_ref_decoy")

    # Validity.
    validity_value = validity_raw = None
    r = rng.random()
    if r < 0.45:
        n = rng.choice([7, 14, 30, 45, 60, 90])
        validity_value = f"P{n}D"
        validity_raw = rng.choice([f"Valid for {n} days", f"Validity: {n} days", f"This quotation is valid for {n} days"])
        if "Validity" in validity_raw:
            validity_raw = validity_raw.replace("Validity", q_h(typos, "Validity"))
    elif r < 0.7:
        until = (quote_date or date(2026, 6, 1)) + timedelta(days=rng.randint(7, 60))
        validity_value = until.isoformat()
        validity_raw = f"Prices valid until {render_date(until, rng.choice(DATE_FORMATS[locale][:3]), pad=rng.random() < 0.6)}"
    elif r < 0.82 and quote_date is not None:
        last = quote_date.replace(day=calendar.monthrange(quote_date.year, quote_date.month)[1])
        validity_value = last.isoformat()
        validity_raw = rng.choice(["Pricing holds until the end of this month", "Valid until end of the month"])
        features.add("relative_validity")
    else:
        features.add("missing:validity")

    payment_raw = None
    if rng.random() < 0.8:
        payment_raw = rng.choice(PAYMENT_TERMS)
        if rng.random() < 0.15:
            payment_raw += f"; {rng.choice(['2', '2.5', '3'])}% discount if paid within {rng.choice([7, 10, 14])} days"
            features.add("conditional_discount")
    else:
        features.add("missing:payment_terms")

    return Quote(
        doc_id=doc_id, locale=locale, layout=layout, supplier=supplier, address=rng.choice(loc["places"]),
        customer=rng.choice(CUSTOMERS), customer_ref=customer_ref, quote_no=quote_no, date=quote_date, date_raw=date_raw,
        currency_raw=currency_raw, currency_line=currency_line, prefix=prefix, group=group, lines=lines, discounts=discounts,
        gst=gst, subtotal=subtotal, subtotal_raw=fmt_amount(subtotal, prefix, group) if subtotal_printed else None,
        total=total, total_raw=fmt_amount(total, prefix, group) if total_printed else None,
        validity_value=validity_value, validity_raw=validity_raw, payment_raw=payment_raw, typos=typos,
        features=features, expected_failures=expected_failures,
    )


def q_h(typos: dict[str, str], word: str) -> str:
    return typos.get(word, word)


# ---------- gold label ----------

NS = {"state": "not_stated"}


def _s(value: str, raw: str) -> dict:
    return {"state": "stated", "value": value, "raw": raw}


def to_label(q: Quote) -> dict:
    lines = []
    for line in q.lines:
        lines.append({
            "description": _s(collapse(line.desc), line.desc),
            "quantity": _s(decimal_value(line.qty), line.qty_raw) if line.qty is not None else NS,
            "unit": _s(line.unit, line.unit_raw) if line.unit else NS,
            "unit_price": _s(price_value(line.price), line.price_raw) if line.qty is not None else NS,
            "discount": ({"state": "stated", "kind": line.disc_kind,
                          "value": decimal_value(line.disc_value) if line.disc_kind == "percent" else money_value(line.disc_value),
                          "raw": line.disc_raw} if line.disc_kind else NS),
            "line_total": _s(money_value(line.total), line.total_raw),
        })
    discounts = [{
        "description": _s(collapse(d["desc"]), d["desc"]),
        "kind": d["kind"],
        "rate": _s(decimal_value(d["rate"]), d["rate_raw"]) if d["kind"] == "percent" else NS,
        "amount": _s(money_value(d["amount"]), d["amount_raw"]) if d["amount_raw"] else NS,
    } for d in q.discounts]
    gst = q.gst
    return {
        "schema_version": "1.0.0",
        "supplier": _s(collapse(q.supplier), q.supplier),
        "quote_number": _s(q.quote_no, q.quote_no) if q.quote_no else NS,
        "date": _s(q.date.isoformat(), q.date_raw) if q.date else NS,
        "currency": _s(LOCALES[q.locale]["currency"], q.currency_raw) if q.currency_raw else NS,
        "line_items": lines,
        "discounts": discounts,
        "gst": {
            "treatment": gst["treatment"],
            "rate": _s(decimal_value(gst["rate"]), gst["rate_raw"]) if gst["rate_raw"] else NS,
            "amount": _s(money_value(gst["amount"]), gst["amount_raw"]) if gst["amount_raw"] else NS,
        },
        "subtotal": _s(money_value(q.subtotal), q.subtotal_raw) if q.subtotal_raw else NS,
        "total": _s(money_value(q.total), q.total_raw) if q.total_raw else NS,
        "validity": _s(q.validity_value, q.validity_raw) if q.validity_value else NS,
        "payment_terms": _s(normalise_payment_terms(q.payment_raw), q.payment_raw) if q.payment_raw else NS,
    }
