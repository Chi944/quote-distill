"""Build tiny random models in the demo's layout, with the answers Python gets from them, for demo/test/models.test.ts.

    python tests/demo_models.py tagger       # needs the train extra
    python tests/demo_models.py generative   # needs the generative extra (optimum-onnx)

Writes demo/fixtures/models/tiny-<kind>/ and demo/fixtures/models/<kind>-expected.json. The models are untrained, so
the answers are nonsense; the point is that the browser code gets the same nonsense from the same files.
"""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "demo" / "fixtures" / "models"
sys.path.insert(0, str(ROOT / "tests"))


def rows(n: int) -> list[dict]:
    from quote_distill.generator.build import generate
    from quote_distill.student.data import prepare

    records, _ = generate(n, 11, "dev")
    return prepare(records)[0]


def tagger() -> None:
    import transformers
    from test_tagger_smoke import stand_in_tokenizer

    from quote_distill.student.tagger import _offsets, export_onnx, onnx_logits
    from quote_distill.student.tokens import LABEL_ID, LABELS, read

    docs = rows(30)
    tok = stand_in_tokenizer([r["text"] for r in docs])
    config = transformers.ModernBertConfig(
        vocab_size=len(tok), hidden_size=32, intermediate_size=64, num_hidden_layers=2, num_attention_heads=2,
        max_position_embeddings=1024, pad_token_id=tok.pad_token_id, cls_token_id=tok.cls_token_id,
        sep_token_id=tok.sep_token_id, num_labels=len(LABELS), id2label=dict(enumerate(LABELS)), label2id=LABEL_ID)
    transformers.set_seed(0)
    model = transformers.AutoModelForTokenClassification.from_config(config)
    out = OUT / "tiny-tagger"
    export_onnx(model, tok, str(out))
    expected = []
    for name in ("model.onnx", "model_quantized.onnx"):
        run = onnx_logits(str(out / "onnx" / name))
        for r in docs[:10]:
            (ids, offs), = _offsets(tok, [r["text"]], 1024)
            expected.append({"file": name, "text": r["text"], "label": read(r["text"], offs, run([ids], [[1] * len(ids)])[0])})
    (OUT / "tagger-expected.json").write_text(json.dumps(expected, ensure_ascii=False))


def generative() -> None:
    import torch
    import transformers
    from test_generative_smoke import stand_in_tokenizer

    from quote_distill.student.generative import PROMPT, export_onnx, generate, onnx_model

    docs = rows(12)
    tok = stand_in_tokenizer([r["text"] + r["target"] for r in docs])
    config = transformers.LlamaConfig(
        vocab_size=len(tok), hidden_size=32, intermediate_size=64, num_hidden_layers=2, num_attention_heads=2,
        num_key_value_heads=1, max_position_embeddings=2048, initializer_range=1.0, pad_token_id=tok.pad_token_id,
        eos_token_id=tok.eos_token_id, bos_token_id=tok.eos_token_id, tie_word_embeddings=True)
    torch.manual_seed(0)
    model = transformers.AutoModelForCausalLM.from_config(config)
    with tempfile.TemporaryDirectory() as tmp:
        model.save_pretrained(tmp)
        tok.save_pretrained(tmp)
        export_onnx(tmp, str(OUT / "tiny-generative"))
    expected = []
    for name in ("model.onnx", "model_q4.onnx"):
        outs = generate(onnx_model(str(OUT / "tiny-generative"), name), tok, docs[:4], batch_size=1, max_new_tokens=24,
                        device="cpu")
        expected += [{"file": name, "text": r["text"], "output": o} for r, o in zip(docs[:4], outs, strict=True)]
    (OUT / "generative-expected.json").write_text(json.dumps({"prompt": PROMPT, "max_new_tokens": 24,
                                                              "cases": expected}, ensure_ascii=False))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    {"tagger": tagger, "generative": generative}[sys.argv[1]]()
    print("wrote", OUT)
