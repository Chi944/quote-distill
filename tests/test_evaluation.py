import json
import shutil

import pytest

from quote_distill import evaluation, splits
from quote_distill.evaluation import Refusal, hand_checked, replace_between, run, teacher_cost

GOLD = splits.load()
CHECKED = "## Hand check\n\n| Date | Documents checked | Problems found | Corrections |\n|---|---|---|---|\n"


@pytest.fixture
def docs(tmp_path, monkeypatch):
    """Copies of the files the command writes, with the hand check recorded as complete."""
    for name, src in (("README", evaluation.README), ("EVALUATION_DOC", evaluation.EVALUATION_DOC)):
        dst = tmp_path / src.name
        shutil.copy(src, dst)
        monkeypatch.setattr(evaluation, name, dst)
    test_set = tmp_path / "test-set.md"
    test_set.write_text(CHECKED + "| 2026-10-25 | 150 | 0 | |\n| 2026-10-26 | 150 | 1 | x: y |\n", encoding="utf-8")
    monkeypatch.setattr(evaluation, "TEST_SET_DOC", test_set)
    return tmp_path


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def perfect(tmp_path, name="perfect", **extra):
    return write(tmp_path / name / "predictions.jsonl", [{"id": g["id"], "output": g["label"], **extra} for g in GOLD])


def empty(tmp_path, name="empty"):
    return write(tmp_path / name / "predictions.jsonl", [{"id": g["id"], "output": None} for g in GOLD])


def test_hand_check_counts_table_rows_only():
    assert hand_checked("# Test set\n\n" + CHECKED) == 0
    assert hand_checked(CHECKED + "| 2026-10-25 | 120 | 2 | a |\n| 2026-10-26 | 180 | 0 | |\n") == 300
    assert hand_checked("| 999 | 999 |\n" + CHECKED) == 0  # a table above the section doesn't count


def test_refuses_until_the_hand_check_covers_300(docs, tmp_path):
    evaluation.TEST_SET_DOC.write_text(CHECKED + "| 2026-10-25 | 299 | 0 | |\n", encoding="utf-8")
    with pytest.raises(Refusal, match="299 of 300"):
        run({"tagger": perfect(tmp_path)})
    draft = tmp_path / "draft.md"
    assert run({"tagger": perfect(tmp_path)}, draft=draft) == [str(draft)]
    assert "Draft: a pipeline check" in draft.read_text(encoding="utf-8")


def test_writes_evaluation_and_readme_between_markers(docs, tmp_path):
    readme_before = evaluation.README.read_text(encoding="utf-8")
    run({"tagger": perfect(tmp_path, latency_ms=250.0), "generative": empty(tmp_path)})
    readme = evaluation.README.read_text(encoding="utf-8")
    assert readme.split(evaluation.START)[0] == readme_before.split(evaluation.START)[0]
    assert readme.split(evaluation.END)[1] == readme_before.split(evaluation.END)[1]
    rows = [line for line in readme.splitlines() if line.startswith("| Student")]
    assert [r.split(" | ")[3:5] for r in rows] == [["300/300 (100.0%)", "300/300 (100.0%)"], ["0/300 (0.0%)", "0/300 (0.0%)"]]
    assert rows[0].endswith("| 1.000 | 300/300 (100.0%) | 300/300 (100.0%) | 250 ms median | $0 (runs in the browser) |")
    assert rows[1].endswith("| 0.000 | 0/300 (0.0%) | 0/300 (0.0%) | not measured | $0 (runs in the browser) |")
    report = evaluation.EVALUATION_DOC.read_text(encoding="utf-8")
    assert "| Whole document exact | 300/300 (100.0%) | 0/300 (0.0%) |" in report
    assert "Student: generative (in browser): 300 of 300 documents not exact" in report
    assert "Student: encoder tagger (in browser): 0 of 300 documents not exact" in report
    assert "Not run yet." not in report and report.count(evaluation.START) == 1


def test_hard_case_table_has_a_row_per_feature_with_its_count(docs, tmp_path):
    run({"tagger": perfect(tmp_path)})
    report = evaluation.EVALUATION_DOC.read_text(encoding="utf-8")
    coverage = json.loads((splits.TEST_DIR / "coverage.json").read_text(encoding="utf-8"))["features"]
    for feature, n in coverage.items():
        assert f"| `{feature}` | {n} | {n}/{n} (100.0%) |" in report


@pytest.mark.parametrize("rows, match", [
    (lambda: [{"id": g["id"], "output": None} for g in GOLD[1:]], "1 test ids missing"),
    (lambda: [{"id": g["id"], "output": None} for g in GOLD] + [{"id": "dev-1", "output": None}], "1 ids not in"),
    (lambda: [{"id": g["id"], "output": None} for g in GOLD] + [{"id": GOLD[0]["id"], "output": None}], "duplicate"),
])
def test_refuses_predictions_that_are_not_exactly_the_test_ids(docs, tmp_path, rows, match):
    with pytest.raises(Refusal, match=match):
        run({"tagger": write(tmp_path / "p.jsonl", rows())})


def test_teacher_job_must_be_an_evaluation_job_and_names_its_model(docs, tmp_path):
    preds = perfect(tmp_path, "teacher")
    (preds.parent / "plan.json").write_text(json.dumps({"evaluation": False, "subagent_model": "haiku"}), encoding="utf-8")
    with pytest.raises(Refusal, match="--evaluation"):
        run({"teacher": preds})
    (preds.parent / "plan.json").write_text(json.dumps({"evaluation": True, "subagent_model": "sonnet"}), encoding="utf-8")
    run({"teacher": preds}, teacher_usd="6.00")
    assert ("| Teacher: Claude Sonnet in a Claude Code subagent | 11208/11208 (100.0%) | 1.000 | 300/300 (100.0%)"
            " | 300/300 (100.0%) | not measured | $0.0200 ($6.00 of cloud credits / 300) |"
            ) in evaluation.README.read_text(encoding="utf-8")


def test_refuses_a_test_set_that_differs_from_its_manifest(docs, tmp_path):
    test_dir = tmp_path / "test"
    shutil.copytree(splits.TEST_DIR, test_dir)
    records = splits.load(test_dir)
    records[0]["label"]["total"] = {"state": "not_stated"}
    write(test_dir / "docs.jsonl", records)
    with pytest.raises(Refusal, match="differs from its manifest"):
        run({"tagger": perfect(tmp_path)}, test_dir=test_dir)


def test_latency_reads_in_ms_below_a_second_and_flags_partial_timing():
    assert evaluation._latency([5.2, 4.8, 6.0], 3) == "5 ms median"
    assert evaluation._latency([12_400.0, 9_800.0], 2) == "11.1 s median"
    assert evaluation._latency([300.0], 2) == "300 ms median (1 of 2 timed)"
    assert evaluation._latency([], 2) == "not measured"


def test_marker_and_cost_helpers():
    assert replace_between(f"a\n{evaluation.START}\nold\n{evaluation.END}\nb", "new\n") == \
        f"a\n{evaluation.START}\nnew\n{evaluation.END}\nb"
    with pytest.raises(Refusal):
        replace_between("no markers", "x")
    assert teacher_cost(None, 300) == "not measured"
    assert teacher_cost("4.20", 300) == "$0.0140 ($4.20 of cloud credits / 300)"


def test_committed_docs_carry_one_pair_of_markers():
    for path in (evaluation.README, evaluation.EVALUATION_DOC):
        text = path.read_text(encoding="utf-8")
        assert text.count(evaluation.START) == 1 and text.count(evaluation.END) == 1, path
