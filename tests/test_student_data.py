import json
from pathlib import Path

import pytest

from quote_distill.metrics import score_document
from quote_distill.schema import schema_errors
from quote_distill.student import data

ROOT = Path(__file__).resolve().parents[1]


def pilot_records() -> list[dict]:
    return [json.loads(line) for line in open(ROOT / "data" / "pilot" / "pilot-20.jsonl", encoding="utf-8")]


def test_compact_round_trips_every_pilot_label():
    for r in pilot_records():
        back = data.expand(json.loads(data.target(r["label"])))
        assert not schema_errors(back)
        assert score_document(r["id"], r["label"], back).exact, r["id"]


def test_compact_is_shorter_and_has_no_raw():
    label = pilot_records()[0]["label"]
    t = data.target(label)
    assert '"raw"' not in t and '"state"' not in t
    assert len(t) < len(json.dumps(label, separators=(",", ":"))) / 2


def test_expand_rejects_malformed_rows():
    c = json.loads(data.target(pilot_records()[0]["label"]))
    c["line_items"][0] = c["line_items"][0][:5]
    with pytest.raises(ValueError):
        data.expand(c)
    del c["total"]
    with pytest.raises(KeyError):
        data.expand(c)


def test_prepare_drops_pilot_documents():
    from quote_distill.generator.build import generate

    records, _ = generate(5, 99, "train")
    rows, counts = data.prepare(records + [r for r in pilot_records() if r["split"] == "dev"])
    assert counts["dropped_pilot"] == 15 and counts["kept"] == 5 and counts["targets_not_exact"] == []
    assert {r["id"] for r in rows} == {r["id"] for r in records}


def test_build_is_deterministic(tmp_path):
    for name in ("a", "b"):
        assert data.main(["--out", str(tmp_path / name), "--n-train", "12", "--n-dev", "6"]) == 0
    stats = [json.loads((tmp_path / n / "stats.json").read_text()) for n in ("a", "b")]
    assert stats[0] == stats[1]
    assert (tmp_path / "a" / "train.jsonl").read_bytes() == (tmp_path / "b" / "train.jsonl").read_bytes()
    assert stats[0]["train"]["kept"] == 12 and stats[0]["train_dev_shared_texts"] == 0
