"""Run the teacher through the Message Batches API, with the spend rules built in.

    python -m quote_distill.teacher.batch plan    --job pilot-haiku-1 --docs data/pilot/pilot-20.jsonl --model claude-haiku-5-5
    python -m quote_distill.teacher.batch log     --job pilot-haiku-1            # add the estimate row to docs/spend.md
    python -m quote_distill.teacher.batch count   --job pilot-haiku-1 --yes      # token-counting endpoint (not billed)
    python -m quote_distill.teacher.batch submit  --job pilot-haiku-1 --yes      # refuses without the spend.md row
    python -m quote_distill.teacher.batch collect --job pilot-haiku-1            # results, actual cost, predictions

`plan` and `log` make no network call. Every command that calls the API needs --yes and an ANTHROPIC_API_KEY in the
git-ignored .env file. Job files live in runs/<job>/ (git-ignored); results are keyed by custom_id, never by order.
"""

import argparse
import json
import os
import sys
import urllib.request
from datetime import date
from decimal import Decimal
from pathlib import Path

from . import spend
from .prompt import parse_output, prompt_sha256, system_prompt, user_turn

ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "runs"
API = "https://api.anthropic.com/v1"
CHARS_PER_TOKEN = 3  # conservative; `count` replaces the input estimate with exact numbers
THINKING_ALLOWANCE = 1500  # output tokens per request for adaptive thinking at effort "low"


def build_requests(docs: list[dict], model: str, effort: str, max_tokens: int) -> list[dict]:
    system = system_prompt()
    ids = [d["id"] for d in docs]
    if len(set(ids)) != len(ids):
        raise ValueError("document ids must be unique: they are the batch custom_ids")
    return [{"custom_id": d["id"],
             "params": {"model": model, "max_tokens": max_tokens, "system": system,
                        "messages": [{"role": "user", "content": user_turn(d["text"])}],
                        "output_config": {"effort": effort}}} for d in docs]


def estimate(requests: list[dict], docs: list[dict], model: str) -> dict:
    """Expected and worst-case tokens and cost. Output is sized from the gold label, which the reply must reproduce."""
    by_id = {d["id"]: d for d in docs}
    input_tokens = sum((len(r["params"]["system"]) + len(r["params"]["messages"][0]["content"])) // CHARS_PER_TOKEN + 10
                       for r in requests)
    output_tokens = sum(len(json.dumps(by_id[r["custom_id"]]["label"], ensure_ascii=False)) // CHARS_PER_TOKEN
                        + THINKING_ALLOWANCE for r in requests)
    worst_output = sum(r["params"]["max_tokens"] for r in requests)
    return {"requests": len(requests), "input_tokens": input_tokens, "output_tokens": output_tokens,
            "worst_output_tokens": worst_output, "cost": spend.cost(model, input_tokens, output_tokens),
            "worst_cost": spend.cost(model, input_tokens, worst_output), "pricing_checked": spend.PRICING_CHECKED}


def _job_dir(job: str) -> Path:
    return RUNS / job


def _load_plan(job: str) -> dict:
    path = _job_dir(job) / "plan.json"
    if not path.exists():
        sys.exit(f"no plan for {job}; run `plan` first")
    return json.loads(path.read_text(encoding="utf-8"))


def _api_key() -> str:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            if key.strip() == "ANTHROPIC_API_KEY" and value.strip():
                return value.strip().strip('"').strip("'")
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    sys.exit("ANTHROPIC_API_KEY is not set: copy .env.example to .env and fill it in")


def _call(method: str, url: str, body: dict | None = None) -> bytes:
    req = urllib.request.Request(url, method=method, data=None if body is None else json.dumps(body).encode("utf-8"),
                                 headers={"x-api-key": _api_key(), "anthropic-version": "2023-06-01",
                                          "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def _require_yes(args, what: str) -> None:
    if not args.yes:
        sys.exit(f"{what} calls the API. Re-run with --yes once the estimate has been approved.")


def cmd_plan(args) -> None:
    docs = [json.loads(line) for line in open(args.docs, encoding="utf-8")]
    if any(d.get("split") == "test" or str(d["id"]).startswith("test") for d in docs):
        sys.exit("refusing: test-set documents never go to the teacher during development")
    requests = build_requests(docs, args.model, args.effort, args.max_tokens)
    est = estimate(requests, docs, args.model)
    out = _job_dir(args.job)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "requests.jsonl", "w", encoding="utf-8") as f:
        for r in requests:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    plan = {"job": args.job, "model": args.model, "effort": args.effort, "max_tokens": args.max_tokens,
            "docs": str(args.docs), "prompt_sha256": prompt_sha256(),
            **{k: (str(v) if isinstance(v, Decimal) else v) for k, v in est.items()}}
    (out / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(f"{args.job}: {est['requests']} requests to {args.model} (batch), prompt {plan['prompt_sha256'][:12]}")
    print(f"  input  ~{est['input_tokens']:,} tokens")
    print(f"  output ~{est['output_tokens']:,} tokens (worst case {est['worst_output_tokens']:,})")
    print(f"  cost   ~{spend.usd(est['cost'])} expected, {spend.usd(est['worst_cost'])} worst case "
          f"(prices checked {est['pricing_checked']})")
    print(f"  wrote {out / 'requests.jsonl'}")


def cmd_log(args) -> None:
    p = _load_plan(args.job)
    spend.log_estimate(spend.Row(date.today().isoformat(), args.job, p["model"], "batch", p["requests"],
                                 f"~{p['input_tokens']:,}", f"~{p['output_tokens']:,}",
                                 f"{spend.usd(Decimal(p['cost']))} (worst {spend.usd(Decimal(p['worst_cost']))})",
                                 "pending", "", p["pricing_checked"]))
    print(f"added {args.job} to {spend.SPEND_PATH.relative_to(ROOT)}")


def cmd_count(args) -> None:
    _require_yes(args, "count")
    p = _load_plan(args.job)
    total = 0
    for line in open(_job_dir(args.job) / "requests.jsonl", encoding="utf-8"):
        params = json.loads(line)["params"]
        body = {k: params[k] for k in ("model", "system", "messages")}
        total += json.loads(_call("POST", f"{API}/messages/count_tokens", body))["input_tokens"]
    p["counted_input_tokens"] = total
    p["cost_with_counted_input"] = str(spend.cost(p["model"], total, p["output_tokens"]))
    (_job_dir(args.job) / "plan.json").write_text(json.dumps(p, indent=2) + "\n", encoding="utf-8")
    print(f"{args.job}: {total:,} input tokens counted (estimate was ~{p['input_tokens']:,}); "
          f"expected cost now {spend.usd(Decimal(p['cost_with_counted_input']))}")


def cmd_submit(args) -> None:
    _require_yes(args, "submit")
    p = _load_plan(args.job)
    row = spend.find(args.job)
    if row is None:
        sys.exit(f"refusing: {args.job} has no estimate row in docs/spend.md; run `log` first")
    if row.actual_cost != "pending":
        sys.exit(f"refusing: {args.job} already has an actual cost in docs/spend.md")
    if prompt_sha256() != p["prompt_sha256"]:
        sys.exit("refusing: the prompt changed since `plan`; plan and log a new job")
    batch_file = _job_dir(args.job) / "batch.json"
    if batch_file.exists():
        sys.exit(f"refusing: {args.job} was already submitted ({batch_file})")
    requests = [json.loads(line) for line in open(_job_dir(args.job) / "requests.jsonl", encoding="utf-8")]
    batch = json.loads(_call("POST", f"{API}/messages/batches", {"requests": requests}))
    batch_file.write_text(json.dumps(batch, indent=2) + "\n", encoding="utf-8")
    print(f"submitted {args.job} as {batch['id']} ({len(requests)} requests)")


def collect(job: str, results: list[dict], model: str) -> dict:
    """Turn batch result lines into predictions.jsonl rows and a usage summary (no network)."""
    preds, usage = [], {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    outcomes: dict[str, int] = {}
    for line in results:
        result = line["result"]
        outcomes[result["type"]] = outcomes.get(result["type"], 0) + 1
        if result["type"] != "succeeded":
            preds.append({"id": line["custom_id"], "output": None, "problem": f"request {result['type']}"})
            continue
        msg = result["message"]
        for k in usage:
            usage[k] += msg["usage"].get(k) or 0
        text = "".join(b["text"] for b in msg["content"] if b["type"] == "text")
        label, problem = parse_output(text)
        if msg.get("stop_reason") == "max_tokens":
            problem = "hit max_tokens" + (f"; {problem}" if problem else "")
        preds.append({"id": line["custom_id"], "output": label, "problem": problem, "stop_reason": msg.get("stop_reason"),
                      "usage": msg["usage"], "raw_text": text})
    actual = spend.cost(model, usage["input_tokens"], usage["output_tokens"], usage["cache_creation_input_tokens"],
                        usage["cache_read_input_tokens"])
    return {"predictions": preds, "usage": usage, "outcomes": outcomes, "cost": actual}


def cmd_collect(args) -> None:
    p = _load_plan(args.job)
    batch_file = _job_dir(args.job) / "batch.json"
    if not batch_file.exists():
        sys.exit(f"{args.job} was not submitted")
    batch = json.loads(_call("GET", f"{API}/messages/batches/{json.loads(batch_file.read_text())['id']}"))
    batch_file.write_text(json.dumps(batch, indent=2) + "\n", encoding="utf-8")
    if batch["processing_status"] != "ended":
        print(f"{args.job}: {batch['processing_status']}, counts {batch['request_counts']}; try again later")
        return
    lines = [json.loads(x) for x in _call("GET", batch["results_url"]).decode("utf-8").splitlines() if x.strip()]
    (_job_dir(args.job) / "results.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
    out = collect(args.job, lines, p["model"])
    with open(_job_dir(args.job) / "predictions.jsonl", "w", encoding="utf-8") as f:
        for row in out["predictions"]:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    row = spend.log_actual(args.job, out["usage"]["input_tokens"], out["usage"]["output_tokens"], out["cost"])
    print(f"{args.job}: {out['outcomes']}; usage {out['usage']}; actual cost {row.actual_cost} "
          f"(running total {row.running_total}); docs/spend.md updated")
    print(f"score with: quote-distill-score --gold {p['docs']} --pred {_job_dir(args.job) / 'predictions.jsonl'} --gates")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Teacher batch jobs with spend logging.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "log", "count", "submit", "collect"):
        sp = sub.add_parser(name)
        sp.add_argument("--job", required=True)
        if name == "plan":
            sp.add_argument("--docs", type=Path, required=True)
            sp.add_argument("--model", choices=sorted(spend.BATCH_PRICES), default="claude-haiku-5-5")
            sp.add_argument("--effort", default="low")
            sp.add_argument("--max-tokens", type=int, default=8000)
        if name in ("count", "submit"):
            sp.add_argument("--yes", action="store_true")
    args = ap.parse_args(argv)
    {"plan": cmd_plan, "log": cmd_log, "count": cmd_count, "submit": cmd_submit, "collect": cmd_collect}[args.cmd](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
