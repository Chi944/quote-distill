"""Train, evaluate and export the encoder tagger. Run from notebooks/train_tagger.ipynb on a free GPU.

Needs the `train` extra (torch, transformers, onnx, onnxruntime), which the rest of the package doesn't, so those
imports live inside the functions. Every result is a Ratio with its denominator; nothing here reads the frozen test set.

    tok = load_tokenizer("jhu-clsp/ettin-encoder-32m")
    print(ceiling(dev, tok))                  # what a perfect tagger would score through this tokenizer
    model = train(train_rows, dev, tok, "jhu-clsp/ettin-encoder-32m", "out/tagger")
    report = evaluate(dev, predict(torch_logits(model), tok, dev))
    export_onnx(model, tok, "out/tagger-onnx")
"""

import json
from dataclasses import dataclass

from ..metrics import Ratio, aggregate, score_document
from .data import expand
from .tokens import IGNORE, LABEL_ID, LABELS, encode, read, round_trip

MAX_LENGTH = 1024
# ASCII punctuation only: Rust (Python tokenizers) and JavaScript (transformers.js) agree on this class, while their
# `\w` differ for non-ASCII letters, which would tokenise the same text differently in the browser.
PUNCTUATION = r"[!-/:-@\[-`{-~]"


def load_tokenizer(name: str):
    """The model's fast tokenizer, with every punctuation mark split into its own piece before byte-level BPE.
    Otherwise a run like "$." in "Amounts are in S$." is one token and a span can't end between its characters.
    The change is saved in tokenizer.json, so the browser tokenizes the same way."""
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(name)
    isolate_punctuation(tok)
    return tok


def isolate_punctuation(tok) -> None:
    backend = tok.backend_tokenizer
    from tokenizers import Regex, pre_tokenizers

    split = pre_tokenizers.Split(Regex(PUNCTUATION), behavior="isolated")
    backend.pre_tokenizer = (pre_tokenizers.Sequence([split, backend.pre_tokenizer]) if backend.pre_tokenizer
                             else split)


def _offsets(tok, texts: list[str], max_length: int):
    enc = tok(texts, truncation=True, max_length=max_length, return_offsets_mapping=True,
              return_special_tokens_mask=True)
    rows = []
    for i in range(len(texts)):
        # Special tokens are (0, 0) for the tokens.py functions, whatever the tokenizer reports.
        offs = [(0, 0) if sp else tuple(o) for o, sp in zip(enc["offset_mapping"][i], enc["special_tokens_mask"][i],
                                                            strict=True)]
        rows.append((enc["input_ids"][i], offs))
    return rows


@dataclass
class Features:
    rows: list[dict]
    truncated: Ratio  # documents with text past max_length
    lost: int  # gold spans cut off by truncation
    clashes: int  # tokens that straddle two gold spans
    lengths: list[int]  # tokens per document, before truncation


def features(records: list[dict], tok, max_length: int = MAX_LENGTH) -> Features:
    """Token ids and labels for training. Records without complete spans are left out of training (none so far)."""
    usable = [r for r in records if r["spans"] is not None]
    full = tok([r["text"] for r in usable], add_special_tokens=True)["input_ids"]
    rows, lost, clashes = [], 0, 0
    for r, (ids, offs) in zip(usable, _offsets(tok, [r["text"] for r in usable], max_length), strict=True):
        enc = encode(r["text"], offs, r["spans"], r["classes"])
        lost += enc.lost
        clashes += enc.clashes
        rows.append({"input_ids": ids, "attention_mask": [1] * len(ids), "labels": enc.labels})
    lengths = [len(ids) for ids in full]
    return Features(rows, Ratio(sum(n > max_length for n in lengths), len(lengths)), lost, clashes, lengths)


def ceiling(records: list[dict], tok, max_length: int = MAX_LENGTH) -> Ratio:
    """Documents a perfect tagger would get exactly right through this tokenizer and length limit."""
    exact = 0
    for r, (_, offs) in zip(records, _offsets(tok, [r["text"] for r in records], max_length), strict=True):
        gold = expand(json.loads(r["target"]))
        exact += score_document(r["id"], gold, round_trip(r["text"], offs, r["spans"], r["classes"])).exact
    return Ratio(exact, len(records))


def train(train_records: list[dict], dev_records: list[dict], tok, base: str, out_dir: str, *, epochs: float = 4,
          lr: float = 1e-4, batch_size: int = 16, max_length: int = MAX_LENGTH, seed: int = 0, max_steps: int = -1,
          model=None):
    """Fine-tune `base` (or a given model) as a token classifier over tokens.LABELS. Returns the trained model."""
    import torch
    from transformers import AutoModelForTokenClassification, DataCollatorForTokenClassification, Trainer, TrainingArguments

    if model is None:
        model = AutoModelForTokenClassification.from_pretrained(
            base, num_labels=len(LABELS), id2label=dict(enumerate(LABELS)), label2id=LABEL_ID)
    train_f, dev_f = features(train_records, tok, max_length), features(dev_records, tok, max_length)
    steps = max_steps if max_steps > 0 else int(epochs * -(-len(train_f.rows) // batch_size))
    args = TrainingArguments(
        output_dir=out_dir, num_train_epochs=epochs, max_steps=max_steps, learning_rate=lr, warmup_steps=steps // 10,
        weight_decay=0.01, per_device_train_batch_size=batch_size, per_device_eval_batch_size=batch_size,
        eval_strategy="epoch" if max_steps < 0 else "no", save_strategy="no", logging_steps=50, seed=seed,
        fp16=torch.cuda.is_available(), report_to=[])
    trainer = Trainer(model=model, args=args, train_dataset=train_f.rows, eval_dataset=dev_f.rows,
                      data_collator=DataCollatorForTokenClassification(tok, label_pad_token_id=IGNORE))
    trainer.train()
    trainer.save_model(out_dir)
    tok.save_pretrained(out_dir)
    return model


def torch_logits(model, device: str | None = None):
    """A logits function for predict() from a PyTorch model."""
    import torch

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device).eval()

    def run(input_ids, attention_mask):
        with torch.no_grad():
            out = model(input_ids=torch.tensor(input_ids, device=device),
                        attention_mask=torch.tensor(attention_mask, device=device))
        return out.logits.float().cpu().numpy()
    return run


def onnx_logits(path: str):
    """A logits function for predict() from an exported ONNX file, run on CPU as the browser would."""
    import numpy as np
    import onnxruntime as ort

    session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])

    def run(input_ids, attention_mask):
        return session.run(["logits"], {"input_ids": np.asarray(input_ids, dtype=np.int64),
                                        "attention_mask": np.asarray(attention_mask, dtype=np.int64)})[0]
    return run


def predict(logits_fn, tok, records: list[dict], *, batch_size: int = 16, max_length: int = MAX_LENGTH) -> list[dict]:
    """Schema labels for records, one batch at a time, padded to the longest document in the batch."""
    out = []
    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        rows = _offsets(tok, [r["text"] for r in batch], max_length)
        width = max(len(ids) for ids, _ in rows)
        pad = tok.pad_token_id
        ids = [list(i) + [pad] * (width - len(i)) for i, _ in rows]
        mask = [[1] * len(i) + [0] * (width - len(i)) for i, _ in rows]
        logits = logits_fn(ids, mask)
        for r, (i, offs), lg in zip(batch, rows, logits, strict=True):
            out.append(read(r["text"], offs, lg[:len(i)]))
    return out


def evaluate(records: list[dict], preds: list[dict]) -> dict:
    """The same report as the teacher's (metrics.aggregate), against each record's gold label."""
    scores = [score_document(r["id"], expand(json.loads(r["target"])), p) for r, p in zip(records, preds, strict=True)]
    return aggregate(scores)


def export_onnx(model, tok, out_dir: str, *, opset: int = 17) -> dict:
    """Write the layout transformers.js loads: config and tokenizer files, onnx/model.onnx (float32) and
    onnx/model_quantized.onnx (int8 weights). Returns the file sizes in bytes."""
    from pathlib import Path

    import torch
    from onnxruntime.quantization import QuantType, quantize_dynamic

    out = Path(out_dir)
    (out / "onnx").mkdir(parents=True, exist_ok=True)
    model = model.to("cpu").eval()
    model.set_attn_implementation("eager")  # traces to plain ops; SDPA's shape checks would be frozen into the graph
    model.config.save_pretrained(out)
    tok.save_pretrained(out)
    # Two lengths, so padding and the attention mask are part of the traced graph.
    sample = tok(["Quotation Q-1\nTotal: $1.00", "Quotation Q-2\nDrill bit set (19 pc)  3 x $24.55\nTotal: $73.65"],
                 padding=True, return_tensors="pt")
    torch.onnx.export(model, (sample["input_ids"], sample["attention_mask"]), out / "onnx" / "model.onnx",
                      input_names=["input_ids", "attention_mask"], output_names=["logits"],
                      dynamic_axes={"input_ids": {0: "batch", 1: "tokens"}, "attention_mask": {0: "batch", 1: "tokens"},
                                    "logits": {0: "batch", 1: "tokens"}}, opset_version=opset, dynamo=False)
    quantize_dynamic(out / "onnx" / "model.onnx", out / "onnx" / "model_quantized.onnx", weight_type=QuantType.QInt8)
    return {p.name: p.stat().st_size for p in (out / "onnx").iterdir()}
