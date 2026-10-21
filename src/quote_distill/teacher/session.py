"""Run the teacher inside a Claude Code cloud session, paid from cloud session credits instead of an API key.

    python -m quote_distill.teacher.session prepare --job pilot-session-haiku-1 --docs data/pilot/pilot-20.jsonl
    (the session runs each document through a fresh subagent and saves its reply; see docs/teacher-session.md)
    python -m quote_distill.teacher.session collect --job pilot-session-haiku-1

`prepare` writes one self-contained task per document to runs/<job>/tasks/ (git-ignored): the same system prompt
and user turn the Batches API would send, joined into a single message because a subagent takes no system prompt.
Replies go verbatim into results/teacher/<job>/outputs/<id>.txt, which is committed so the run can be checked.
`collect` parses them with the same strict parser as the API path and writes predictions.jsonl beside them.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .batch import check_split
from .prompt import parse_output, prompt_sha256, system_prompt, user_turn

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "runs"
RESULTS = ROOT / "results" / "teacher"

TASK = """{system}

---

Extract the quotation below. Reply with the JSON object only: no code fence, no commentary. Do not use any tools.

{user}
"""


def task_text(doc: dict) -> str:
    return TASK.format(system=system_prompt(), user=user_turn(doc["text"]))


def prepare(job: str, docs_path: Path, model: str, evaluation: bool) -> dict:
    docs = [json.loads(line) for line in open(docs_path, encoding="utf-8")]
    check_split(docs, evaluation)
    if len({d["id"] for d in docs}) != len(docs):
        sys.exit("refusing: duplicate document ids")
    tasks = RUNS / job / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    for d in docs:
        (tasks / f"{d['id']}.txt").write_text(task_text(d), encoding="utf-8")
    out = RESULTS / job
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    plan = {"job": job, "runner": "claude-code-session", "subagent_model": model, "evaluation": evaluation,
            "docs": str(docs_path), "ids": [d["id"] for d in docs], "prompt_sha256": prompt_sha256(),
            "prepared": date.today().isoformat()}
    (out / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return plan


def collect(job: str) -> dict:
    out = RESULTS / job
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    if plan["prompt_sha256"] != prompt_sha256():
        sys.exit("refusing: the teacher prompt changed after this job was prepared")
    preds, missing = [], []
    for doc_id in plan["ids"]:
        path = out / "outputs" / f"{doc_id}.txt"
        if not path.exists():
            missing.append(doc_id)
            preds.append({"id": doc_id, "output": None, "problem": "no reply saved"})
            continue
        text = path.read_text(encoding="utf-8")
        label, problem = parse_output(text.strip())
        preds.append({"id": doc_id, "output": label, "problem": problem})
    with open(out / "predictions.jsonl", "w", encoding="utf-8") as f:
        for row in preds:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"n": len(preds), "parsed": sum(p["output"] is not None for p in preds), "missing": missing}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Teacher runs inside a Claude Code cloud session.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("prepare")
    sp.add_argument("--job", required=True)
    sp.add_argument("--docs", type=Path, required=True)
    sp.add_argument("--model", choices=["haiku", "sonnet"], default="haiku", help="subagent model")
    sp.add_argument("--evaluation", action="store_true",
                    help="final teacher baseline on the frozen test set; never for prompt tuning")
    sc = sub.add_parser("collect")
    sc.add_argument("--job", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "prepare":
        plan = prepare(args.job, args.docs, args.model, args.evaluation)
        print(f"{args.job}: {len(plan['ids'])} tasks in {RUNS / args.job / 'tasks'}, prompt {plan['prompt_sha256'][:12]}")
        print(f"save each reply to {RESULTS / args.job / 'outputs'}/<id>.txt")
    else:
        r = collect(args.job)
        print(f"{args.job}: parsed {r['parsed']}/{r['n']}; no reply saved for {len(r['missing'])}")
        plan = json.loads((RESULTS / args.job / "plan.json").read_text(encoding="utf-8"))
        print(f"score with: quote-distill-score --gold {plan['docs']} --pred {RESULTS / args.job / 'predictions.jsonl'}"
              " --gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
