import json
from decimal import Decimal
from pathlib import Path

import pytest

from quote_distill.metrics import score_document
from quote_distill.teacher import spend
from quote_distill.teacher.batch import build_requests, collect, estimate
from quote_distill.teacher.pilot import FAMILIES, PER_FAMILY, load_seeds, select
from quote_distill.teacher.prompt import parse_output, system_prompt

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "data" / "pilot"


def pilot_docs() -> list[dict]:
    return [json.loads(line) for line in open(PILOT / "pilot-20.jsonl", encoding="utf-8")]


def test_committed_pilot_is_reproducible():
    from quote_distill.generator.build import generate

    manifest = json.loads((PILOT / "manifest.json").read_text(encoding="utf-8"))
    pool, _ = generate(manifest["pool"]["size"], manifest["pool"]["seed"], manifest["pool"]["split"])
    again = load_seeds() + select([r for r in pool if not r.get("rejected")])
    assert [d["meta"]["text_sha256"] for d in again] == [d["text_sha256"] for d in manifest["documents"]]
    assert [d["meta"]["text_sha256"] for d in pilot_docs()] == [d["text_sha256"] for d in manifest["documents"]]


def test_pilot_composition():
    docs = pilot_docs()
    assert len(docs) == 20 and len({d["id"] for d in docs}) == 20
    assert all(d["split"] in ("seed", "dev") for d in docs)
    families = [d["meta"]["family"] for d in docs]
    assert families.count("hand-written seed") == 5
    for family, (required, _) in FAMILIES.items():
        members = [d for d in docs if d["meta"]["family"] == family]
        assert len(members) == PER_FAMILY
        assert all(required <= set(d["meta"]["features"]) for d in members)


def test_system_prompt_carries_rules_and_schema():
    s = system_prompt()
    assert "not_stated" in s and "Canonical arithmetic" in s and '"$schema"' in s
    assert "](" not in s  # repository links stripped


def test_parse_output_is_strict():
    assert parse_output('{"a": 1}') == ({"a": 1}, None)
    assert parse_output('```json\n{"a": 1}\n```') == (None, "wrapped in a code fence")
    assert parse_output("Here you go: {}")[0] is None
    assert parse_output("[1]") == (None, "JSON is a list, not an object")


def test_requests_and_estimate():
    docs = pilot_docs()
    reqs = build_requests(docs, "claude-haiku-5-5", "low", 8000)
    assert [r["custom_id"] for r in reqs] == [d["id"] for d in docs]
    assert len({r["params"]["system"] for r in reqs}) == 1
    assert reqs[0]["params"]["output_config"] == {"effort": "low"}
    est = estimate(reqs, docs, "claude-haiku-5-5")
    assert est["worst_output_tokens"] == 160_000
    assert est["cost"] < Decimal("0.05") and est["worst_cost"] < Decimal("0.05")
    with pytest.raises(ValueError):
        build_requests(docs + docs[:1], "claude-haiku-5-5", "low", 8000)


def test_cost_arithmetic():
    assert spend.cost("claude-haiku-5-5", 1_000_000, 1_000_000) == Decimal("0.30")
    assert spend.cost("claude-sonnet-5-5", 90_000, 54_000) == Decimal("0.36")


def test_spend_log_round_trip(tmp_path):
    path = tmp_path / "spend.md"
    rule = "|---" * 11 + "|"
    path.write_text(f"# Log\n\n{spend.HEADER}\n{rule}\n\nNo jobs yet. Running total: **$0.00**.\n")
    row = spend.Row("2026-10-19", "pilot-haiku-1", "claude-haiku-5-5", "batch", 20, "~81,915", "~47,967",
                    "$0.0161 (worst $0.0441)", "pending", "", "2026-10-18")
    spend.log_estimate(row, path)
    assert spend.find("pilot-haiku-1", path).actual_cost == "pending"
    with pytest.raises(ValueError):
        spend.log_estimate(row, path)
    spend.log_actual("pilot-haiku-1", 80_000, 40_000, Decimal("0.014"), path)
    text = path.read_text()
    assert "| $0.0140 | $0.0140 |" in text and "Running total: **$0.0140** of US$50." in text
    assert "No jobs yet" not in text
    with pytest.raises(ValueError):
        spend.log_actual("never-logged", 1, 1, Decimal("0"), path)


def test_collect_scores_by_custom_id():
    docs = {d["id"]: d for d in pilot_docs()}
    good = json.dumps(docs["seed-02"]["label"])

    def ok(cid, text, stop="end_turn"):
        return {"custom_id": cid, "result": {"type": "succeeded", "message": {
            "content": [{"type": "thinking", "thinking": "..."}, {"type": "text", "text": text}], "stop_reason": stop,
            "usage": {"input_tokens": 4000, "output_tokens": 2000}}}}

    lines = [ok("seed-02", good), ok("seed-01", "```json\n{}\n```"), ok("seed-03", '{"sup', stop="max_tokens"),
             {"custom_id": "seed-04", "result": {"type": "errored", "error": {"type": "overloaded_error"}}}]
    out = collect("t", lines, "claude-haiku-5-5")
    preds = {p["id"]: p for p in out["predictions"]}
    assert score_document("seed-02", docs["seed-02"]["label"], preds["seed-02"]["output"]).exact
    assert preds["seed-01"]["output"] is None and preds["seed-01"]["problem"] == "wrapped in a code fence"
    assert preds["seed-03"]["problem"].startswith("hit max_tokens")
    assert preds["seed-04"]["problem"] == "request errored"
    assert out["outcomes"] == {"succeeded": 3, "errored": 1}
    assert out["usage"]["input_tokens"] == 12_000
    assert out["cost"] == spend.cost("claude-haiku-5-5", 12_000, 6_000)


def test_test_set_reaches_the_teacher_only_as_an_evaluation_job(monkeypatch, tmp_path):
    from quote_distill.teacher import batch

    monkeypatch.setattr(batch, "RUNS", tmp_path)
    test_docs = str(ROOT / "data" / "test" / "docs.jsonl")
    with pytest.raises(SystemExit, match="only for the final evaluation"):
        batch.main(["plan", "--job", "x", "--docs", test_docs])
    with pytest.raises(SystemExit, match="only frozen test-set documents"):
        batch.main(["plan", "--job", "x", "--docs", str(PILOT / "pilot-20.jsonl"), "--evaluation"])
    batch.main(["plan", "--job", "eval", "--docs", test_docs, "--evaluation"])
    assert json.loads((tmp_path / "eval" / "plan.json").read_text())["evaluation"] is True
