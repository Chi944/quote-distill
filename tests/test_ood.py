import importlib.util
import json
import shutil

import pytest

from quote_distill import ood
from quote_distill.checks import check_label


def _author():
    spec = importlib.util.spec_from_file_location("ood_author", ood.OOD_DIR / "author.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_committed_files_are_what_the_author_script_writes():
    docs = _author().DOCS
    assert len(docs) == 30
    assert sorted({d[1] for d in docs}) == ["AU", "MY", "NZ", "SG", "US"]
    for id_, _, _, _, body, label in docs:
        assert (ood.OOD_DIR / f"{id_}.doc.txt").read_text(encoding="utf-8") == body
        assert json.loads((ood.OOD_DIR / f"{id_}.label.json").read_text(encoding="utf-8")) == label


def test_every_label_passes_the_checks():
    for r in ood.load(ood.OOD_DIR):
        result = check_label(r["label"], r["text"], r["meta"]["locale"])
        assert result.keep, (r["id"], result.schema, result.provenance, result.unexpected)


def test_no_document_is_a_generator_or_seed_text():
    texts = {r["text"] for r in ood.load(ood.SEEDS_DIR)}
    assert not texts & {r["text"] for r in ood.load(ood.OOD_DIR)}


def test_export_writes_both_sets(tmp_path):
    ood_path, seeds_path = ood.export(tmp_path)
    rows = [json.loads(line) for line in ood_path.open(encoding="utf-8")]
    assert len(rows) == 30 and {r["split"] for r in rows} == {"ood"}
    assert len(seeds_path.read_text(encoding="utf-8").splitlines()) == 5


def test_freeze_then_verify_catches_edits(tmp_path):
    folder = tmp_path / "ood"
    shutil.copytree(ood.OOD_DIR, folder)
    (folder / "MANIFEST.sha256").unlink(missing_ok=True)
    assert ood.verify(folder) and "not frozen" in ood.verify(folder)[0]
    ood.freeze(folder)
    assert ood.verify(folder) == []
    doc = folder / "ood-07.doc.txt"
    doc.write_text(doc.read_text(encoding="utf-8").replace("1,912.90", "1,912.99"), encoding="utf-8")
    assert ood.verify(folder) == ["ood-07: changed since the freeze"]


def test_predictions_must_cover_every_document(tmp_path):
    path = tmp_path / "p.jsonl"
    path.write_text(json.dumps({"id": "ood-01", "output": None, "latency_ms": 5.0}) + "\n", encoding="utf-8")
    preds, latency = ood.predictions(path, ["ood-01"])
    assert preds == {"ood-01": None} and latency == [5.0]
    with pytest.raises(ood.Refusal):
        ood.predictions(path, ["ood-01", "ood-02"])


def test_markers_appear_once_in_readme_and_doc():
    for path in (ood.README, ood.OOD_DOC):
        text = path.read_text(encoding="utf-8")
        assert text.count(ood.OOD_START) == 1 and text.count(ood.OOD_END) == 1
