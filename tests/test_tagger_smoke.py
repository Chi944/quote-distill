"""End-to-end run of student/tagger.py on a tiny random model and a locally trained stand-in tokenizer.

It checks the code path the notebook runs (features, training, prediction, ONNX export and parity), not accuracy.
CI skips it because torch isn't installed there; run it with the `train` extra installed.
"""

import json

import pytest

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")
pytest.importorskip("onnxruntime")

from tokenizers import Tokenizer, decoders, models, pre_tokenizers, processors, trainers  # noqa: E402

from quote_distill.generator.build import generate  # noqa: E402
from quote_distill.student.data import prepare  # noqa: E402
from quote_distill.student.tagger import (  # noqa: E402
    ceiling,
    evaluate,
    export_onnx,
    features,
    isolate_punctuation,
    onnx_logits,
    predict,
    torch_logits,
    train,
)
from quote_distill.student.tokens import LABEL_ID, LABELS  # noqa: E402


def stand_in_tokenizer(texts):
    """Byte-level BPE with [CLS] ... [SEP], like ModernBERT's, trained on the documents themselves."""
    tok = Tokenizer(models.BPE(unk_token="[UNK]"))
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    specials = ["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"]
    tok.train_from_iterator(texts, trainers.BpeTrainer(vocab_size=600, special_tokens=specials,
                                                       initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
    tok.post_processor = processors.TemplateProcessing(single="[CLS] $A [SEP]", special_tokens=[
        ("[CLS]", tok.token_to_id("[CLS]")), ("[SEP]", tok.token_to_id("[SEP]"))])
    fast = transformers.PreTrainedTokenizerFast(tokenizer_object=tok, pad_token="[PAD]", unk_token="[UNK]",
                                                cls_token="[CLS]", sep_token="[SEP]", mask_token="[MASK]")
    isolate_punctuation(fast)
    return fast


@pytest.fixture(scope="module")
def setup():
    records, _ = generate(48, 5, "dev")
    rows, _ = prepare(records)
    tok = stand_in_tokenizer([r["text"] for r in rows])
    return rows[:40], rows[40:], tok


def test_tagger_trains_predicts_and_exports(setup, tmp_path):
    train_rows, dev_rows, tok = setup
    f = features(dev_rows, tok)
    assert f.lost == 0 and f.truncated.n == 0 and f.clashes == 0
    assert ceiling(dev_rows, tok).n == len(dev_rows)

    config = transformers.ModernBertConfig(
        vocab_size=len(tok), hidden_size=32, intermediate_size=64, num_hidden_layers=2, num_attention_heads=2,
        max_position_embeddings=1024, pad_token_id=tok.pad_token_id, cls_token_id=tok.cls_token_id,
        sep_token_id=tok.sep_token_id, num_labels=len(LABELS), id2label=dict(enumerate(LABELS)), label2id=LABEL_ID)
    model = transformers.AutoModelForTokenClassification.from_config(config)
    model = train(train_rows, dev_rows, tok, base="", out_dir=str(tmp_path / "model"), max_steps=3, batch_size=8,
                  model=model)

    preds = predict(torch_logits(model, "cpu"), tok, dev_rows, batch_size=4)
    report = evaluate(dev_rows, preds)
    assert report["documents"] == len(dev_rows)
    json.dumps(report, default=str)

    sizes = export_onnx(model, tok, str(tmp_path / "onnx"))
    assert set(sizes) == {"model.onnx", "model_quantized.onnx"}
    run_torch, run_onnx = torch_logits(model, "cpu"), onnx_logits(str(tmp_path / "onnx" / "onnx" / "model.onnx"))
    texts = [r["text"] for r in dev_rows[:3]]
    batch = tok(texts, padding=True)
    a, b = run_torch(batch["input_ids"], batch["attention_mask"]), run_onnx(batch["input_ids"], batch["attention_mask"])
    for i, mask in enumerate(batch["attention_mask"]):
        n = sum(mask)
        assert abs(a[i, :n] - b[i, :n]).max() < 1e-3
        single = tok([texts[i]])  # one unpadded document, as the browser runs it
        assert abs(run_onnx(single["input_ids"], single["attention_mask"])[0] - b[i, :n]).max() < 1e-3
    assert predict(run_onnx, tok, dev_rows, batch_size=4) == preds
    assert (tmp_path / "onnx" / "tokenizer.json").exists()
