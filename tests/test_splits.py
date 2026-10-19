import json
import re
import shutil
from pathlib import Path

from quote_distill.splits import N_TEST, TEST_DIR, coverage, exclude_test, freeze, load, verify

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_test_set_is_intact():
    assert verify() == []


def test_any_edit_is_caught(tmp_path):
    work = tmp_path / "test"
    shutil.copytree(TEST_DIR, work)
    records = load(work)
    records[3]["label"]["total"] = {"state": "not_stated"}
    with open(work / "docs.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    problems = verify(work)
    assert "docs.jsonl changed since it was frozen" in problems
    assert f"{records[3]['id']}: changed" in problems
    freeze(work)  # an intentional, reviewed correction re-freezes
    assert verify(work) == []


def test_every_test_label_passes_the_checks():
    from quote_distill.checks import check_label

    for r in load():
        result = check_label(r["label"], r["text"], r["meta"]["locale"], r["meta"]["expected_check_failures"])
        assert result.keep, r["id"]


def test_coverage():
    c = coverage(load())
    assert c["documents"] == N_TEST
    assert set(c["locales"].values()) == {60} and set(c["layouts"].values()) == {60}
    assert min(c["features"].values()) >= 15


def test_exclude_test_drops_test_texts():
    records = load()[:5]
    assert exclude_test(records) == []


def test_only_evaluation_code_reads_the_test_set():
    allowed = {"splits.py"}
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if path.name in allowed:
            continue
        assert not re.search(r"data/test\b|TEST_DIR|splits import .*\bload\b", text), path
