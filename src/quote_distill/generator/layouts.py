"""Render a sampled Quote as document text. Layouts only arrange the surface strings chosen in sample.py."""

import random

from .sample import Quote


def _header_block(q: Quote, rng: random.Random) -> list[str]:
    out = [q.supplier, q.address, ""]
    title = q.h("Quotation").upper() if rng.random() < 0.5 else q.h("Quotation")
    meta = []
    if q.quote_no:
        meta.append(f"{rng.choice([q.h('Quotation') + ' No.:', 'Quote #', 'Quote No:', 'Our quote:'])} {q.quote_no}")
    if q.date_raw:
        meta.append(f"Date: {q.date_raw}")
    out.append(title)
    out.extend(meta)
    out.append(f"To: {q.customer}")
    if q.customer_ref:
        out.append(f"Your ref: {q.customer_ref}")
    if q.currency_line:
        out.append(q.currency_line)
    if q.gst["treatment"] == "inclusive":
        rate = f" {q.gst['rate_raw']}" if q.gst["rate_raw"] else ""
        out.append(f"All prices include{rate} GST.")
    out.append("")
    return out


def _footer_rows(q: Quote) -> list[tuple[str, str]]:
    """(label, printed amount) rows below the item table, in canonical order."""
    rows = []
    if q.subtotal_raw:
        rows.append((q.h("Subtotal"), q.subtotal_raw))
    for d in q.discounts:
        rows.append((d["desc"], d["amount_raw"] or ""))
    g = q.gst
    if g["treatment"] == "exclusive":
        if g["amount_raw"]:
            rows.append((f"GST {g['rate_raw']}" if g["rate_raw"] else "GST", g["amount_raw"]))
        else:
            rows.append((f"Plus GST {g['rate_raw']}" if g["rate_raw"] else "Plus GST", ""))
    if q.total_raw:
        label = q.h("Total")
        if g["treatment"] == "exclusive":
            label += " incl. GST"
        elif g["treatment"] == "inclusive":
            label += " (GST inclusive)"
        rows.append((label, q.total_raw))
    if g["treatment"] == "inclusive" and g["amount_raw"]:
        rows.append((f"GST included @ {g['rate_raw']}" if g["rate_raw"] else "GST included", g["amount_raw"]))
    if g["phrase"]:
        rows.append((g["phrase"], ""))
    return rows


def _terms(q: Quote) -> list[str]:
    out = []
    if q.validity_raw:
        out.append(f"{q.validity_raw}.")
    if q.payment_raw:
        out.append(f"{q.h('Payment')} terms: {q.payment_raw}.")
    return out


def _disc_cell(line) -> str:
    return line.disc_raw or ""


def fixed_table(q: Quote, rng: random.Random) -> str:
    out = _header_block(q, rng)
    show_code = any(l.code for l in q.lines)  # noqa: E741
    cols = ["No.", *(["Code"] if show_code else []), q.h("Description"), "Qty", "Unit", "Unit Price", q.h("Discount"), "Amount"]
    rows = []
    for i, line in enumerate(q.lines, 1):
        rows.append([str(i), *([line.code or ""] if show_code else []), line.desc, line.qty_raw or "", line.unit_raw or "",
                     line.price_raw or "", _disc_cell(line), line.total_raw])
    widths = [max(len(r[c]) for r in [cols, *rows]) for c in range(len(cols))]
    def fmt(row: list[str]) -> str:
        cells = zip(row, widths, strict=True)
        return "  ".join(cell.ljust(w) if c < len(cols) - 5 else cell.rjust(w) for c, (cell, w) in enumerate(cells))

    out.append(fmt(cols))
    out.extend(fmt(r) for r in rows)
    out.append("-" * len(fmt(cols)))
    width = len(fmt(cols))
    for label, amount in _footer_rows(q):
        out.append(f"{label}  {amount}".rjust(width) if amount else label.rjust(width))
    out.append("")
    out.extend(_terms(q))
    return "\n".join(out) + "\n"


def pipe_table(q: Quote, rng: random.Random) -> str:
    out = _header_block(q, rng)
    show_code = any(l.code for l in q.lines)  # noqa: E741
    code_head, code_rule = ("Code | ", "---|") if show_code else ("", "")
    out.append(f"| # | {code_head}{q.h('Description')} | Qty | UoM | Rate | Disc | Ext |")
    out.append(f"|---|{code_rule}---|---|---|---|---|---|")
    for i, line in enumerate(q.lines, 1):
        code = f"{line.code or ''} | " if show_code else ""
        out.append(f"| {i} | {code}{line.desc} | {line.qty_raw or ''} | {line.unit_raw or ''} | {line.price_raw or ''} "
                   f"| {_disc_cell(line)} | {line.total_raw} |")
    out.append("")
    for label, amount in _footer_rows(q):
        out.append(f"{label}: {amount}" if amount else label)
    out.append("")
    out.extend(_terms(q))
    return "\n".join(out) + "\n"


def item_blocks(q: Quote, rng: random.Random) -> str:
    out = _header_block(q, rng)
    for i, line in enumerate(q.lines, 1):
        out.append(f"Item {i}: {line.desc}")
        if line.code:
            out.append(f"  Part no.: {line.code}")
        if line.qty_raw:
            out.append(f"  {q.h('Quantity')}: {line.qty_raw} {line.unit_raw}")
        elif line.unit_raw:
            out.append(f"  Basis: {line.unit_raw}")
        if line.price_raw:
            out.append(f"  Unit price: {line.price_raw}")
        if line.disc_raw:
            out.append(f"  {q.h('Discount')}: {line.disc_raw}")
        out.append(f"  Line total: {line.total_raw}")
        out.append("")
    for label, amount in _footer_rows(q):
        out.append(f"{label} {amount}".rstrip())
    out.append("")
    out.extend(_terms(q))
    return "\n".join(out) + "\n"


def _salutation(q: Quote, rng: random.Random) -> list[str]:
    out = [f"From: sales@{q.supplier.split()[0].lower()}.example"]
    if q.date_raw:
        out.append(f"Date: {q.date_raw}")
    subject = "Re: your enquiry" + (f" {q.customer_ref}" if q.customer_ref else "")
    out += [f"Subject: {subject}", "", rng.choice(["Hi,", "Dear Sir/Madam,", "Hello,"]), ""]
    if q.quote_no:
        out.append(f"Our quote number is {q.quote_no}.")
    if q.currency_line:
        out.append(q.currency_line)
    if q.gst["treatment"] == "inclusive":
        out.append(f"Prices below include {q.gst['rate_raw'] + ' ' if q.gst['rate_raw'] else ''}GST.")
    return out


def _sign_off(q: Quote, rng: random.Random) -> list[str]:
    return ["", rng.choice(["Regards,", "Cheers,", "Thanks,"]), rng.choice(["Lim", "Aroha", "Sam", "Priya", "Tom"]), q.supplier]


def email_list(q: Quote, rng: random.Random) -> str:
    out = _salutation(q, rng)
    out.append("Please see our price for the below:")
    out.append("")
    for line in q.lines:
        if line.qty_raw:
            disc = f" less {line.disc_raw}" if line.disc_raw else ""
            out.append(f"  - {line.desc}   {line.qty_raw} {line.unit_raw} x {line.price_raw}{disc} = {line.total_raw}")
        else:
            out.append(f"  - {line.desc}   {line.unit_raw} {line.total_raw}")
    out.append("")
    for label, amount in _footer_rows(q):
        out.append(f"  {label}: {amount}" if amount else f"  {label}")
    out.append("")
    out.extend(_terms(q))
    out.extend(_sign_off(q, rng))
    return "\n".join(out) + "\n"


def prose_email(q: Quote, rng: random.Random) -> str:
    out = _salutation(q, rng)
    sentences = []
    for line in q.lines:
        if line.qty_raw:
            disc = f", less {line.disc_raw}," if line.disc_raw else ""
            sentences.append(f"For {line.desc} you'd need {line.qty_raw} {line.unit_raw} at {line.price_raw} each{disc} "
                             f"which comes to {line.total_raw}.")
        else:
            sentences.append(f"{line.desc} is a {line.unit_raw} {line.total_raw}.")
    out.append(" ".join(sentences))
    g = q.gst
    tail = []
    if q.subtotal_raw:
        tail.append(f"That's {q.subtotal_raw} all up" + (" before discount." if q.discounts else "."))
    for d in q.discounts:
        tail.append(f"{d['desc']} applies" + (f", which takes off {d['amount_raw']}." if d["amount_raw"] else "."))
    if g["treatment"] == "exclusive":
        rate = f" at {g['rate_raw']}" if g["rate_raw"] else ""
        tail.append(f"GST{rate} comes to {g['amount_raw']}." if g["amount_raw"] else f"Plus GST{rate}.")
    if q.total_raw:
        suffix = {"exclusive": " including GST", "inclusive": " including GST"}.get(g["treatment"], "")
        tail.append(f"The total is {q.total_raw}{suffix}.")
    if g["treatment"] == "inclusive" and g["amount_raw"]:
        tail.append(f"That includes {g['amount_raw']} GST.")
    if g["phrase"]:
        tail.append(f"{g['phrase']}.")
    out += ["", " ".join(tail), ""]
    out.append(" ".join(_terms(q)))
    out.extend(_sign_off(q, rng))
    return "\n".join(out) + "\n"


# ---------- style v2 layouts ----------
# Each prints exactly the raw strings sample.py chose, in new arrangements: other header shapes, column orders,
# separators, totals above the items, and rows without column headings.

def _kv_header(q: Quote, rng: random.Random) -> list[str]:
    """Header fields as key: value pairs in a shuffled order, the title above or below the supplier."""
    title = q.h("Quotation")
    title = rng.choice([title.upper(), title, title.title()])
    pairs = []
    if q.quote_no:
        pairs.append((rng.choice([f"{q.h('Quotation')} no.", "Ref", "Reference", "No.", "Number", "Doc no."]), q.quote_no))
    if q.date_raw:
        pairs.append((rng.choice(["Date", "Dated", "Issue date", "Date issued"]), q.date_raw))
    pairs.append((rng.choice(["Customer", "Bill to", "Prepared for", "Client", "To"]), q.customer))
    if q.customer_ref:
        pairs.append((rng.choice(["Your ref", "Customer PO", "Your order ref", "Enquiry"]), q.customer_ref))
    rng.shuffle(pairs)
    sep = rng.choice([": ", " - ", "  ", " : "])
    head = [q.supplier, q.address] if rng.random() < 0.6 else [q.supplier]
    out = [*head, "", title, *[f"{k}{sep}{v}" for k, v in pairs]] if rng.random() < 0.7 else \
          [title, "", *head, *[f"{k}{sep}{v}" for k, v in pairs]]
    if q.currency_line:
        out.append(q.currency_line)
    if q.gst["treatment"] == "inclusive":
        rate = f" {q.gst['rate_raw']}" if q.gst["rate_raw"] else ""
        out.append(rng.choice([f"All prices include{rate} GST.", f"Prices shown are inclusive of{rate} GST.",
                               f"GST{rate} is included in all prices."]))
    out.append("")
    return out


COLUMN_NAMES = {
    "desc": ["Description", "Item", "Details", "Particulars"],
    "qty": ["Qty", "Quantity", "Qty.", "No."],
    "unit": ["Unit", "UOM", "Per", "U/M"],
    "price": ["Unit Price", "Rate", "Price", "Each", "Unit Cost"],
    "disc": ["Disc", "Discount", "Less"],
    "total": ["Amount", "Total", "Line Total", "Ext. Price", "Value"],
    "code": ["Code", "SKU", "Part No.", "Item No."],
}


def _columns(q: Quote, rng: random.Random) -> list[str]:
    """Which item columns to print, in which order. Description stays before the numbers; amount is last or second."""
    numbers = ["qty", "unit", "price"]
    if rng.random() < 0.4:
        rng.shuffle(numbers)
    if rng.random() < 0.5 and numbers.index("unit") != numbers.index("qty") + 1:
        numbers.remove("unit")
        numbers.insert(numbers.index("qty") + 1, "unit")
    cols = ["desc", *numbers]
    if any(line.disc_raw for line in q.lines):
        cols.insert(len(cols), "disc")
    cols.append("total")
    if any(line.code for line in q.lines):
        cols.insert(0, "code")
    return cols


def _cell(q: Quote, line, col: str) -> str:
    return {"desc": line.desc, "qty": line.qty_raw or "", "unit": line.unit_raw or "", "price": line.price_raw or "",
            "disc": line.disc_raw or "", "total": line.total_raw, "code": line.code or ""}[col]


def _footer_lines(q: Quote, rng: random.Random, width: int | None = None) -> list[str]:
    sep = rng.choice([": ", "  ", " ", " = "])
    out = []
    for label, amount in _footer_rows(q):
        text = f"{label}{sep}{amount}" if amount else label
        out.append(text.rjust(width) if width else text)
    return out


def kv_table(q: Quote, rng: random.Random) -> str:
    out = _kv_header(q, rng)
    cols = _columns(q, rng)
    names = [rng.choice(COLUMN_NAMES[c]) for c in cols]
    rows = [[_cell(q, line, c) for c in cols] for line in q.lines]
    if rng.random() < 0.5:
        names, rows = ["#", *names], [[str(i), *r] for i, r in enumerate(rows, 1)]
    widths = [max(len(r[c]) for r in [names, *rows]) for c in range(len(names))]
    gap = rng.choice(["  ", "   ", " | "])
    def fmt(row: list[str]) -> str:
        return gap.join(cell.ljust(w) for cell, w in zip(row, widths, strict=True)).rstrip()
    out.append(fmt(names))
    if rng.random() < 0.6:
        out.append(rng.choice(["-", "=", "_"]) * len(fmt(names)))
    out.extend(fmt(r) for r in rows)
    out.append("")
    out.extend(_footer_lines(q, rng))
    out.append("")
    out.extend(_terms(q))
    return "\n".join(out) + "\n"


def _quoted(cell: str, sep: str) -> str:
    return f'"{cell}"' if sep == ", " and ("," in cell or '"' in cell) else cell


def delimited(q: Quote, rng: random.Random) -> str:
    """Items as comma-space or tab-separated rows under a heading row, as pasted from a spreadsheet."""
    out = _kv_header(q, rng)
    sep = rng.choice([", ", "\t"])  # a bare "," would glue numbers together
    cols = _columns(q, rng)
    out.append(sep.join(rng.choice(COLUMN_NAMES[c]) for c in cols))
    out.extend(sep.join(_quoted(_cell(q, line, c), sep) for c in cols) for line in q.lines)
    out.append("")
    out.extend(_footer_lines(q, rng))
    out.append("")
    out.extend(_terms(q))
    return "\n".join(out) + "\n"


def totals_first(q: Quote, rng: random.Random) -> str:
    """A summary of the totals above the item breakdown."""
    out = _kv_header(q, rng)
    out.append(rng.choice(["SUMMARY", "Summary", "Price summary", "At a glance"]))
    out.extend(f"  {line}" for line in _footer_lines(q, rng))
    out.append("")
    out.append(rng.choice(["Breakdown", "Itemised breakdown", "Details", "What's included"]) + ":")
    for i, line in enumerate(q.lines, 1):
        code = f" [{line.code}]" if line.code else ""
        if line.qty_raw:
            disc = f" less {line.disc_raw}" if line.disc_raw else ""
            out.append(f"{i}. {line.desc}{code}: {line.qty_raw} {line.unit_raw} @ {line.price_raw}{disc} -> {line.total_raw}")
        else:
            out.append(f"{i}. {line.desc}{code} ({line.unit_raw}): {line.total_raw}")
    out.append("")
    out.extend(_terms(q))
    return "\n".join(out) + "\n"


def numbered_lines(q: Quote, rng: random.Random) -> str:
    """One sentence-like line per item: "1) Desc - 4 ea @ $5.00 = $20.00"."""
    out = _header_block(q, rng) if rng.random() < 0.5 else _kv_header(q, rng)
    bullet = rng.choice(["{i})", "{i}.", "({i})", "-", "*"])
    at, eq = rng.choice([("@", "="), ("x", "="), ("at", "="), ("@", "->"), ("x", ":")])
    for i, line in enumerate(q.lines, 1):
        b = bullet.format(i=i)
        code = f" ({line.code})" if line.code else ""
        if line.qty_raw:
            disc = f", {q.h('Discount').lower()} {line.disc_raw}" if line.disc_raw else ""
            out.append(f"{b} {line.desc}{code} - {line.qty_raw} {line.unit_raw} {at} {line.price_raw}{disc} {eq} {line.total_raw}")
        else:
            out.append(f"{b} {line.desc}{code} - {line.unit_raw} {eq} {line.total_raw}")
    out.append("")
    out.extend(_footer_lines(q, rng))
    out.append("")
    out.extend(_terms(q))
    return "\n".join(out) + "\n"


def bare_columns(q: Quote, rng: random.Random) -> str:
    """Aligned item columns with no heading row, totals right-aligned under the amounts."""
    out = _header_block(q, rng) if rng.random() < 0.5 else _kv_header(q, rng)
    cols = _columns(q, rng)
    rows = [[_cell(q, line, c) for c in cols] for line in q.lines]
    widths = [max(len(r[c]) for r in rows) for c in range(len(cols))]
    lines = ["   ".join(cell.ljust(w) if c in ("desc", "code", "unit") else cell.rjust(w)
                        for cell, w, c in zip(r, widths, cols, strict=True)).rstrip() for r in rows]
    out.extend(lines)
    width = max(len(x) for x in lines)
    out.append(" " * max(0, width - 12) + "-" * min(12, width))
    out.extend(_footer_lines(q, rng, width))
    out.append("")
    out.extend(_terms(q))
    return "\n".join(out) + "\n"


RENDERERS = {"fixed_table": fixed_table, "pipe_table": pipe_table, "item_blocks": item_blocks,
             "email_list": email_list, "prose_email": prose_email, "kv_table": kv_table, "delimited": delimited,
             "totals_first": totals_first, "numbered_lines": numbered_lines, "bare_columns": bare_columns}


def render(q: Quote, rng: random.Random) -> str:
    return RENDERERS[q.layout](q, rng)
