"""Write parity fixtures for the demo's TypeScript port of expand, decode, the token reader and the arithmetic check.

    python -m quote_distill.student.fixtures --data data/generated/student/dev.jsonl --out demo/fixtures/dev.jsonl

Each line holds a document and what the Python code produces for it, so `npm test` in demo/ can require identical
output from TypeScript. Built from dev and pilot documents only; the frozen test set is never read.

With the `tokenizers` package installed it also writes demo/fixtures/tokenizer/tokenizer.json: a stand-in byte-level
BPE tokenizer shaped like the tagger's (ModernBERT's [CLS] ... [SEP], punctuation isolated as tagger.py configures it),
and each fixture gets the ids and offsets Python's tokenizer gives, so the browser's tokenisation can be checked too.
"""

import argparse
import json
import re
from pathlib import Path

from ..checks import check_arithmetic
from .data import PILOT, expand, target
from .decode import decode, tag_of
from .spans import align
from .tokens import IGNORE, LABEL_ID, encode, spans_of

# A byte-level-BPE-like split with ASCII punctuation isolated, as the tagger's tokenizer is configured.
TOKENS = re.compile(r"[!-/:-@\[-`{-~]| ?[^\W\d_]+| ?\d+| ?[^\s\w]+|\s+(?!\S)|\s+|\S")


def fixture(doc_id: str, text: str, compact: str, spans: list, classes: dict) -> dict:
    tagged = [(s, e, tag_of(p)) for s, e, p in spans]
    offsets = [(0, 0), *(m.span() for m in TOKENS.finditer(text)), (0, 0)]
    labels = [LABEL_ID["O"] if lab == IGNORE else lab for lab in encode(text, offsets, spans, classes).labels]
    gold = expand(json.loads(compact))
    return {
        "id": doc_id, "text": text, "target": compact, "spans": tagged, "classes": classes,
        "expanded": gold,
        "decoded": decode(text, tagged, classes["gst_treatment"], classes["month_first"]),
        "decoded_guess_date_order": decode(text, tagged, classes["gst_treatment"], None),
        "arithmetic_failures": check_arithmetic(gold)[0],
        "offsets": offsets, "labels": labels, "read_spans": spans_of(text, offsets, labels),
    }


def stand_in_tokenizer(texts: list[str]):
    """Byte-level BPE with [CLS] ... [SEP], like ModernBERT's, trained on the documents, punctuation isolated."""
    from tokenizers import Tokenizer, decoders, models, pre_tokenizers, processors, trainers

    from .tagger import isolate_punctuation

    tok = Tokenizer(models.BPE(unk_token="[UNK]"))
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    specials = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"]
    tok.train_from_iterator(texts, trainers.BpeTrainer(vocab_size=2000, special_tokens=specials, show_progress=False,
                                                       initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
    tok.post_processor = processors.TemplateProcessing(single="[CLS] $A [SEP]", special_tokens=[
        ("[CLS]", tok.token_to_id("[CLS]")), ("[SEP]", tok.token_to_id("[SEP]"))])
    isolate_punctuation(tok)
    return tok


def add_tokens(rows: list[dict], out_dir: Path, tokenizer: Path | None = None) -> None:
    """With `tokenizer` (a folder holding a model's tokenizer.json and tokenizer_config.json, such as an unpacked
    export), check that one instead of the stand-in."""
    import shutil

    from tokenizers import Tokenizer

    out_dir.mkdir(parents=True, exist_ok=True)
    if tokenizer is not None:
        tok = Tokenizer.from_file(str(tokenizer / "tokenizer.json"))
        for name in ("tokenizer.json", "tokenizer_config.json"):
            shutil.copy(tokenizer / name, out_dir / name)
    else:
        tok = stand_in_tokenizer([r["text"] for r in rows])
        tok.save(str(out_dir / "tokenizer.json"))
        (out_dir / "tokenizer_config.json").write_text(json.dumps({"tokenizer_class": "PreTrainedTokenizerFast",
                                                                    "cls_token": "[CLS]", "sep_token": "[SEP]",
                                                                    "pad_token": "[PAD]", "unk_token": "[UNK]",
                                                                    "mask_token": "[MASK]"}) + "\n", encoding="utf-8")
    for r in rows:
        enc = tok.encode(r["text"])
        r["token_ids"] = enc.ids
        r["token_offsets"] = [[0, 0] if sp else list(o) for o, sp in zip(enc.offsets, enc.special_tokens_mask,
                                                                          strict=True)]


def pilot_rows() -> list[dict]:
    rows = []
    for line in PILOT.open(encoding="utf-8"):
        r = json.loads(line)
        spans = sorted([s, e, p] for p, (s, e) in align(r["label"], r["text"]).spans.items())
        classes = {"gst_treatment": r["label"]["gst"]["treatment"], "month_first": r["meta"].get("locale") == "US"}
        rows.append(fixture(r["id"], r["text"], target(r["label"]), spans, classes))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, required=True, help="a student data file (dev.jsonl)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, help="a real model's tokenizer folder to check instead of the stand-in")
    args = parser.parse_args(argv)
    rows = pilot_rows()
    for line in args.data.open(encoding="utf-8"):
        r = json.loads(line)
        rows.append(fixture(r["id"], r["text"], r["target"], r["spans"], r["classes"]))
    try:
        add_tokens(rows, args.out.parent / "tokenizer", args.tokenizer)
    except ImportError:
        print("tokenizers is not installed; skipping the tokenizer fixtures")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"{len(rows)} fixtures written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
