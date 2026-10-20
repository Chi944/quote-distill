import json

import pytest

from quote_distill.generator.build import generate
from quote_distill.student.evaluate import main, summarise


@pytest.fixture(scope="module")
def records():
    return generate(4, 11, "dev")[0]


def write(path, records):
    path.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    return path


def test_refuses_test_documents_without_evaluation(tmp_path, records):
    docs = write(tmp_path / "docs.jsonl", [{**records[0], "split": "test"}])
    with pytest.raises(SystemExit, match="only in the final evaluation"):
        main(["--docs", str(docs), "--tagger", "x", "--out", str(tmp_path / "out")])


def test_refuses_a_mixed_evaluation_and_a_partial_one(tmp_path, records):
    mixed = write(tmp_path / "mixed.jsonl", [{**records[0], "split": "test"}, records[1]])
    with pytest.raises(SystemExit, match="only frozen test-set documents"):
        main(["--docs", str(mixed), "--evaluation", "--tagger", "x", "--out", str(tmp_path / "out")])
    test = write(tmp_path / "test.jsonl", [{**r, "split": "test"} for r in records])
    with pytest.raises(SystemExit, match="every test document"):
        main(["--docs", str(test), "--evaluation", "--limit", "2", "--tagger", "x", "--out", str(tmp_path / "out")])


def test_summary_counts_with_denominators(tmp_path, records):
    preds = [r["label"] for r in records[:3]] + [None]
    s = summarise("tagger", records, preds, [0.1, 0.2, 0.3, 0.4], tmp_path)
    assert s["documents"] == 4
    assert s["exact_documents"] == "3/4 (75.0%)"
    assert s["per_field_exact"] == "33/44 (75.0%)"  # 11 document fields each; the unparsed one scores 0
    assert s["latency_s"]["median"] == 0.25
    assert s["readme_row"].startswith("| Student: tagger (CPU, onnxruntime) | 33/44 (75.0%) |")
    lines = (tmp_path / "predictions-tagger.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["output"] is None for line in lines] == [False, False, False, True]
    assert "Whole document exact | 3/4 (75.0%)" in (tmp_path / "report-tagger.md").read_text(encoding="utf-8")
