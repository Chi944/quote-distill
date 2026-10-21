import copy
import json
from pathlib import Path

import pytest

from quote_distill.metrics import CRITICAL_FIELDS, DOC_FIELDS, Ratio, aggregate, score_document

SEEDS = Path(__file__).resolve().parents[1] / "data" / "seeds"


def seed(n: int) -> dict:
    return json.loads((SEEDS / f"seed-0{n}.label.json").read_text(encoding="utf-8"))


@pytest.fixture
def gold():
    return seed(2)


def test_gold_scores_perfectly_on_every_seed():
    scores = [score_document(f"s{n}", seed(n), seed(n)) for n in range(1, 6)]
    r = aggregate(scores)
    assert r["schema_valid"] == Ratio(5, 5)
    assert r["critical_fields"] == Ratio(45, 45)
    assert all(v == Ratio(5, 5) for v in r["fields"].values())
    assert r["line_items"]["f1"] == 1.0
    assert r["invented"].n == 0 and r["invented"].d > 0
    assert r["arithmetic_agrees"] == Ratio(5, 5)
    assert r["exact_documents"] == Ratio(5, 5)
    assert r["failing_documents"] == []


def test_raw_is_never_scored(gold):
    pred = copy.deepcopy(gold)
    for line in pred["line_items"]:
        for f in line.values():
            f.pop("raw", None)
    pred["total"]["raw"] = "something else"
    assert score_document("d", gold, pred).exact


def test_whitespace_and_payment_terms_normalised(gold):
    pred = copy.deepcopy(gold)
    pred["supplier"]["value"] = "Bramblewood  Civil Supplies Pty Ltd"
    pred["payment_terms"]["value"] = "30 Days End of Month."
    s = score_document("d", gold, pred)
    assert s.fields["supplier"] and s.fields["payment_terms"]


def test_money_format_is_exact(gold):
    pred = copy.deepcopy(gold)
    pred["total"]["value"] = "6426.350"
    s = score_document("d", gold, pred)
    assert not s.fields["total"] and not s.schema_valid and not s.exact


def test_one_wrong_line_field(gold):
    pred = copy.deepcopy(gold)
    pred["line_items"][1]["unit"]["value"] = "each"
    s = score_document("d", gold, pred)
    assert (s.lines_tp, s.lines_gold, s.lines_pred) == (3, 4, 4)
    assert s.line_fields["unit"] == Ratio(3, 4)
    assert s.line_fields["line_total"] == Ratio(4, 4)
    assert all(s.fields.values()) and not s.exact
    assert s.mismatches == [("line_items[1].unit", ("stated", "sheet"), ("stated", "each"))]
    r = aggregate([s])
    assert r["line_items"]["f1"] == pytest.approx(0.75)


def test_lines_matched_as_multiset_but_positions_scored(gold):
    pred = copy.deepcopy(gold)
    pred["line_items"].reverse()
    s = score_document("d", gold, pred)
    assert s.lines_tp == 4  # F1 ignores order
    assert s.line_fields["description"] == Ratio(0, 4)  # per-field accuracy is by position
    assert not s.exact


def test_missing_and_extra_lines(gold):
    dropped = copy.deepcopy(gold)
    dropped["line_items"].pop()
    s = score_document("d", gold, dropped)
    assert (s.lines_tp, s.lines_gold, s.lines_pred) == (3, 4, 3)
    assert s.line_fields["description"] == Ratio(3, 4)
    extra = copy.deepcopy(gold)
    extra["line_items"].append(copy.deepcopy(gold["line_items"][0]))
    s = score_document("d", gold, extra)
    assert (s.lines_tp, s.lines_gold, s.lines_pred) == (4, 4, 5)
    assert s.line_fields["description"] == Ratio(4, 5)


def test_invented_and_omitted(gold):
    pred = copy.deepcopy(gold)
    pred["line_items"][0]["discount"] = {"state": "stated", "kind": "percent", "value": "5", "raw": "5%"}
    pred["validity"] = {"state": "not_stated"}
    s = score_document("d", gold, pred)
    assert s.invented == ["line_items[0].discount"]
    assert s.omitted == ["validity"]


def test_discount_kind_matters(gold):
    pred = copy.deepcopy(gold)
    pred["line_items"][2]["discount"]["kind"] = "percent"
    assert not score_document("d", gold, pred).exact


def test_teacher_that_fixes_a_supplier_error_disagrees():
    gold = seed(4)  # prints 4 x $18.75 = $76.00; the label keeps the supplier's mistake
    assert score_document("g", gold, gold).gold_failures == ["line[1].line_total"]
    fixed_line = copy.deepcopy(gold)
    fixed_line["line_items"][1]["line_total"]["value"] = "75.00"
    s = score_document("f", gold, fixed_line)
    assert s.pred_failures == ["subtotal"] and not s.arithmetic_agrees
    assert s.line_fields["line_total"] == Ratio(4, 5)
    fixed_all = copy.deepcopy(fixed_line)
    fixed_all["subtotal"]["value"] = fixed_all["total"]["value"] = "608.00"
    s = score_document("f", gold, fixed_all)
    assert s.pred_failures == [] and not s.arithmetic_agrees
    r = aggregate([s])
    assert r["arithmetic_consistent"] == Ratio(1, 1) and r["arithmetic_agrees"] == Ratio(0, 1)


def test_unparseable_prediction_scores_zero_with_denominators(gold):
    s = score_document("d", gold, None)
    assert not s.parsed and not s.schema_valid and s.pred_failures is None
    r = aggregate([s])
    assert r["critical_fields"] == Ratio(0, len(CRITICAL_FIELDS))
    assert r["line_items"]["recall"] == Ratio(0, 4)
    assert r["line_items"]["f1"] == 0.0
    assert r["exact_documents"] == Ratio(0, 1)


def test_wrong_shapes_do_not_crash(gold):
    pred = {"supplier": "Bramblewood", "line_items": "none", "gst": None, "total": {"state": "stated", "value": 6426.35}}
    s = score_document("d", gold, pred)
    assert not s.schema_valid and not any(s.fields.values())


def test_gst_treatment_scored(gold):
    pred = copy.deepcopy(gold)
    pred["gst"]["treatment"] = "inclusive"
    s = score_document("d", gold, pred)
    assert not s.fields["gst.treatment"]
    assert sum(not v for v in s.fields.values()) == 1


def test_field_lists_are_consistent():
    assert set(CRITICAL_FIELDS) <= set(DOC_FIELDS)
    assert len(CRITICAL_FIELDS) == 9  # 20 pilot documents x 9 = 180, as in docs/pilot-plan.md


def test_ratio_formatting():
    assert str(Ratio(171, 180)) == "171/180 (95.0%)"
    assert str(Ratio(0, 0)) == "0/0 (n/a)"


def test_gates_and_report(gold):
    from quote_distill.metrics import format_report, pilot_gates

    bad = copy.deepcopy(gold)
    bad["line_items"][1]["unit"]["value"] = "each"
    scores = [score_document("ok", gold, gold), score_document("bad", gold, bad), score_document("none", gold, None)]
    r = aggregate(scores)
    results = {name: ok for name, _, ok in pilot_gates(r)}  # arithmetic agrees on 2/3, and one miss is allowed
    assert results == {"Schema-valid JSON, no repair": False, "Critical fields exact": False,
                       "Line-item F1 (all six fields)": False, "Invented values": True, "Arithmetic agrees with gold": True}
    text = format_report(r, scores, gates=True)
    assert "18/27 (66.7%)" in text  # critical fields: 9 + 9 + 0
    assert "Failing documents (2/3)" in text and "`line_items[1].unit`" in text
