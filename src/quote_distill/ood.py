"""The out-of-distribution check: the students on quotations the generator didn't write (docs/ood.md).

    python -m quote_distill.ood export --out runs/ood          # data/ood and data/seeds as JSONL for student/evaluate.py
    python -m quote_distill.ood freeze                         # after the hand check: data/ood/MANIFEST.sha256
    python -m quote_distill.ood verify                         # CI: fails on any change after the freeze
    python -m quote_distill.ood report --results results/ood   # docs/ood.md and the README's second table

The 30 documents in data/ood are written by hand (data/ood/author.py). The 5 hand-written seeds are scored beside
them, because they are the only other documents the generator didn't write and the teacher's pilot already answered
them. The teacher can't be run on data/ood (the credits are gone), so its row covers the seeds only.
"""

import argparse
import json
import sys
from pathlib import Path

from .evaluation import System, _f1, _gallery, _latency, per_field, score
from .metrics import Ratio
from .splits import doc_hash

ROOT = Path(__file__).resolve().parents[2]
OOD_DIR = ROOT / "data" / "ood"
SEEDS_DIR = ROOT / "data" / "seeds"
OOD_DOC = ROOT / "docs" / "ood.md"
README = ROOT / "README.md"
TEACHER_SEEDS = ROOT / "results" / "teacher" / "pilot-session-haiku-1" / "predictions.jsonl"
OOD_START, OOD_END = "<!-- ood:start -->", "<!-- ood:end -->"
NAMES = {"teacher": "Teacher: Claude Haiku (pilot run)", "tagger": "Student: encoder tagger",
         "generative": "Student: generative"}


class Refusal(Exception):
    pass


def replace_between(text: str, body: str) -> str:
    if text.count(OOD_START) != 1 or text.count(OOD_END) != 1:
        raise Refusal(f"expected one {OOD_START} and one {OOD_END}")
    before, rest = text.split(OOD_START)
    return before + OOD_START + "\n" + body + OOD_END + rest.split(OOD_END, 1)[1]


def load(folder: Path) -> list[dict]:
    """A manifest folder (data/ood, data/seeds) as records with id, split, text, label and meta."""
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    return [{"id": e["id"], "split": folder.name, "meta": {"locale": e["locale"], "layout": e["layout"]},
             "text": (folder / f"{e['id']}.doc.txt").read_text(encoding="utf-8"),
             "label": json.loads((folder / f"{e['id']}.label.json").read_text(encoding="utf-8"))}
            for e in manifest["seeds"]]


def export(out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for folder, name in ((OOD_DIR, "ood"), (SEEDS_DIR, "seeds")):
        path = out / f"{name}.jsonl"
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in load(folder)), encoding="utf-8")
        written.append(path)
    return written


def freeze(folder: Path = OOD_DIR) -> None:
    (folder / "MANIFEST.sha256").write_text("".join(f"{doc_hash(r)}  {r['id']}\n" for r in load(folder)), encoding="utf-8")


def verify(folder: Path = OOD_DIR) -> list[str]:
    manifest = folder / "MANIFEST.sha256"
    if not manifest.exists():
        return ["not frozen yet: run `python -m quote_distill.ood freeze` after the hand check"]
    expected = dict(reversed(line.split("  ", 1)) for line in manifest.read_text(encoding="utf-8").splitlines() if line)
    seen = {r["id"]: doc_hash(r) for r in load(folder)}
    problems = [f"{i}: changed since the freeze" for i in seen if i in expected and seen[i] != expected[i]]
    problems += [f"{i}: added after the freeze" for i in seen if i not in expected]
    problems += [f"{i}: removed after the freeze" for i in expected if i not in seen]
    return problems


def predictions(path: Path, ids: list[str]) -> tuple[dict, list[float]]:
    rows = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            rows[r["id"]] = r
    missing = [i for i in ids if i not in rows]
    if missing:
        raise Refusal(f"{path}: no prediction for {len(missing)} documents (e.g. {missing[:3]})")
    return ({i: rows[i].get("output") for i in ids},
            [rows[i]["latency_ms"] for i in ids if isinstance(rows[i].get("latency_ms"), int | float)])


def table(systems: list[System], reports: dict) -> list[str]:
    out = ["| Model | Per-field exact match | Line-item F1 | Arithmetic agrees with gold | Whole document exact"
           " | Latency per doc (CPU) |", "|---|---|---|---|---|---|"]
    for s in systems:
        r = reports[s.key]
        out.append(f"| {s.name} | {per_field(r)} | {_f1(r['line_items']['f1'])} | {r['arithmetic_agrees']}"
                   f" | {r['exact_documents']} | {_latency(s.latency_ms, r['documents'])} |")
    return out


def by_locale(gold: list[dict], systems: list[System], scored: dict) -> list[str]:
    out = ["| Locale | n | " + " | ".join(s.name for s in systems) + " |", "|---|---|" + "---|" * len(systems)]
    for loc in sorted({g["meta"]["locale"] for g in gold}):
        idx = [i for i, g in enumerate(gold) if g["meta"]["locale"] == loc]
        out.append(f"| {loc} | {len(idx)} | " + " | ".join(
            str(Ratio(sum(scored[s.key][i].exact for i in idx), len(idx))) for s in systems) + " |")
    return out


def section(title: str, gold: list[dict], systems: list[System]) -> tuple[list[str], list[str]]:
    reports, scored = {}, {}
    for s in systems:
        reports[s.key], scored[s.key] = score(s, gold)
    body = [f"### {title}", "", *table(systems, reports), "", "Whole-document exact by locale:", "",
            *by_locale(gold, systems, scored), ""]
    for s in systems:
        body += [*_gallery(s.name, scored[s.key]), ""]
    return body, table(systems, reports)


def report(results: Path) -> list[str]:
    problems = verify()
    if problems:
        raise Refusal("data/ood isn't as frozen after the hand check: " + "; ".join(problems[:5]))
    out, readme = ["Every rate is numerator/denominator; a missing or unparseable output counts as wrong in every "
                   "field. Latency is onnxruntime on the scoring machine's CPU.", ""], []
    for name, folder, title in (("ood", OOD_DIR, "Hand-written, out-of-distribution (30 documents)"),
                                ("seeds", SEEDS_DIR, "Hand-written seeds (5 documents)")):
        gold = load(folder)
        ids = [g["id"] for g in gold]
        systems = []
        for key in ("teacher", "tagger", "generative"):
            path = TEACHER_SEEDS if key == "teacher" else results / name / f"predictions-{key}.jsonl"
            if key == "teacher" and name != "seeds":
                continue
            preds, latency = predictions(path, ids)
            systems.append(System(key, NAMES[key], path, preds, latency if key != "teacher" else [], ""))
        body, tab = section(title, gold, systems)
        out += body
        readme += [f"**{title}**", "", *tab, ""]
    OOD_DOC.write_text(replace_between(OOD_DOC.read_text(encoding="utf-8"), "\n".join(out).rstrip() + "\n"),
                       encoding="utf-8")
    README.write_text(replace_between(README.read_text(encoding="utf-8"), "\n".join(readme).rstrip() + "\n"),
                      encoding="utf-8")
    return [str(OOD_DOC), str(README)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("export").add_argument("--out", type=Path, required=True)
    sub.add_parser("freeze")
    sub.add_parser("verify")
    sub.add_parser("report").add_argument("--results", type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        if args.cmd == "export":
            print("wrote", ", ".join(map(str, export(args.out))))
        elif args.cmd == "freeze":
            freeze()
            print("froze", OOD_DIR / "MANIFEST.sha256")
        elif args.cmd == "verify":
            problems = verify()
            print("\n".join(problems) or "data/ood is as frozen")
            return 1 if problems else 0
        else:
            print("wrote", ", ".join(report(args.results)))
    except Refusal as e:
        print(f"refusing: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
