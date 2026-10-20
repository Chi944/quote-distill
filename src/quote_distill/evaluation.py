"""The final evaluation: the teacher and both students, scored on the frozen 300-document test set.

    python -m quote_distill.evaluation --teacher results/teacher/test-session-haiku-1/predictions.jsonl \\
        --tagger results/students/tagger/predictions.jsonl --generative results/students/generative/predictions.jsonl \\
        --teacher-cost-usd 4.20

Each file is {id, output} per line, the format teacher/session.py collect and demo/scripts/predict.ts write; a
`latency_ms` per row gives the latency column. Scoring is metrics.py's, unchanged. The command writes the results
into docs/evaluation.md and the README table, between their `results` markers.

It refuses when the test set differs from its manifest, when the hand check in docs/test-set.md doesn't cover all 300
documents, when a file's ids aren't exactly the test ids, or when a teacher job wasn't prepared with --evaluation.
`--draft PATH` skips the hand-check refusal and writes the report to PATH only, for checking the pipeline; a draft
is never a reported result. This and splits.py are the only code that reads data/test.
"""

import argparse
import json
import statistics
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from . import splits
from .metrics import CRITICAL_FIELDS, Ratio, aggregate, score_document

ROOT = Path(__file__).resolve().parents[2]
TEST_SET_DOC = ROOT / "docs" / "test-set.md"
EVALUATION_DOC = ROOT / "docs" / "evaluation.md"
README = ROOT / "README.md"
START, END = "<!-- results:start -->", "<!-- results:end -->"

# Name in the tables, and cost per document when it isn't measured: the students run in the visitor's browser.
SYSTEMS = {
    "teacher": "Teacher: Claude {model} in a Claude Code subagent",
    "tagger": "Student: encoder tagger (in browser)",
    "generative": "Student: generative (in browser)",
}
STUDENT_COST = "$0 (runs in the browser)"
GALLERY_MISMATCHES = 6


class Refusal(Exception):
    pass


@dataclass
class System:
    key: str
    name: str
    path: Path
    predictions: dict
    latency_ms: list[float]
    cost: str


def hand_checked(text: str) -> int:
    """Documents recorded as checked in the hand-check table of docs/test-set.md."""
    section = text.split("## Hand check", 1)[-1]
    total = 0
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|") and len(cells) >= 2 and cells[1].isdigit():
            total += int(cells[1])
    return total


def load_predictions(path: Path, test_ids: list[str]) -> tuple[dict, list[float]]:
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise Refusal(f"{path}: duplicate ids")
    missing, extra = set(test_ids) - set(ids), set(ids) - set(test_ids)
    if missing or extra:
        raise Refusal(f"{path}: {len(missing)} test ids missing, {len(extra)} ids not in the test set"
                      f" (e.g. {sorted(missing or extra)[:3]})")
    latencies = [r["latency_ms"] for r in rows if isinstance(r.get("latency_ms"), int | float)]
    return {r["id"]: r.get("output") for r in rows}, latencies


def teacher_name(path: Path) -> str:
    """The teacher's table name from its job's plan.json, which must mark an --evaluation job."""
    plan = path.parent / "plan.json"
    if not plan.exists():
        return SYSTEMS["teacher"].format(model="(model not recorded)")
    job = json.loads(plan.read_text(encoding="utf-8"))
    if not job.get("evaluation"):
        raise Refusal(f"{plan}: the teacher job wasn't prepared with --evaluation")
    return SYSTEMS["teacher"].format(model=str(job.get("subagent_model", "(model not recorded)")).title())


def _pct(r: Ratio) -> str:
    return f"{r.n / r.d:.1%}" if r.d else "n/a"


def _f1(x) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def _latency(ms: list[float], n: int) -> str:
    if not ms:
        return "not measured"
    if len(ms) != n:
        return f"{statistics.median(ms) / 1000:.2f} s median ({len(ms)} of {n} timed)"
    return f"{statistics.median(ms) / 1000:.2f} s median"


def per_field(report: dict) -> Ratio:
    """Every document-level field plus every line field by position, micro-averaged."""
    return sum(report["fields"].values(), Ratio(0, 0)) + sum(report["line_fields"].values(), Ratio(0, 0))


def score(system: System, gold: list[dict]) -> tuple[dict, list]:
    scores = [score_document(g["id"], g["label"], system.predictions.get(g["id"])) for g in gold]
    return aggregate(scores), scores


def by_feature(gold: list[dict], scored: dict[str, list], names: dict[str, str]) -> list[str]:
    """Whole-document exact match for each hard-case feature, locale and layout, per system."""
    groups: dict[str, list[int]] = {}
    for i, g in enumerate(gold):
        for f in g["meta"]["features"]:
            groups.setdefault(f, []).append(i)
    keys = list(scored)
    out = ["| Documents with | n | " + " | ".join(names[k] for k in keys) + " |",
           "|---|---|" + "---|" * len(keys)]
    for f in sorted(groups):
        idx = groups[f]
        cells = [str(Ratio(sum(scored[k][i].exact for i in idx), len(idx))) for k in keys]
        out.append(f"| `{f}` | {len(idx)} | " + " | ".join(cells) + " |")
    return out


def _gallery(name: str, scores: list) -> list[str]:
    failing = [s for s in scores if not s.exact]
    out = [f"<details><summary>{name}: {len(failing)} of {len(scores)} documents not exact</summary>", ""]
    for s in failing:
        tag = "" if s.schema_valid else (" (schema-invalid)" if s.parsed else " (no output)")
        shown = "; ".join(f"`{p}` gold {g[1:] if len(g) > 1 else g[0]} vs {pr[1:] if len(pr) > 1 else pr[0]}"
                          for p, g, pr in s.mismatches[:GALLERY_MISMATCHES])
        more = len(s.mismatches) - GALLERY_MISMATCHES
        out.append(f"- **{s.doc_id}**{tag}: {shown}" + (f"; and {more} more" if more > 0 else ""))
    return out + ["", "</details>"]


def readme_table(systems: list[System], reports: dict) -> list[str]:
    out = ["| Model | Per-field exact match | Line-item F1 | Arithmetic agrees with gold | Whole document exact"
           " | Latency per doc | Cost per doc |", "|---|---|---|---|---|---|---|"]
    for s in systems:
        r = reports[s.key]
        out.append(f"| {s.name} | {_pct(per_field(r))} | {_f1(r['line_items']['f1'])} | {_pct(r['arithmetic_agrees'])}"
                   f" | {_pct(r['exact_documents'])} | {_latency(s.latency_ms, r['documents'])} | {s.cost} |")
    return out


def render(systems: list[System], gold: list[dict], manifest: str, draft: bool) -> tuple[str, str]:
    """(evaluation.md results section, README table), both without their markers."""
    reports, scored = {}, {}
    for s in systems:
        reports[s.key], scored[s.key] = score(s, gold)
    n = len(gold)
    out = ["**Draft: a pipeline check, not a reported result.**", ""] if draft else []
    out += [f"Scored {date.today().isoformat()} on all {n} test documents (`docs.jsonl` SHA-256 `{manifest[:12]}`).",
            "Every rate is numerator/denominator; a missing or unparseable output counts as wrong in every field.", "",
            "### Summary", "", *readme_table(systems, reports), "",
            "Per-field exact match counts every document-level field and every line-item field by position. Line-item F1"
            " counts a line only when all six of its fields match. Latency is the median per document from the run's"
            " own timing.", ""]

    def row(label, get):
        return f"| {label} | " + " | ".join(str(get(reports[s.key])) for s in systems) + " |"

    def header(first):
        return ["| " + first + " | " + " | ".join(s.name for s in systems) + " |", "|---|" + "---|" * len(systems)]

    out += ["### Measures", "", *header("Measure"),
            row("Parsed", lambda r: r["parsed"]), row("Schema-valid", lambda r: r["schema_valid"]),
            row("Critical fields exact", lambda r: r["critical_fields"]),
            row("Per-field exact", per_field),
            row("Line items: precision", lambda r: r["line_items"]["precision"]),
            row("Line items: recall", lambda r: r["line_items"]["recall"]),
            row("Line items: F1", lambda r: _f1(r["line_items"]["f1"])),
            row("Document discounts: F1", lambda r: _f1(r["document_discounts"]["f1"])),
            row("Invented values (gold not_stated, predicted stated)", lambda r: r["invented"]),
            row("Omitted values (gold stated, predicted not_stated)", lambda r: r["omitted"]),
            row("Arithmetic agrees with gold", lambda r: r["arithmetic_agrees"]),
            row("Arithmetic internally consistent", lambda r: r["arithmetic_consistent"]),
            row("Whole document exact", lambda r: r["exact_documents"]), "",
            f"Critical fields are {', '.join(f'`{f}`' for f in CRITICAL_FIELDS)}. A supplier's printed arithmetic mistake"
            " is kept in the gold label, so a model that \"fixes\" it fails *agrees with gold*; *internally consistent*"
            " can't reach 100% on this set.", "",
            "### Per field", "", *header("Field")]
    out += [row(f"`{f}`", lambda r, f=f: r["fields"][f]) for f in reports[systems[0].key]["fields"]]
    out += [row(f"`line.{f}` (by position)", lambda r, f=f: r["line_fields"].get(f, Ratio(0, 0)))
            for f in reports[systems[0].key]["line_fields"]]
    out += ["", "### By hard case", "", "Whole-document exact match among the test documents with each feature.", "",
            *by_feature(gold, scored, {s.key: s.name for s in systems}), "", "### Failure gallery", ""]
    for s in systems:
        out += [*_gallery(s.name, scored[s.key]), ""]
    sources = [f"- {s.name}: `{s.path.relative_to(ROOT) if s.path.is_relative_to(ROOT) else s.path}`" for s in systems]
    out += ["### Sources", "", *sources]
    return "\n".join(out).rstrip() + "\n", "\n".join(readme_table(systems, reports)) + "\n"


def replace_between(text: str, body: str) -> str:
    if text.count(START) != 1 or text.count(END) != 1:
        raise Refusal(f"expected one {START} and one {END}")
    before, rest = text.split(START)
    return before + START + "\n" + body + END + rest.split(END, 1)[1]


def teacher_cost(total_usd: str | None, n: int) -> str:
    if total_usd is None:
        return "not measured"
    return f"${Decimal(total_usd) / n:.4f} (${Decimal(total_usd):.2f} of cloud credits / {n})"


def run(paths: dict[str, Path], teacher_usd: str | None = None, draft: Path | None = None,
        test_dir: Path = splits.TEST_DIR) -> list[str]:
    """Score, write, and return the paths written."""
    if not paths:
        raise Refusal("give at least one of --teacher, --tagger, --generative")
    problems = splits.verify(test_dir)
    if problems:
        raise Refusal("the test set differs from its manifest: " + "; ".join(problems[:5]))
    checked = hand_checked(TEST_SET_DOC.read_text(encoding="utf-8"))
    if draft is None and checked < splits.N_TEST:
        raise Refusal(f"the hand check covers {checked} of {splits.N_TEST} documents (docs/test-set.md); "
                      "finish it, or pass --draft PATH to check the pipeline")
    gold = splits.load(test_dir)
    test_ids = [g["id"] for g in gold]
    systems = []
    for key in SYSTEMS:
        if key not in paths:
            continue
        name = teacher_name(paths[key]) if key == "teacher" else SYSTEMS[key]
        preds, latency = load_predictions(paths[key], test_ids)
        cost = teacher_cost(teacher_usd, len(gold)) if key == "teacher" else STUDENT_COST
        systems.append(System(key, name, paths[key], preds, latency, cost))
    manifest = (test_dir / "MANIFEST.sha256").read_text(encoding="utf-8").split()[0]
    section, table = render(systems, gold, manifest, draft is not None)
    if draft is not None:
        draft.parent.mkdir(parents=True, exist_ok=True)
        draft.write_text("# Evaluation (draft)\n\n" + section, encoding="utf-8")
        return [str(draft)]
    EVALUATION_DOC.write_text(replace_between(EVALUATION_DOC.read_text(encoding="utf-8"), section), encoding="utf-8")
    README.write_text(replace_between(README.read_text(encoding="utf-8"), table), encoding="utf-8")
    return [str(EVALUATION_DOC), str(README)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Score the teacher and students on the frozen test set.")
    for key in SYSTEMS:
        ap.add_argument(f"--{key}", type=Path, help=f"predictions.jsonl for the {key}")
    ap.add_argument("--teacher-cost-usd", help="the teacher job's whole credit draw in US$, from docs/spend.md")
    ap.add_argument("--draft", type=Path, help="write a draft report here and touch nothing else")
    args = ap.parse_args(argv)
    paths = {k: getattr(args, k) for k in SYSTEMS if getattr(args, k) is not None}
    try:
        written = run(paths, args.teacher_cost_usd, args.draft)
    except Refusal as e:
        print(f"refusing: {e}")
        return 1
    print("wrote " + ", ".join(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
