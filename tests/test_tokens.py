import json
import re
from pathlib import Path

from quote_distill.metrics import score_document
from quote_distill.student.spans import align
from quote_distill.student.tokens import DOC_LABELS, IGNORE, LABEL_ID, LABELS, SPAN_LABELS, doc_label, encode, read, round_trip, spans_of

ROOT = Path(__file__).resolve().parents[1]
# Stand-ins for a real tokenizer: byte-level BPE keeps a leading space on words and numbers. The first isolates every
# punctuation mark (what the training notebook configures); the second keeps punctuation runs such as "$." together.
ISOLATED = re.compile(r" ?[A-Za-z]+| ?\d+|[^\s\w]|\s+|\S")
RUNS = re.compile(r" ?[A-Za-z]+| ?\d+| ?[^\s\w]+|\s+(?!\S)|\s+|\S")


def offsets(text: str, pattern: re.Pattern) -> list[tuple[int, int]]:
    return [(0, 0), *(m.span() for m in pattern.finditer(text)), (0, 0)]


def pilot() -> list[dict]:
    rows = []
    for line in open(ROOT / "data" / "pilot" / "pilot-20.jsonl", encoding="utf-8"):
        r = json.loads(line)
        spans = [[s, e, p] for p, (s, e) in align(r["label"], r["text"]).spans.items()]
        classes = {"gst_treatment": r["label"]["gst"]["treatment"], "month_first": r["meta"].get("locale") == "US"}
        rows.append((r, spans, classes))
    return rows


def test_labels_are_unique_and_doc_labels_cover_every_class():
    assert len(set(LABELS)) == len(LABELS) == len(SPAN_LABELS) + len(DOC_LABELS) == 1 + 2 * 19 + 8
    assert LABELS[doc_label("inclusive", True)] == "DOC-inclusive-M"


def test_gold_labels_read_back_exact_with_isolated_punctuation():
    for r, spans, classes in pilot():
        offs = offsets(r["text"], ISOLATED)
        enc = encode(r["text"], offs, spans, classes)
        assert enc.clashes == 0 and enc.lost == 0, r["id"]
        assert score_document(r["id"], r["label"], round_trip(r["text"], offs, spans, classes)).exact, r["id"]


def test_punctuation_runs_can_cost_exactness():
    # "Amounts are in S$." makes "$." one token, so the currency span reads back as "S$." That's why the notebook
    # isolates punctuation, and why it measures this ceiling with the real tokenizer before training.
    text = "Amounts are in S$.\n"
    spans = [[text.index("S$"), text.index("S$") + 2, "$.currency"]]
    got = spans_of(text, offsets(text, RUNS), encode(text, offsets(text, RUNS), spans, {"gst_treatment": "not_stated",
                                                                                        "month_first": False}).labels)
    assert [text[s:e] for s, e, _ in got] == ["S$."]
    got = spans_of(text, offsets(text, ISOLATED), encode(text, offsets(text, ISOLATED), spans,
                                                         {"gst_treatment": "not_stated", "month_first": False}).labels)
    assert [text[s:e] for s, e, _ in got] == ["S$"]


def test_whitespace_tokens_are_ignored_and_dont_split_a_span():
    text = "Line pump hire (4hr)"
    offs = offsets(text, ISOLATED)
    enc = encode(text, offs, [[0, len(text), "$.line_items[0].description"]], {"gst_treatment": "not_stated",
                                                                               "month_first": False})
    assert enc.labels[0] == doc_label("not_stated", False) and enc.labels[-1] == IGNORE
    assert spans_of(text, offs, [LABEL_ID["O"] if lab == IGNORE else lab for lab in enc.labels]) == [
        (0, len(text), "line_items.description")]


def test_truncated_spans_are_counted_as_lost():
    r, spans, classes = pilot()[0]
    assert encode(r["text"], offsets(r["text"], ISOLATED)[:5], spans, classes).lost > 0


def test_read_takes_the_document_class_from_the_first_special_token():
    for r, spans, classes in pilot()[:5]:
        offs = offsets(r["text"], ISOLATED)
        labels = encode(r["text"], offs, spans, classes).labels
        logits = [[1.0 if j == (LABEL_ID["O"] if lab == IGNORE else lab) else 0.0 for j in range(len(LABELS))]
                  for lab in labels]
        assert score_document(r["id"], r["label"], read(r["text"], offs, logits)).exact, r["id"]
