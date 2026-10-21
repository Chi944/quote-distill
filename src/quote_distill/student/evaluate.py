"""Score the exported students: the same ONNX files the browser loads, run on CPU, scored like the teacher.

    python -m quote_distill.student.evaluate --docs data/generated/dev/docs.jsonl \
        --tagger out/tagger-onnx --generative out/generative-onnx --out runs/students-dev

For the frozen test set, pass its file with --evaluation, as for the teacher (docs/test-set.md): a job is either all
test documents with --evaluation or none. Each student is optional, since they need different extras (`train` for the
tagger, `generative` for the generative student). Writes per student a report (report-<student>.md), predictions with
a latency_ms per row (predictions-<student>.jsonl, read by `quote-distill-score --pred` and quote_distill.evaluation),
and summary.json with the model file's SHA-256 and the README row.

Latency is wall time per document on this machine's CPU through onnxruntime, one document at a time, model loading
excluded. It is not browser latency, which the demo page shows per run.
"""

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

from ..metrics import DOC_FIELDS, Ratio, aggregate, format_report, score_document

FILES = {"tagger": "model_quantized.onnx", "generative": "model_q4.onnx"}  # what the demo page loads


def run_tagger(model_dir: str, records: list[dict]) -> tuple[list[dict], list[float]]:
    from transformers import AutoTokenizer

    from .tagger import onnx_logits, predict

    tok = AutoTokenizer.from_pretrained(model_dir)
    logits = onnx_logits(str(Path(model_dir) / "onnx" / FILES["tagger"]))
    preds, times = [], []
    for r in records:
        t0 = time.perf_counter()
        preds += predict(logits, tok, [r], batch_size=1)
        times.append(time.perf_counter() - t0)
    return preds, times


def run_generative(model_dir: str, records: list[dict], max_new_tokens: int) -> tuple[list[dict | None], list[float]]:
    from transformers import AutoTokenizer

    from .generative import generate, onnx_model, parse

    tok = AutoTokenizer.from_pretrained(model_dir)
    model = onnx_model(model_dir, FILES["generative"])
    preds, times = [], []
    for r in records:
        t0 = time.perf_counter()
        (out,) = generate(model, tok, [r], batch_size=1, max_new_tokens=max_new_tokens, device="cpu")
        times.append(time.perf_counter() - t0)
        preds.append(parse(out))
    return preds, times


def sha256(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def summarise(name: str, records: list[dict], preds: list, times: list[float], out: Path, model_dir: str | None = None) -> dict:
    scores = [score_document(r["id"], r["label"], p) for r, p in zip(records, preds, strict=True)]
    report = aggregate(scores)
    (out / f"report-{name}.md").write_text(f"# {name} student\n\n" + format_report(report, scores), encoding="utf-8")
    with open(out / f"predictions-{name}.jsonl", "w", encoding="utf-8") as f:
        for r, p, t in zip(records, preds, times, strict=True):
            f.write(json.dumps({"id": r["id"], "output": p, "latency_ms": round(t * 1000, 1)}, ensure_ascii=False) + "\n")
    fields = sum((report["fields"][k] for k in DOC_FIELDS), Ratio(0, 0))
    qs = statistics.quantiles(times, n=10) if len(times) > 1 else times * 9
    li = report["line_items"]["f1"]
    summary = {
        "documents": len(records),
        "per_field_exact": str(fields),
        "line_item_f1": None if li is None else round(li, 3),
        "arithmetic_consistent": str(report["arithmetic_consistent"]),
        "arithmetic_agrees": str(report["arithmetic_agrees"]),
        "exact_documents": str(report["exact_documents"]),
        "parsed": str(report["parsed"]),
        "latency_s": {"median": round(statistics.median(times), 3), "p90": round(qs[8], 3)},
    }
    if model_dir:
        summary["model_file"] = {"name": FILES[name], "sha256": sha256(Path(model_dir) / "onnx" / FILES[name])}
    summary["readme_row"] = (f"| Student: {name} (CPU, onnxruntime) | {fields} | {summary['line_item_f1']} | "
                             f"{report['arithmetic_consistent']} | {report['exact_documents']} | "
                             f"{summary['latency_s']['median']} s median | $0 |")
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--docs", type=Path, required=True, help="JSONL of documents with id, text and label")
    ap.add_argument("--tagger", help="exported tagger folder (tagger-onnx.zip, unpacked)")
    ap.add_argument("--generative", help="exported generative folder (generative-onnx.zip, unpacked)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--evaluation", action="store_true", help="the docs are the frozen test set (final evaluation)")
    ap.add_argument("--limit", type=int, help="score only the first N documents (for a quick check; not on the test set)")
    ap.add_argument("--max-new-tokens", type=int, default=768)
    args = ap.parse_args(argv)

    records = [json.loads(line) for line in args.docs.open(encoding="utf-8")]
    has_test = any(r.get("split") == "test" for r in records)
    if has_test and not args.evaluation:
        sys.exit("refusing: test-set documents are scored only in the final evaluation (--evaluation)")
    if args.evaluation and not all(r.get("split") == "test" for r in records):
        sys.exit("refusing: an --evaluation run contains only frozen test-set documents")
    if args.evaluation and args.limit:
        sys.exit("refusing: the final evaluation scores every test document")
    if not (args.tagger or args.generative):
        sys.exit("nothing to score: pass --tagger and/or --generative")
    records = records[:args.limit] if args.limit else records

    args.out.mkdir(parents=True, exist_ok=True)
    summary = {"docs": str(args.docs), "evaluation": args.evaluation, "students": {}}
    if args.tagger:
        summary["students"]["tagger"] = summarise("tagger", records, *run_tagger(args.tagger, records), args.out, args.tagger)
    if args.generative:
        preds, times = run_generative(args.generative, records, args.max_new_tokens)
        summary["students"]["generative"] = summarise("generative", records, preds, times, args.out, args.generative)
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for name, s in summary["students"].items():
        print(f"{name}: {s['per_field_exact']} fields exact, {s['exact_documents']} documents exact, "
              f"median {s['latency_s']['median']} s/doc")
        print(s["readme_row"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
