import copy
import json
from pathlib import Path

from quote_distill.checks import iter_fields
from quote_distill.normalise import collapse
from quote_distill.student.spans import align, occurrences

ROOT = Path(__file__).resolve().parents[1]


def pilot_records() -> list[dict]:
    return [json.loads(line) for line in open(ROOT / "data" / "pilot" / "pilot-20.jsonl", encoding="utf-8")]


def test_every_pilot_document_aligns_without_overlap():
    for r in pilot_records():
        a = align(r["label"], r["text"])
        assert a.complete, (r["id"], a.ambiguous, a.missing)
        raws = {p: f["raw"] for p, f in iter_fields(r["label"]) if f["state"] == "stated"}
        assert set(a.spans) | set(a.nested) == set(raws)
        for p, (s, e) in {**a.spans, **a.nested}.items():
            assert collapse(r["text"][s:e]) == collapse(raws[p])
        spans = sorted(a.spans.values())
        assert all(spans[i][1] <= spans[i + 1][0] for i in range(len(spans) - 1)), r["id"]


def test_matches_do_not_split_words_or_numbers():
    assert occurrences("RM7.91 and 12 units", "RM") == [(0, 2)]
    assert occurrences("12 units", "unit") == []
    assert occurrences("Qty 2, total 12.50", "2") == [(4, 5)]
    assert occurrences("Net  30\n days", "Net 30 days") == [(0, 13)]


def test_line_fields_stay_in_their_row_and_skip_the_row_number():
    text = "1  Drill 2 batteries   2 each   10.00   20.00\n2  Gloves   1 box   20.00   20.00\nTotal 40.00\n"

    def f(raw, value=None):
        return {"state": "stated", "value": value or raw, "raw": raw}

    line = lambda d, q, u, p, t: {"description": f(d), "quantity": f(q), "unit": f(u), "unit_price": f(p),  # noqa: E731
                                  "discount": {"state": "not_stated"}, "line_total": f(t)}
    label = {"line_items": [line("Drill 2 batteries", "2", "each", "10.00", "20.00"),
                            line("Gloves", "1", "box", "20.00", "20.00")],
             "discounts": [], "total": f("40.00")}
    a = align(label, text)
    assert a.complete
    assert text[slice(*a.spans["$.line_items[0].quantity"])] == "2" and a.spans["$.line_items[0].quantity"][0] == 23
    assert a.spans["$.line_items[1].quantity"][0] > text.index("Gloves")
    assert a.spans["$.line_items[1].unit_price"][0] < a.spans["$.line_items[1].line_total"][0]


def test_ambiguity_is_reported_not_guessed():
    r = copy.deepcopy(pilot_records()[0])
    qn = r["label"]["quote_number"]["raw"]
    r["text"] += f"\nAlso quoted under {qn}.\n"
    a = align(r["label"], r["text"])
    assert a.ambiguous == {"$.quote_number": 2} and not a.complete
