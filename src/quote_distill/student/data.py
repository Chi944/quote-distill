"""Build the student's training and validation sets from generator gold, with every test and pilot document removed.

    python -m quote_distill.student.data --out data/generated/student

Output: <out>/train.jsonl and <out>/dev.jsonl, one {id, text, target, meta} per line, and <out>/stats.json.
`target` is the string the generative student learns to write: the gold label in the compact form below, which
`expand` turns back into a schema-shaped label. `raw` is dropped (outputs may omit it and metrics never score it).
The same arguments always produce byte-identical files.
"""

import argparse
import hashlib
import json
import statistics
from pathlib import Path

from ..generator.build import generate
from ..metrics import score_document
from ..schema import schema_errors
from ..splits import exclude_test

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "data" / "pilot" / "pilot-20.jsonl"

# Seeds differ from the pilot pool (dev seed 7) and the test pool (test-candidates seed 1).
TRAIN = {"n": 10_000, "seed": 1, "split": "train"}
DEV = {"n": 1_000, "seed": 2, "split": "dev"}


LINE_ORDER = ("description", "quantity", "unit", "unit_price", "discount", "line_total")
FIELDS = {
    "top": ("supplier", "quote_number", "date", "currency", "subtotal", "total", "validity", "payment_terms"),
    "gst": ("rate", "amount"),
    "discounts": ("description", "rate", "amount"),
}


def _pack(f: dict):
    if f["state"] == "not_stated":
        return None
    rest = {k: v for k, v in f.items() if k not in ("state", "raw")}
    return rest["value"] if list(rest) == ["value"] else rest


def _unpack(v) -> dict:
    if v is None:
        return {"state": "not_stated"}
    if isinstance(v, dict):
        return {"state": "stated", **v}
    return {"state": "stated", "value": v}


def compact(label: dict) -> dict:
    """The label in a shorter, lossless form (raw aside): a field is its value or null; a line item is a row."""
    out = {k: _pack(label[k]) for k in FIELDS["top"]}
    out["line_items"] = [[_pack(line[k]) for k in LINE_ORDER] for line in label["line_items"]]
    out["discounts"] = [{**{k: _pack(d[k]) for k in FIELDS["discounts"]}, "kind": d["kind"]} for d in label["discounts"]]
    out["gst"] = {"treatment": label["gst"]["treatment"], **{k: _pack(label["gst"][k]) for k in FIELDS["gst"]}}
    return out


def expand(c: dict) -> dict:
    """Inverse of compact: rebuild a schema-shaped label. Raises KeyError, TypeError or ValueError on a malformed input."""
    label = {"schema_version": "1.0.0", **{k: _unpack(c[k]) for k in FIELDS["top"]}}
    lines = []
    for row in c["line_items"]:
        if len(row) != len(LINE_ORDER):
            raise ValueError(f"line item has {len(row)} cells, expected {len(LINE_ORDER)}")
        lines.append(dict(zip(LINE_ORDER, map(_unpack, row), strict=True)))
    label["line_items"] = lines
    label["discounts"] = [{"description": _unpack(d["description"]), "kind": d["kind"], "rate": _unpack(d["rate"]),
                           "amount": _unpack(d["amount"])} for d in c["discounts"]]
    label["gst"] = {"treatment": c["gst"]["treatment"], **{k: _unpack(c["gst"][k]) for k in FIELDS["gst"]}}
    return label


def target(label: dict) -> str:
    return json.dumps(compact(label), ensure_ascii=False, separators=(",", ":"))


def pilot_text_hashes(path: Path = PILOT) -> set[str]:
    return {json.loads(line)["meta"]["text_sha256"] for line in path.open(encoding="utf-8")}


def prepare(records: list[dict]) -> tuple[list[dict], dict]:
    """Drop test and pilot texts, attach targets, and confirm every target scores exact against its gold label."""
    kept = exclude_test(records)
    n_test = len(records) - len(kept)
    pilot = pilot_text_hashes()
    clean = [r for r in kept if r["meta"]["text_sha256"] not in pilot]
    out, not_exact = [], []
    for r in clean:
        t = target(r["label"])
        back = expand(json.loads(t))
        if schema_errors(back) or not score_document(r["id"], r["label"], back).exact:
            not_exact.append(r["id"])
        out.append({"id": r["id"], "text": r["text"], "target": t,
                    "meta": {k: r["meta"][k] for k in ("locale", "layout", "features", "text_sha256")}})
    return out, {"generated": len(records), "dropped_test": n_test, "dropped_pilot": len(kept) - len(clean),
                 "kept": len(out), "targets_not_exact": not_exact}


def lengths(rows: list[dict]) -> dict:
    def summary(xs):
        xs = sorted(xs)
        return {"median": int(statistics.median(xs)), "p95": xs[int(0.95 * (len(xs) - 1))], "max": xs[-1]}
    return {"text_chars": summary([len(r["text"]) for r in rows]),
            "target_chars": summary([len(r["target"]) for r in rows])}


def write(rows: list[dict], path: Path) -> str:
    data = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows).encode("utf-8")
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-train", type=int, default=TRAIN["n"])
    parser.add_argument("--n-dev", type=int, default=DEV["n"])
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    stats, ids = {}, {}
    for name, cfg, n in (("train", TRAIN, args.n_train), ("dev", DEV, args.n_dev)):
        records, _ = generate(n, cfg["seed"], cfg["split"])
        rows, counts = prepare(records)
        ids[name] = {r["meta"]["text_sha256"] for r in rows}
        stats[name] = {**cfg, "n": n, **counts, **lengths(rows), "sha256": write(rows, args.out / f"{name}.jsonl")}
        print(f"{name}: kept {counts['kept']}/{counts['generated']} (dropped {counts['dropped_test']} test, "
              f"{counts['dropped_pilot']} pilot); targets exact {counts['kept'] - len(counts['targets_not_exact'])}"
              f"/{counts['kept']}")
    stats["train_dev_shared_texts"] = len(ids["train"] & ids["dev"])
    (args.out / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(f"train/dev shared texts: {stats['train_dev_shared_texts']}")
    bad = stats["train"]["targets_not_exact"] or stats["dev"]["targets_not_exact"] or stats["train_dev_shared_texts"]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
