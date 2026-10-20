"""Character spans to per-token labels for the encoder tagger, and back.

The tagger is a plain token classifier, so it exports to ONNX and runs in the browser like any other. Each text token
gets O, B-<tag> or I-<tag>. The two document-level classes (GST treatment and date order) are one combined label on
the first special token ([CLS]); `read` takes the best document label there and the best span label everywhere else.

Nothing here loads a tokenizer: callers pass each token's character offsets, with (0, 0) for special tokens. That
keeps the conversion testable without the Hugging Face Hub and identical in training and evaluation.
"""

from dataclasses import dataclass

from .decode import TAGS, TREATMENTS, decode, tag_of

IGNORE = -100
SPAN_LABELS = ("O", *(f"{p}-{t}" for t in TAGS for p in "BI"))
DOC_LABELS = tuple(f"DOC-{t}-{'M' if mf else 'D'}" for t in TREATMENTS for mf in (False, True))
LABELS = SPAN_LABELS + DOC_LABELS
LABEL_ID = {label: i for i, label in enumerate(LABELS)}


def doc_label(treatment: str, month_first: bool) -> int:
    return LABEL_ID[f"DOC-{treatment}-{'M' if month_first else 'D'}"]


def _trim(text: str, s: int, e: int) -> tuple[int, int]:
    """A token's offsets without surrounding whitespace (byte-level BPE tokens may carry a leading space)."""
    while s < e and text[s].isspace():
        s += 1
    while e > s and text[e - 1].isspace():
        e -= 1
    return s, e


@dataclass
class Encoded:
    labels: list[int]
    clashes: int  # tokens that straddle two spans; each keeps the first span's label
    lost: int  # spans with no token at all (cut off by truncation)


def encode(text: str, offsets: list[tuple[int, int]], spans: list, classes: dict) -> Encoded:
    """Labels for one tokenised document. `spans` is a record's [start, end, field path] list."""
    labels = [IGNORE] * len(offsets)
    special = [i for i, (s, e) in enumerate(offsets) if s == e]
    if special:
        labels[special[0]] = doc_label(classes["gst_treatment"], classes["month_first"])
    trimmed = [_trim(text, s, e) for s, e in offsets]
    for i, (s, e) in enumerate(trimmed):
        if s != e:  # whitespace-only tokens stay unlabelled and don't break a span
            labels[i] = LABEL_ID["O"]
    clashes = lost = 0
    for s, e, path in sorted(spans):
        tag = tag_of(path)
        hit = [i for i, (ts, te) in enumerate(trimmed) if ts != te and ts < e and te > s]
        if not hit:
            lost += 1
            continue
        for k, i in enumerate(hit):
            if labels[i] != LABEL_ID["O"]:
                clashes += 1
                continue
            labels[i] = LABEL_ID[f"{'B' if k == 0 else 'I'}-{tag}"]
    return Encoded(labels, clashes, lost)


def spans_of(text: str, offsets: list[tuple[int, int]], label_ids: list[int]) -> list[tuple[int, int, str]]:
    """Read tagged character spans back from one label per token. An I- that doesn't continue its tag opens a span;
    whitespace-only tokens are skipped."""
    out, cur = [], None
    for (s, e), lid in zip(offsets, label_ids, strict=True):
        if s == e:
            continue
        s, e = _trim(text, s, e)
        if s == e:
            continue
        name = LABELS[lid] if 0 <= lid < len(SPAN_LABELS) else "O"
        if name == "O":
            cur = None
            continue
        kind, tag = name.split("-", 1)
        if kind == "I" and cur is not None and cur[2] == tag:
            cur[1] = e
            continue
        cur = [s, e, tag]
        out.append(cur)
    return [tuple(c) for c in out]


def read(text: str, offsets: list[tuple[int, int]], logits) -> dict:
    """A schema label from one document's logits (tokens x LABELS), via decode()."""
    n_span = len(SPAN_LABELS)
    special = [i for i, (s, e) in enumerate(offsets) if s == e]
    ids = [max(range(n_span), key=row.__getitem__) for row in map(list, logits)]
    if special:
        row = list(logits[special[0]])
        _, treatment, mf = LABELS[max(range(n_span, len(LABELS)), key=row.__getitem__)].split("-")
    else:
        treatment, mf = "not_stated", None
    return decode(text, spans_of(text, offsets, ids), treatment, None if mf is None else mf == "M")


def round_trip(text: str, offsets: list[tuple[int, int]], spans: list, classes: dict) -> dict:
    """What a perfect tagger would produce through this tokenisation: gold labels, read back and decoded."""
    enc = encode(text, offsets, spans, classes)
    ids = [LABEL_ID["O"] if lab == IGNORE else lab for lab in enc.labels]
    return decode(text, spans_of(text, offsets, ids), classes["gst_treatment"], classes["month_first"])
