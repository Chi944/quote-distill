"""Write parity fixtures for the demo's TypeScript port of expand, decode, the token reader and the arithmetic check.

    python -m quote_distill.student.fixtures --data data/generated/student/dev.jsonl --out demo/fixtures/dev.jsonl

Each line holds a document and what the Python code produces for it, so `npm test` in demo/ can require identical
output from TypeScript. Built from dev and pilot documents only; the frozen test set is never read.
"""

import argparse
import json
import re
from pathlib import Path

from ..checks import check_arithmetic
from .data import PILOT, expand, target
from .decode import decode, tag_of
from .spans import align
from .tokens import IGNORE, LABEL_ID, encode, spans_of

# A byte-level-BPE-like split with ASCII punctuation isolated, as the tagger's tokenizer is configured.
TOKENS = re.compile(r"[!-/:-@\[-`{-~]| ?[^\W\d_]+| ?\d+| ?[^\s\w]+|\s+(?!\S)|\s+|\S")


def fixture(doc_id: str, text: str, compact: str, spans: list, classes: dict) -> dict:
    tagged = [(s, e, tag_of(p)) for s, e, p in spans]
    offsets = [(0, 0), *(m.span() for m in TOKENS.finditer(text)), (0, 0)]
    labels = [LABEL_ID["O"] if lab == IGNORE else lab for lab in encode(text, offsets, spans, classes).labels]
    gold = expand(json.loads(compact))
    return {
        "id": doc_id, "text": text, "target": compact, "spans": tagged, "classes": classes,
        "expanded": gold,
        "decoded": decode(text, tagged, classes["gst_treatment"], classes["month_first"]),
        "decoded_guess_date_order": decode(text, tagged, classes["gst_treatment"], None),
        "arithmetic_failures": check_arithmetic(gold)[0],
        "offsets": offsets, "labels": labels, "read_spans": spans_of(text, offsets, labels),
    }


def pilot_rows() -> list[dict]:
    rows = []
    for line in PILOT.open(encoding="utf-8"):
        r = json.loads(line)
        spans = sorted([s, e, p] for p, (s, e) in align(r["label"], r["text"]).spans.items())
        classes = {"gst_treatment": r["label"]["gst"]["treatment"], "month_first": r["meta"].get("locale") == "US"}
        rows.append(fixture(r["id"], r["text"], target(r["label"]), spans, classes))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, required=True, help="a student data file (dev.jsonl)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = pilot_rows()
    for line in args.data.open(encoding="utf-8"):
        r = json.loads(line)
        rows.append(fixture(r["id"], r["text"], r["target"], r["spans"], r["classes"]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"{len(rows)} fixtures written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
