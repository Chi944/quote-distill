"""Train, evaluate and export the generative student. Run from notebooks/train_generative.ipynb on a free GPU.

The model reads a prompt holding the document and writes the compact target from student/data.py, which `expand`
turns back into a schema label. Output that isn't valid compact JSON is scored as unparsed, as with the teacher.

Needs the `generative` extra. ONNX export goes through optimum-onnx, which pins transformers below 4.58, so this
notebook installs its own versions. Heavy imports live inside the functions. Nothing here reads the frozen test set.
"""

import json

from ..metrics import Ratio
from .data import expand
from .tagger import evaluate

PROMPT = "Extract the supplier quotation below as compact JSON.\n### Quotation\n{text}\n### JSON\n"
MAX_LENGTH = 1536
MAX_NEW_TOKENS = 768


def prompt(text: str) -> str:
    return PROMPT.format(text=text)


def parse(output: str) -> dict | None:
    """A schema-shaped label from generated text, or None when it isn't one compact JSON object."""
    try:
        return expand(json.loads(output.strip()))
    except (ValueError, KeyError, TypeError, AttributeError):
        return None


def features(records: list[dict], tok, max_length: int = MAX_LENGTH) -> tuple[list[dict], Ratio, dict]:
    """Prompt + target + end-of-text, with loss on the target only. Documents longer than max_length are left out
    of training and counted. Also returns prompt and target token counts (median, p95, max)."""
    rows, too_long, p_lens, t_lens = [], 0, [], []
    for r in records:
        p = tok(prompt(r["text"]), add_special_tokens=False)["input_ids"]
        t = tok(r["target"], add_special_tokens=False)["input_ids"] + [tok.eos_token_id]
        p_lens.append(len(p))
        t_lens.append(len(t))
        if len(p) + len(t) > max_length:
            too_long += 1
            continue
        rows.append({"input_ids": p + t, "attention_mask": [1] * (len(p) + len(t)), "labels": [-100] * len(p) + t})

    def summary(xs):
        xs = sorted(xs)
        return {"median": xs[len(xs) // 2], "p95": xs[int(0.95 * (len(xs) - 1))], "max": xs[-1]}
    return rows, Ratio(too_long, len(records)), {"prompt": summary(p_lens), "target": summary(t_lens)}


def train(train_records: list[dict], tok, base: str, out_dir: str, *, epochs: float = 2, lr: float = 5e-5,
          batch_size: int = 4, grad_accum: int = 4, max_length: int = MAX_LENGTH, seed: int = 0, max_steps: int = -1,
          model=None):
    """Full fine-tune of a small causal LM. fp16 on a T4, gradient checkpointing to fit 360M parameters."""
    import torch
    from transformers import AutoModelForCausalLM, DataCollatorForSeq2Seq, Trainer, TrainingArguments

    if model is None:
        model = AutoModelForCausalLM.from_pretrained(base, dtype=torch.float32)
    rows, _, _ = features(train_records, tok, max_length)
    steps = max_steps if max_steps > 0 else int(epochs * -(-len(rows) // (batch_size * grad_accum)))
    args = TrainingArguments(
        output_dir=out_dir, num_train_epochs=epochs, max_steps=max_steps, learning_rate=lr, warmup_steps=steps // 20,
        lr_scheduler_type="cosine", weight_decay=0.0, per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum, gradient_checkpointing=torch.cuda.is_available(),
        fp16=torch.cuda.is_available(), save_strategy="no", logging_steps=25, seed=seed, report_to=[])
    trainer = Trainer(model=model, args=args, train_dataset=rows,
                      data_collator=DataCollatorForSeq2Seq(tok, label_pad_token_id=-100, padding=True))
    trainer.train()
    trainer.save_model(out_dir)
    tok.save_pretrained(out_dir)
    return model


def generate(model, tok, records: list[dict], *, batch_size: int = 16, max_new_tokens: int = MAX_NEW_TOKENS,
             device: str | None = None) -> list[str]:
    """Greedy outputs, one batch at a time with left padding. Works with a PyTorch or an optimum ONNX model."""
    import torch

    device = device or getattr(model, "device", "cpu")
    tok.padding_side = "left"
    outs = []
    for start in range(0, len(records), batch_size):
        batch = [prompt(r["text"]) for r in records[start:start + batch_size]]
        enc = tok(batch, return_tensors="pt", padding=True, add_special_tokens=False, return_token_type_ids=False)
        enc = {k: v.to(device) for k, v in enc.items()}
        with torch.no_grad():
            ids = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                                 pad_token_id=tok.pad_token_id, eos_token_id=tok.eos_token_id)
        outs += tok.batch_decode(ids[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
    return outs


def score(records: list[dict], outputs: list[str]) -> dict:
    """The teacher's report for generated text; unparseable output counts as wrong everywhere."""
    return evaluate(records, [parse(o) for o in outputs])


def export_onnx(model_dir: str, out_dir: str) -> dict:
    """Write the layout transformers.js loads for text generation with a KV cache: config and tokenizer files at the
    top, and onnx/model.onnx (float32), onnx/model_quantized.onnx (int8) and onnx/model_q4.onnx (4-bit weights).
    Returns the file sizes in bytes."""
    import shutil
    import tempfile
    from pathlib import Path

    import onnx
    from onnxruntime.quantization import QuantType, quantize_dynamic
    from onnxruntime.quantization.matmul_nbits_quantizer import MatMulNBitsQuantizer
    from optimum.exporters.onnx import main_export

    out = Path(out_dir)
    (out / "onnx").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        main_export(model_dir, tmp, task="text-generation-with-past")
        for f in Path(tmp).iterdir():
            shutil.copy(f, out / ("onnx" if f.name.startswith("model.onnx") else "") / f.name)
    model_path = out / "onnx" / "model.onnx"
    quantize_dynamic(model_path, out / "onnx" / "model_quantized.onnx", weight_type=QuantType.QInt8)
    q4 = MatMulNBitsQuantizer(onnx.load(model_path), block_size=32, is_symmetric=True)
    q4.process()
    q4.model.save_model_to_file(str(out / "onnx" / "model_q4.onnx"), use_external_data_format=False)
    return {p.name: p.stat().st_size for p in (out / "onnx").iterdir()}


def onnx_model(out_dir: str, file_name: str):
    """An optimum ORT model for generate(), from the layout export_onnx writes."""
    from optimum.onnxruntime import ORTModelForCausalLM

    return ORTModelForCausalLM.from_pretrained(out_dir, subfolder="onnx", file_name=file_name)
