"""Choose the 20 pilot documents: the 5 hand-written seeds plus 3 generated dev documents per hard-case family.

    python -m quote_distill.teacher.pilot --out data/pilot

Selection is deterministic: the same pool seed always picks the same documents. Only the dev split is used,
because the pilot tunes the prompt. Writes <out>/pilot-20.jsonl (id, text, label, meta) and <out>/manifest.json.
"""

import argparse
import hashlib
import json
from pathlib import Path

from ..generator.build import generate

SEEDS_DIR = Path(__file__).resolve().parents[3] / "data" / "seeds"

# family -> (features a document must have, features that make it a better example)
FAMILIES = {
    "inclusive GST and rounding": ({"gst:inclusive"}, {"half_cent_tie", "doc_discount", "gst_rate_unprinted"}),
    "line and lump-sum discounts": ({"line:lump_sum"}, {"line:line_discount_percent", "line:line_discount_amount",
                                                         "doc_discount", "half_cent_tie", "line:sub_cent_price"}),
    "sparse or missing fields": ({"missing:subtotal", "missing:quote_number"}, {"missing:date", "missing:total",
                                                                                "missing:validity", "missing:payment_terms",
                                                                                "gst_plus_unpriced", "doc_discount_amount_unprinted"}),
    "supplier errors and credits": ({"supplier_error"}, {"line:credit", "line:foc", "line:qty_in_words", "line:decimal_qty"}),
    "prose, bare $ and conditional discounts": ({"layout:prose_email", "bare_dollar"}, {"conditional_discount", "relative_validity",
                                                                                         "customer_ref_decoy", "header_typos"}),
}
PER_FAMILY = 3


def load_seeds(seeds_dir: Path = SEEDS_DIR) -> list[dict]:
    manifest = json.loads((seeds_dir / "manifest.json").read_text(encoding="utf-8"))
    out = []
    for entry in manifest["seeds"]:
        text = (seeds_dir / f"{entry['id']}.doc.txt").read_text(encoding="utf-8")
        label = json.loads((seeds_dir / f"{entry['id']}.label.json").read_text(encoding="utf-8"))
        out.append({"id": entry["id"], "split": "seed", "text": text, "label": label,
                    "meta": {"locale": entry["locale"], "family": "hand-written seed",
                             "expected_check_failures": entry["expected_check_failures"],
                             "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}})
    return out


def select(pool: list[dict]) -> list[dict]:
    """Pick PER_FAMILY documents per family, most bonus features first, spreading locales and layouts."""
    chosen, used = [], set()
    for family, (required, bonus) in FAMILIES.items():
        candidates = [r for r in pool if r["id"] not in used and required <= set(r["meta"]["features"])]
        picked: list[dict] = []
        while len(picked) < PER_FAMILY and candidates:
            locales = {r["meta"]["locale"] for r in picked}
            layouts = {r["meta"]["layout"] for r in picked}

            def rank(r, bonus=bonus, locales=locales, layouts=layouts):
                f = set(r["meta"]["features"])
                return (-len(bonus & f), r["meta"]["locale"] in locales, r["meta"]["layout"] in layouts, r["id"])

            best = min(candidates, key=rank)
            picked.append(best)
            candidates.remove(best)
        if len(picked) < PER_FAMILY:
            raise ValueError(f"pool has only {len(picked)} documents for family {family!r}; generate a larger pool")
        for r in picked:
            used.add(r["id"])
            chosen.append({**r, "meta": {**r["meta"], "family": family}})
    return chosen


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pool-seed", type=int, default=7)
    ap.add_argument("--pool-size", type=int, default=2000)
    ap.add_argument("--out", type=Path, default=Path("data/pilot"))
    args = ap.parse_args(argv)
    pool, _ = generate(args.pool_size, args.pool_seed, "dev")
    pool = [r for r in pool if not r.get("rejected")]
    docs = load_seeds() + select(pool)
    args.out.mkdir(parents=True, exist_ok=True)
    with open(args.out / "pilot-20.jsonl", "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    manifest = {"pool": {"split": "dev", "seed": args.pool_seed, "size": args.pool_size},
                "documents": [{"id": d["id"], "family": d["meta"]["family"], "locale": d["meta"]["locale"],
                               "layout": d["meta"].get("layout", "seed"), "text_sha256": d["meta"]["text_sha256"],
                               "expected_check_failures": d["meta"]["expected_check_failures"]} for d in docs]}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{len(docs)} pilot documents written to {args.out}")
    for d in manifest["documents"]:
        print(f"  {d['id']:<16} {d['locale']}  {d['layout']:<12} {d['family']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
