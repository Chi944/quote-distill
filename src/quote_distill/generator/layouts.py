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


RENDERERS = {"fixed_table": fixed_table, "pipe_table": pipe_table, "item_blocks": item_blocks,
             "email_list": email_list, "prose_email": prose_email}


def render(q: Quote, rng: random.Random) -> str:
    return RENDERERS[q.layout](q, rng)
