import copy
import json
from pathlib import Path

import pytest

from quote_distill.checks import check_label, check_seeds

SEEDS = Path(__file__).resolve().parents[1] / "data" / "seeds"
MANIFEST = {s["id"]: s for s in json.loads((SEEDS / "manifest.json").read_text(encoding="utf-8"))["seeds"]}


def load(sid):
    label = json.loads((SEEDS / f"{sid}.label.json").read_text(encoding="utf-8"))
    return label, (SEEDS / f"{sid}.doc.txt").read_text(encoding="utf-8"), MANIFEST[sid]


def run(label, text, entry):
    return check_label(label, text, entry["locale"], entry["expected_check_failures"])


def test_all_seeds_kept():
    assert check_seeds(SEEDS) == 0


@pytest.mark.parametrize("sid", sorted(MANIFEST))
def test_every_seed_field_is_machine_checked(sid):
    assert run(*load(sid)).unverified == []


def test_rejects_bankers_rounding():
    label, text, entry = load("seed-01")
    label["discounts"][0]["amount"] = {"state": "stated", "value": "24.74", "raw": "24.75"}
    r = run(label, text, entry)
    assert not r.keep and "discounts[0].amount" in r.unexpected


def test_rejects_corrected_supplier_error():
    label, text, entry = load("seed-04")
    label["line_items"][1]["line_total"]["value"] = "75.00"
    assert not run(label, text, entry).keep


def test_rejects_invented_gst_rate():
    label, text, entry = load("seed-05")
    label["gst"]["rate"] = {"state": "stated", "value": "15", "raw": "15%"}
    assert not run(label, text, entry).keep


def test_rejects_bare_dollar_as_currency():
    label, text, entry = load("seed-05")
    label["currency"] = {"state": "stated", "value": "NZD", "raw": "$"}
    assert not run(label, text, entry).keep


def test_rejects_wrong_unit_and_date():
    label, text, entry = load("seed-02")
    bad_unit = copy.deepcopy(label)
    bad_unit["line_items"][0]["unit"]["value"] = "m2"
    assert not run(bad_unit, text, entry).keep
    bad_date = copy.deepcopy(label)
    bad_date["date"]["value"] = "2026-10-16"
    assert not run(bad_date, text, entry).keep


def test_rejects_float_money():
    label, text, entry = load("seed-01")
    label["total"]["value"] = 470.15
    assert run(label, text, entry).schema
