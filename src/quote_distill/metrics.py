"""Score predicted labels against gold. Every rate is reported as numerator/denominator.

Fields are compared on `state`, `value` and (for discounts) `kind`; `raw` is never scored. Text fields are compared
with whitespace collapsed and payment terms with the normalisation in docs/schema.md. Everything else is an exact
string match, so `65.0` is wrong where gold says `65.00`. A prediction that is missing, unparseable or schema-invalid
is still scored field by field: anything absent or malformed counts as wrong.
"""

from collections import Counter
from dataclasses import dataclass, field

from .checks import check_arithmetic
from .normalise import collapse, normalise_payment_terms
from .schema import schema_errors

DOC_FIELDS = ["supplier", "quote_number", "date", "currency", "subtotal", "total", "validity", "payment_terms",
              "gst.treatment", "gst.rate", "gst.amount"]
CRITICAL_FIELDS = ["supplier", "quote_number", "date", "currency", "subtotal", "gst.treatment", "gst.rate", "gst.amount",
                   "total"]
LINE_FIELDS = ["description", "quantity", "unit", "unit_price", "discount", "line_total"]
DISCOUNT_FIELDS = ["description", "kind", "rate", "amount"]
TEXT_FIELDS = {"supplier", "quote_number", "description"}
MISSING = ("<missing>",)


@dataclass(frozen=True)
class Ratio:
    n: int
    d: int

    @property
    def rate(self) -> float | None:
        return self.n / self.d if self.d else None

    def __add__(self, other: "Ratio") -> "Ratio":
        return Ratio(self.n + other.n, self.d + other.d)

    def __str__(self) -> str:
        return f"{self.n}/{self.d} ({self.n / self.d:.1%})" if self.d else f"{self.n}/0 (n/a)"


def _get(node, path: str):
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def canon(name: str, f) -> tuple:
    """Comparable form of one field. Gold and prediction go through the same function."""
    leaf = name.rsplit(".", 1)[-1]
    if leaf in ("treatment", "kind"):
        return (f,) if isinstance(f, str) else MISSING
    if not isinstance(f, dict) or f.get("state") not in ("stated", "not_stated"):
        return MISSING
    if f["state"] == "not_stated":
        return ("not_stated",)
    value = f.get("value")
    if not isinstance(value, str):
        return MISSING
    if leaf in TEXT_FIELDS:
        value = collapse(value)
    elif leaf == "payment_terms":
        value = normalise_payment_terms(value)
    return ("stated", f.get("kind"), value) if leaf == "discount" else ("stated", value)


def _items(label, key: str) -> list:
    items = label.get(key) if isinstance(label, dict) else None
    return items if isinstance(items, list) else []


def line_key(line) -> tuple:
    return tuple(canon(f, _get(line, f)) for f in LINE_FIELDS)


def discount_key(d) -> tuple:
    return tuple(canon(f, _get(d, f)) for f in DISCOUNT_FIELDS)


@dataclass
class DocScore:
    doc_id: str
    parsed: bool
    schema_valid: bool
    fields: dict[str, bool]  # document-level field -> exact
    line_fields: dict[str, Ratio]  # line field -> matches by position / max(gold, predicted lines)
    lines_tp: int
    lines_gold: int
    lines_pred: int
    discounts_tp: int
    discounts_gold: int
    discounts_pred: int
    gold_not_stated: int  # denominator for invented values
    invented: list[str]  # gold not_stated, predicted stated
    omitted: list[str]  # gold stated, predicted not_stated
    gold_failures: list[str]
    pred_failures: list[str] | None  # None when the prediction cannot be checked
    exact: bool
    mismatches: list[tuple[str, tuple, tuple]] = field(default_factory=list)

    @property
    def arithmetic_agrees(self) -> bool:
        return self.pred_failures is not None and sorted(self.pred_failures) == sorted(self.gold_failures)


def _aligned_pairs(gold: dict, pred) -> list[tuple[str, object, object]]:
    """(path, gold field, predicted field) for every field object in gold, lines and discounts aligned by position."""
    pairs = [(p, _get(gold, p), _get(pred, p)) for p in DOC_FIELDS]
    for key, names in (("line_items", LINE_FIELDS), ("discounts", DISCOUNT_FIELDS)):
        g_items, p_items = _items(gold, key), _items(pred, key)
        for i in range(max(len(g_items), len(p_items))):
            g = g_items[i] if i < len(g_items) else None
            p = p_items[i] if i < len(p_items) else None
            pairs += [(f"{key}[{i}].{n}", _get(g, n), _get(p, n)) for n in names]
    return pairs


def score_document(doc_id: str, gold: dict, pred) -> DocScore:
    parsed = isinstance(pred, dict)
    schema_valid = parsed and not schema_errors(pred)
    pairs = _aligned_pairs(gold, pred if parsed else None)

    fields, line_fields, mismatches, invented, omitted = {}, {}, [], [], []
    gold_not_stated = 0
    for path, g, p in pairs:
        cg, cp = canon(path, g), canon(path, p)
        gold_not_stated += cg == ("not_stated",)
        ok = cg == cp
        if not ok:
            mismatches.append((path, cg, cp))
        if cg == ("not_stated",) and cp[:1] == ("stated",):
            invented.append(path)
        if cg[:1] == ("stated",) and cp == ("not_stated",):
            omitted.append(path)
        if path in DOC_FIELDS:
            fields[path] = ok
        elif path.startswith("line_items["):
            name = path.split(".", 1)[1]
            line_fields[name] = line_fields.get(name, Ratio(0, 0)) + Ratio(int(ok), 1)

    def multiset_tp(key, keyfn) -> tuple[int, int, int]:
        g = Counter(keyfn(x) for x in _items(gold, key))
        p = Counter(keyfn(x) for x in _items(pred, key)) if parsed else Counter()
        return sum((g & p).values()), sum(g.values()), sum(p.values())

    lines_tp, lines_gold, lines_pred = multiset_tp("line_items", line_key)
    disc_tp, disc_gold, disc_pred = multiset_tp("discounts", discount_key)
    gold_failures = check_arithmetic(gold)[0]
    pred_failures = check_arithmetic(pred)[0] if schema_valid else None
    return DocScore(doc_id, parsed, schema_valid, fields, line_fields, lines_tp, lines_gold, lines_pred,
                    disc_tp, disc_gold, disc_pred, gold_not_stated, invented, omitted, gold_failures, pred_failures,
                    exact=parsed and not mismatches, mismatches=mismatches)


def _f1(tp: int, gold: int, pred: int) -> dict:
    """F1 = 2·TP / (gold + predicted). With no gold and no predicted items there is nothing to score (None)."""
    return {"tp": tp, "precision": Ratio(tp, pred), "recall": Ratio(tp, gold),
            "f1": 2 * tp / (gold + pred) if gold + pred else None}


def aggregate(scores: list[DocScore]) -> dict:
    """Corpus-level report. Field rates are micro-averaged; every entry carries its denominator."""
    n = len(scores)
    per_field = {f: Ratio(sum(s.fields[f] for s in scores), n) for f in DOC_FIELDS}
    line_fields: dict[str, Ratio] = {}
    for s in scores:
        for name, r in s.line_fields.items():
            line_fields[name] = line_fields.get(name, Ratio(0, 0)) + r
    critical = sum((per_field[f] for f in CRITICAL_FIELDS), Ratio(0, 0))
    return {
        "documents": n,
        "parsed": Ratio(sum(s.parsed for s in scores), n),
        "schema_valid": Ratio(sum(s.schema_valid for s in scores), n),
        "critical_fields": critical,
        "fields": per_field,
        "line_fields": line_fields,
        "line_items": _f1(sum(s.lines_tp for s in scores), sum(s.lines_gold for s in scores),
                          sum(s.lines_pred for s in scores)),
        "document_discounts": _f1(sum(s.discounts_tp for s in scores), sum(s.discounts_gold for s in scores),
                                  sum(s.discounts_pred for s in scores)),
        "invented": Ratio(sum(len(s.invented) for s in scores), sum(s.gold_not_stated for s in scores)),
        "omitted": sum(len(s.omitted) for s in scores),
        "arithmetic_agrees": Ratio(sum(s.arithmetic_agrees for s in scores), n),
        "arithmetic_consistent": Ratio(sum(s.pred_failures == [] for s in scores), n),
        "exact_documents": Ratio(sum(s.exact for s in scores), n),
        "failing_documents": [s.doc_id for s in scores if not s.exact],
    }



# Fixed before the pilot runs; see docs/pilot-plan.md.
PILOT_GATES = [
    ("Schema-valid JSON, no repair", lambda r: r["schema_valid"], lambda x: x.n == x.d),
    ("Critical fields exact", lambda r: r["critical_fields"], lambda x: x.d > 0 and x.n / x.d >= 0.95),
    ("Line-item F1 (all six fields)", lambda r: r["line_items"]["f1"], lambda x: x is not None and x >= 0.90),
    ("Invented values", lambda r: r["invented"], lambda x: x.n <= 1),
    ("Arithmetic agrees with gold", lambda r: r["arithmetic_agrees"], lambda x: x.d > 0 and x.d - x.n <= 1),
]


def pilot_gates(report: dict) -> list[tuple[str, object, bool]]:
    return [(name, get(report), passes(get(report))) for name, get, passes in PILOT_GATES]


def _show(x) -> str:
    return f"{x:.3f}" if isinstance(x, float) else ("n/a" if x is None else str(x))


def format_report(report: dict, scores: list[DocScore], gates: bool = False) -> str:
    li, dd = report["line_items"], report["document_discounts"]
    out = [f"Documents: {report['documents']}", ""]
    if gates:
        out += ["| Gate | Result | Pass |", "|---|---|---|"]
        out += [f"| {name} | {_show(v)} | {'yes' if ok else '**no**'} |" for name, v, ok in pilot_gates(report)]
        out.append("")
    out += ["| Measure | Result |", "|---|---|",
            f"| Parsed as JSON | {report['parsed']} |",
            f"| Schema-valid | {report['schema_valid']} |",
            f"| Critical fields exact | {report['critical_fields']} |",
            f"| Line items: precision / recall / F1 | {li['precision']} / {li['recall']} / {_show(li['f1'])} |",
            f"| Document discounts: precision / recall / F1 | {dd['precision']} / {dd['recall']} / {_show(dd['f1'])} |",
            f"| Invented values (gold not_stated, predicted stated) | {report['invented']} |",
            f"| Omitted values (gold stated, predicted not_stated) | {report['omitted']} |",
            f"| Arithmetic agrees with gold | {report['arithmetic_agrees']} |",
            f"| Arithmetic internally consistent | {report['arithmetic_consistent']} |",
            f"| Whole document exact | {report['exact_documents']} |",
            "", "| Field | Exact |", "|---|---|"]
    out += [f"| {f} | {r} |" for f, r in report["fields"].items()]
    out += [f"| line.{f} (by position) | {r} |" for f, r in report["line_fields"].items()]
    failing = [s for s in scores if not s.exact]
    if failing:
        out += ["", f"## Failing documents ({len(failing)}/{len(scores)})", ""]
        for s in failing:
            tag = "" if s.schema_valid else (" (schema-invalid)" if s.parsed else " (no JSON)")
            out.append(f"- **{s.doc_id}**{tag}: " + "; ".join(
                f"`{path}` gold {g[1:] if len(g) > 1 else g[0]} vs predicted {p[1:] if len(p) > 1 else p[0]}"
                for path, g, p in s.mismatches[:8]) + (f"; and {len(s.mismatches) - 8} more" if len(s.mismatches) > 8 else ""))
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Score predictions against gold labels.")
    ap.add_argument("--gold", required=True, help="JSONL of records with id and label (generator or pilot format)")
    ap.add_argument("--pred", required=True, help="JSONL of {id, output}; output is the parsed label or null")
    ap.add_argument("--gates", action="store_true", help="also show the pilot quality gates")
    args = ap.parse_args(argv)
    gold = [json.loads(line) for line in open(args.gold, encoding="utf-8")]
    preds = {r["id"]: r.get("output") for r in map(json.loads, open(args.pred, encoding="utf-8"))}
    missing = [g["id"] for g in gold if g["id"] not in preds]
    scores = [score_document(g["id"], g["label"], preds.get(g["id"])) for g in gold]
    if missing:
        print(f"{len(missing)} gold documents have no prediction and score as empty: {', '.join(missing)}\n")
    print(format_report(aggregate(scores), scores, gates=args.gates))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
