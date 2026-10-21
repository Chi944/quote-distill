"""End-to-end run of student/generative.py on a tiny random Llama and a locally trained stand-in tokenizer.

It checks the code path the notebook runs (features, training, generation, scoring, ONNX export with a KV cache),
not accuracy. CI skips it: it needs the `generative` extra (torch, transformers<4.58, optimum-onnx).
"""

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
pytest.importorskip("optimum.exporters.onnx")

from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers  # noqa: E402

from quote_distill.generator.build import generate as generate_docs  # noqa: E402
from quote_distill.student.data import prepare  # noqa: E402
from quote_distill.student.generative import export_onnx, features, generate, onnx_model, parse, score, train  # noqa: E402


def stand_in_tokenizer(texts):
    tok = Tokenizer(models.BPE(unk_token="<unk>"))
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    tok.train_from_iterator(texts, trainers.BpeTrainer(vocab_size=600, special_tokens=["<pad>", "<unk>", "<|im_end|>"],
                                                       initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
    return transformers.PreTrainedTokenizerFast(tokenizer_object=tok, pad_token="<pad>", unk_token="<unk>",
                                                eos_token="<|im_end|>")


def test_parse_accepts_compact_json_only():
    records, _ = generate_docs(1, 5, "dev")
    rows, _ = prepare(records)
    assert parse(rows[0]["target"]) is not None
    assert parse("```json\n" + rows[0]["target"] + "\n```") is None
    assert parse('{"supplier": "x"}') is None
    assert parse("[]") is None


def test_generative_trains_generates_and_exports(tmp_path):
    records, _ = generate_docs(24, 5, "dev")
    rows, _ = prepare(records)
    tok = stand_in_tokenizer([r["text"] + r["target"] for r in rows])
    train_rows, dev_rows = rows[:20], rows[20:]
    feats, too_long, lengths = features(train_rows, tok)
    assert too_long.n == 0 and len(feats) == 20 and lengths["target"]["max"] > 0
    assert all(lab == -100 for lab in feats[0]["labels"][:10])

    config = transformers.LlamaConfig(
        vocab_size=len(tok), hidden_size=32, intermediate_size=64, num_hidden_layers=2, num_attention_heads=2,
        num_key_value_heads=1, max_position_embeddings=2048, pad_token_id=tok.pad_token_id,
        eos_token_id=tok.eos_token_id, bos_token_id=tok.eos_token_id, tie_word_embeddings=True)
    model = transformers.AutoModelForCausalLM.from_config(config)
    model = train(train_rows, tok, base="", out_dir=str(tmp_path / "model"), max_steps=3, batch_size=4, grad_accum=1,
                  model=model)

    outputs = generate(model, tok, dev_rows, batch_size=2, max_new_tokens=24, device="cpu")
    assert len(outputs) == len(dev_rows)
    assert score(dev_rows, outputs)["parsed"].d == len(dev_rows)

    sizes = export_onnx(str(tmp_path / "model"), str(tmp_path / "js"))
    assert {"model.onnx", "model_quantized.onnx", "model_q4.onnx"} <= set(sizes)
    assert (tmp_path / "js" / "tokenizer.json").exists() and (tmp_path / "js" / "config.json").exists()
    ort = onnx_model(str(tmp_path / "js"), "model.onnx")
    assert generate(ort, tok, dev_rows, batch_size=2, max_new_tokens=24, device="cpu") == outputs
    for name in ("model_quantized.onnx", "model_q4.onnx"):
        assert len(generate(onnx_model(str(tmp_path / "js"), name), tok, dev_rows[:1], max_new_tokens=8,
                            device="cpu")) == 1
