"""Generate labelled synthetic quotations and keep only labels that pass every deterministic check.

    quote-distill-generate --n 500 --seed 1 --split dev --out data/generated/dev

Output: <out>/docs.jsonl (one record per kept document) and <out>/stats.json (coverage and rejections).
The same --seed, --split and --n always produce byte-identical output.
"""

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from ..checks import check_label
from .layouts import render
from .sample import sample_quote, to_label


def generate(n: int, seed: int, split: str) -> tuple[list[dict], dict]:
    records, features, rejects = [], Counter(), Counter()
    resampled = 0
    for i in range(n):
        doc_id = f"{split}-s{seed}-{i:06d}"
        attempt = 0
        while True:
            rng = random.Random(f"{split}:{seed}:{i}:{attempt}")
            q = sample_quote(rng, doc_id)
            if q.subtotal > 0 and q.total > 0:
                break
            attempt += 1
            resampled += 1
        text = render(q, rng)
        label = to_label(q)
        result = check_label(label, text, q.locale, q.expected_failures)
        if not result.keep:
            for problem in result.schema + result.provenance + [f"arithmetic:{u}" for u in result.unexpected]:
                rejects[problem.split(":")[0] if problem.startswith("arithmetic") else problem.split(" ")[0]] += 1
            records.append({"id": doc_id, "rejected": True, "problems": result.schema + result.provenance + result.unexpected})
            continue
        features.update(q.features)
        records.append({
            "id": doc_id,
            "split": split,
            "text": text,
            "label": label,
            "meta": {
                "locale": q.locale,
                "layout": q.layout,
                "features": sorted(q.features),
                "expected_check_failures": q.expected_failures,
                "checks": {"pass": len(result.passes), "fail": len(result.failures), "skipped": len(result.skips)},
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            },
        })
    kept = [r for r in records if not r.get("rejected")]
    stats = {
        "n_requested": n,
        "n_kept": len(kept),
        "n_rejected": n - len(kept),
        "rejections": dict(rejects),
        "rejected_examples": [r for r in records if r.get("rejected")][:5],
        "resampled_nonpositive_totals": resampled,
        "seed": seed,
        "split": split,
        "feature_counts": dict(sorted(features.items())),
        "arithmetic_checks": {
            k: sum(r["meta"]["checks"][k] for r in kept) for k in ("pass", "fail", "skipped")
        },
        "line_items": sum(len(r["label"]["line_items"]) for r in kept),
    }
    return kept, stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--split", choices=["dev", "train", "test-candidates"], default="dev")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    kept, stats = generate(args.n, args.seed, args.split)
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "docs.jsonl").open("w", encoding="utf-8") as f:
        for record in kept:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    (args.out / "stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"kept {stats['n_kept']}/{stats['n_requested']} documents ({stats['line_items']} line items); "
          f"rejected {stats['n_rejected']}; arithmetic checks {stats['arithmetic_checks']}")
    return 0 if stats["n_rejected"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
