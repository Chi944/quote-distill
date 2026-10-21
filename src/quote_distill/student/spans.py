"""Locate each gold field's `raw` text in its document, for training the encoder tagger.

A label says what was printed but not where. `align` finds the place: every occurrence of the raw text (whitespace
may differ, and a match may not start or end inside a word or number), narrowed by document structure. Line-item
fields are searched only within their own row's region, after its description where possible; document fields
must be unique once line items are placed. Anything still ambiguous is reported, never guessed, so a document
with unresolved fields can be left out of tagger training and counted.
"""

import re
from dataclasses import dataclass, field

from ..checks import iter_fields

LINE = re.compile(r"\$\.line_items\[(\d+)\]\.(\w+)$")
# May be printed more than once by design (every price may carry the symbol; a GST rate in the header and the
# footer): the first free occurrence is the convention.
REPEATED = {"$.currency", "$.gst.rate"}
# May sit inside another field's text ("10% trade discount", "NZ$ 1.85"); recorded as nested, not tagged.
NESTABLE = re.compile(r"^\$\.(currency|gst\.rate|discounts\[\d+\]\.rate|line_items\[\d+\]\.discount)$")
# When several of these print the same text, they appear in this order.
FOOTER_ORDER = ["$.subtotal", "$.total"]
# Printed below the items: a word like "Discount" above or inside the item rows is a column header or a line label.
FOOTER = re.compile(r"^\$\.(subtotal|total|gst\.amount|discounts\[\d+\]\.\w+)$")


@dataclass
class Alignment:
    spans: dict[str, tuple[int, int]] = field(default_factory=dict)  # field path -> [start, end)
    nested: dict[str, tuple[int, int]] = field(default_factory=dict)  # inside another field's span
    ambiguous: dict[str, int] = field(default_factory=dict)  # field path -> remaining candidates
    missing: list[str] = field(default_factory=list)  # raw not found at all

    @property
    def complete(self) -> bool:
        return not self.ambiguous and not self.missing


def occurrences(text: str, raw: str) -> list[tuple[int, int]]:
    parts = raw.split()
    if not parts:
        return []
    pattern = r"\s+".join(map(re.escape, parts))
    # A match may not split a word or a number: "RM7.91" holds "RM", but "units" does not hold "unit".
    if raw[0].isdigit():
        pattern = r"(?<![0-9.,])" + pattern
    elif raw[0].isalpha():
        pattern = r"(?<![A-Za-z])" + pattern
    if raw[-1].isdigit():
        pattern += r"(?![0-9]|[.,][0-9])"
    elif raw[-1].isalpha():
        pattern += r"(?![A-Za-z])"
    return [m.span() for m in re.finditer(pattern, text)]


def _free(span, taken) -> bool:
    return all(span[1] <= a or span[0] >= b for a, b in taken)


def _inside(span, taken) -> bool:
    return any(a <= span[0] and span[1] <= b for a, b in taken)


def _line_start(text: str, pos: int) -> int:
    return text.rfind("\n", 0, pos) + 1


def align(label: dict, text: str) -> Alignment:
    out = Alignment()
    fields = [(p, f) for p, f in iter_fields(label) if f["state"] == "stated"]
    cands = {p: occurrences(text, f["raw"]) for p, f in fields}
    out.missing = [p for p, c in cands.items() if not c]

    # Descriptions in document order fix each line item's region.
    regions, cursor = {}, 0
    for i in range(len(label["line_items"])):
        path = f"$.line_items[{i}].description"
        after = [c for c in cands.get(path, []) if c[0] >= cursor]
        if after:
            out.spans[path] = after[0]
            cursor = after[0][1]
    # A row's region starts at its description's line (a row number or "2 x" may come first), or at the description
    # itself when items share a line (prose), and runs to the next row's region.
    placed = sorted((s, int(LINE.match(p).group(1))) for p, s in out.spans.items())
    starts, prev_end = [], 0
    for span, i in placed:
        line = _line_start(text, span[0])
        starts.append((line if line >= prev_end else span[0], i, span[0]))
        prev_end = span[1]
    for k, (start, i, desc) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(text)
        regions[i] = (start, end, desc)

    taken = list(out.spans.values())
    for p, _ in fields:
        m = LINE.match(p)
        if p in out.spans or p in out.missing or not m:
            continue
        if int(m.group(1)) not in regions:
            out.ambiguous[p] = len(cands[p])
            continue
        lo, hi, desc = regions[int(m.group(1))]
        inside = [c for c in cands[p] if lo <= c[0] and c[1] <= hi and _free(c, taken)]
        pick = [c for c in inside if c[0] >= desc] or inside
        if pick:
            out.spans[p] = pick[0]
            taken.append(pick[0])
        elif NESTABLE.match(p) and (nest := [c for c in cands[p] if lo <= c[0] and c[1] <= hi and _inside(c, taken)]):
            out.nested[p] = nest[0]
        else:
            out.ambiguous[p] = 0

    # Document-level fields: repeat until nothing changes, placing any field left with one free candidate.
    items_end = max((e for p, (_, e) in out.spans.items() if LINE.match(p)), default=0)
    for p in cands:
        if FOOTER.match(p) and (below := [c for c in cands[p] if c[0] >= items_end]):
            cands[p] = below

    # Nestable fields wait until the rest are placed, so they can't take a span that belongs to a larger field.
    pending = [p for p, _ in fields if p not in out.spans and p not in out.missing and p not in out.ambiguous]
    while pending:
        progress = False
        for p in [p for p in pending if not NESTABLE.match(p)]:
            free = [c for c in cands[p] if _free(c, taken)]
            if len(free) == 1:
                out.spans[p] = free[0]
                taken.append(free[0])
                pending.remove(p)
                progress = True
        if not progress:
            break
    # Equal printed text in a known order (a subtotal equal to its total).
    same = [p for p in FOOTER_ORDER if p in pending]
    if len(same) > 1 and len({tuple(cands[p]) for p in same}) == 1:
        free = [c for c in cands[same[0]] if _free(c, taken)]
        if len(free) == len(same):
            for p, c in zip(same, free, strict=True):
                out.spans[p] = c
                taken.append(c)
                pending.remove(p)
    for p in sorted(pending, key=lambda p: p in REPEATED):
        free = [c for c in cands[p] if _free(c, taken)]
        nest = [c for c in cands[p] if _inside(c, taken)]
        if len(free) == 1 or (p in REPEATED and free and not nest):
            out.spans[p] = free[0]
            taken.append(free[0])
        elif NESTABLE.match(p) and nest:
            out.nested[p] = nest[0]
        else:
            out.ambiguous[p] = len(free)
    return out
