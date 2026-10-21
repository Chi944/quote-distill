"""The frozen test set: selection, freezing and verification.

    python -m quote_distill.splits select --out data/test      # once; then hand-check, then freeze
    python -m quote_distill.splits freeze data/test           # writes MANIFEST.sha256
    python -m quote_distill.splits verify data/test           # CI: fails on any change to a test document

Test documents come from their own split ("test-candidates"), so their random streams never overlap dev or train.
Training and prompt code must not read data/test; `exclude_test` drops any record whose text matches a test document.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from .generator.build import generate

TEST_DIR = Path(__file__).resolve().parents[2] / "data" / "test"
N_TEST = 300
POOL_SEED, POOL_SIZE = 1, 3000
FEATURE_TARGET = 15  # at least this many test documents per hard-case feature, where the pool allows


def select_test(pool: list[dict], n: int = N_TEST) -> list[dict]:
    """Greedy, deterministic: each pick covers the most under-target features, keeping locales and layouts balanced."""
    locales = sorted({r["meta"]["locale"] for r in pool})
    layouts = sorted({r["meta"]["layout"] for r in pool})
    cap_locale, cap_layout = -(-n // len(locales)), -(-n // len(layouts))
    have, by_locale, by_layout = Counter(), Counter(), Counter()
    chosen, left = [], sorted(pool, key=lambda r: r["meta"]["text_sha256"])  # hash order: arbitrary but fixed
    while len(chosen) < n:
        best, best_key = None, None
        for r in left:
            m = r["meta"]
            if by_locale[m["locale"]] >= cap_locale or by_layout[m["layout"]] >= cap_layout:
                continue
            gain = sum(1 for f in m["features"] if not f.startswith(("locale:", "layout:")) and have[f] < FEATURE_TARGET)
            key = (gain, -by_locale[m["locale"]] - by_layout[m["layout"]])
            if best_key is None or key > best_key:
                best, best_key = r, key
        if best is None:
            raise ValueError("pool too small for the locale and layout caps")
        left.remove(best)
        chosen.append(best)
        have.update(best["meta"]["features"])
        by_locale[best["meta"]["locale"]] += 1
        by_layout[best["meta"]["layout"]] += 1
    return sorted(chosen, key=lambda r: r["id"])


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def doc_hash(record: dict) -> str:
    """Hash of one test document: its text and its label, canonically serialised."""
    return _sha(json.dumps({"text": record["text"], "label": record["label"]}, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def load(test_dir: Path = TEST_DIR) -> list[dict]:
    return [json.loads(line) for line in open(test_dir / "docs.jsonl", encoding="utf-8")]


def freeze(test_dir: Path = TEST_DIR) -> str:
    records = load(test_dir)
    lines = [f"{_sha((test_dir / 'docs.jsonl').read_bytes())}  docs.jsonl"]
    lines += [f"{doc_hash(r)}  {r['id']}" for r in records]
    (test_dir / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines[0].split()[0]


def verify(test_dir: Path = TEST_DIR) -> list[str]:
    """Problems with the frozen test set; empty means it is exactly as frozen."""
    manifest = (test_dir / "MANIFEST.sha256").read_text(encoding="utf-8").split("\n")
    expected = dict(reversed(line.split("  ", 1)) for line in manifest if line.strip())
    problems = []
    if _sha((test_dir / "docs.jsonl").read_bytes()) != expected.pop("docs.jsonl"):
        problems.append("docs.jsonl changed since it was frozen")
    records = load(test_dir)
    seen = {r["id"]: doc_hash(r) for r in records}
    problems += [f"{i}: changed" for i, h in seen.items() if i in expected and expected[i] != h]
    problems += [f"{i}: added" for i in seen.keys() - expected.keys()]
    problems += [f"{i}: removed" for i in expected.keys() - seen.keys()]
    if len(records) != N_TEST:
        problems.append(f"{len(records)} documents, expected {N_TEST}")
    return sorted(problems)


def test_text_hashes(test_dir: Path = TEST_DIR) -> set[str]:
    return {r["meta"]["text_sha256"] for r in load(test_dir)}


def exclude_test(records: list[dict], test_dir: Path = TEST_DIR) -> list[dict]:
    """Drop any record whose text is a test document. Training data must pass through this."""
    banned = test_text_hashes(test_dir)
    return [r for r in records if r["meta"]["text_sha256"] not in banned]


def coverage(records: list[dict]) -> dict:
    return {"documents": len(records),
            "locales": dict(sorted(Counter(r["meta"]["locale"] for r in records).items())),
            "layouts": dict(sorted(Counter(r["meta"]["layout"] for r in records).items())),
            "features": dict(sorted(Counter(f for r in records for f in r["meta"]["features"]
                                            if not f.startswith(("locale:", "layout:"))).items())),
            "line_items": sum(len(r["label"]["line_items"]) for r in records),
            "with_supplier_error": sum(bool(r["meta"]["expected_check_failures"]) for r in records)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Select, freeze and verify the test set.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("--out", type=Path, default=TEST_DIR)
    for name in ("freeze", "verify"):
        sub.add_parser(name).add_argument("dir", type=Path, nargs="?", default=TEST_DIR)
    args = ap.parse_args(argv)
    if args.cmd == "select":
        if (args.out / "MANIFEST.sha256").exists():
            sys.exit(f"refusing: {args.out} is frozen; the test set is never re-selected")
        pool, _ = generate(POOL_SIZE, POOL_SEED, "test-candidates")
        chosen = select_test([r for r in pool if not r.get("rejected")])
        args.out.mkdir(parents=True, exist_ok=True)
        with open(args.out / "docs.jsonl", "w", encoding="utf-8") as f:
            for r in chosen:
                f.write(json.dumps({**r, "split": "test"}, ensure_ascii=False) + "\n")
        (args.out / "coverage.json").write_text(json.dumps(coverage(chosen), indent=2) + "\n", encoding="utf-8")
        print(f"{len(chosen)} test documents written to {args.out}")
    elif args.cmd == "freeze":
        print(f"frozen: docs.jsonl {freeze(args.dir)[:12]}")
    else:
        problems = verify(args.dir)
        for p in problems:
            print("  !", p)
        print("test set intact" if not problems else f"{len(problems)} problems")
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
