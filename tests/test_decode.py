import json
from pathlib import Path

from quote_distill.metrics import score_document
from quote_distill.schema import schema_errors
from quote_distill.student.decode import TAGS, decode, parse_date, tag_of
from quote_distill.student.spans import align

ROOT = Path(__file__).resolve().parents[1]


def pilot_records() -> list[dict]:
    return [json.loads(line) for line in open(ROOT / "data" / "pilot" / "pilot-20.jsonl", encoding="utf-8")]


def gold_spans(r: dict) -> list[tuple[int, int, str]]:
    return [(s, e, tag_of(p)) for p, (s, e) in align(r["label"], r["text"]).spans.items()]


def test_gold_spans_decode_to_the_gold_label():
    for r in pilot_records():
        spans = gold_spans(r)
        assert {t for _, _, t in spans} <= set(TAGS)
        pred = decode(r["text"], spans, r["label"]["gst"]["treatment"], r["meta"].get("locale") == "US")
        assert not schema_errors(pred), r["id"]
        assert score_document(r["id"], r["label"], pred).exact, r["id"]


def test_nothing_tagged_is_not_stated_and_still_valid():
    pred = decode("Hello", [], "not_stated")
    assert not schema_errors(pred)
    assert pred["supplier"] == {"state": "not_stated"} and pred["line_items"] == [] and pred["currency"]["state"] == "not_stated"


def test_items_sharing_a_line_group_by_description():
    text = "For Bolts you'd need 3 pcs at RM2.00 each which comes to RM6.00. For Nuts you'd need 4 pcs at RM1.00 each."
    spans = [(text.index(w, start), text.index(w, start) + len(w), t) for w, t, start in [
        ("Bolts", "line_items.description", 0), ("3", "line_items.quantity", 0), ("RM6.00", "line_items.line_total", 0),
        ("Nuts", "line_items.description", 0), ("4", "line_items.quantity", 60)]]
    pred = decode(text, spans, "not_stated")
    assert [li["quantity"]["value"] for li in pred["line_items"]] == ["3", "4"]
    assert pred["line_items"][1]["line_total"] == {"state": "not_stated"}
    assert pred["currency"]["value"] == "MYR"  # read from inside a price


def test_date_order_and_credit_brackets():
    assert parse_date("05/06/2026", month_first=False).isoformat() == "2026-06-05"
    assert parse_date("05/06/2026", month_first=True).isoformat() == "2026-05-06"
    assert parse_date("Prices valid until 30 Oct 2026", month_first=False).isoformat() == "2026-10-30"
    text = "Credit (50.00)"
    pred = decode(text, [(7, 14, "total")], "not_stated")
    assert pred["total"]["value"] == "-50.00"
