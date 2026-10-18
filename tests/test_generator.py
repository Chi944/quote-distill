import json
import re

import pytest

from quote_distill.generator.build import generate
from quote_distill.normalise import CURRENCY_TOKENS

N = 400


@pytest.fixture(scope="module")
def batch():
    return generate(N, seed=7, split="dev")


def test_every_document_passes_checks(batch):
    kept, stats = batch
    assert stats["n_rejected"] == 0, stats["rejected_examples"]
    assert len(kept) == N


def test_deterministic():
    a, _ = generate(30, seed=3, split="dev")
    b, _ = generate(30, seed=3, split="dev")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    c, _ = generate(30, seed=4, split="dev")
    assert [r["text"] for r in a] != [r["text"] for r in c]


@pytest.mark.parametrize("feature", [
    "gst:exclusive", "gst:inclusive", "gst:not_charged", "gst:not_stated", "gst_plus_unpriced", "doc_discount",
    "line:line_discount_percent", "line:line_discount_amount", "line:lump_sum", "line:foc", "line:credit",
    "line:decimal_qty", "line:qty_in_words", "supplier_error", "bare_dollar", "relative_validity", "conditional_discount",
    "header_typos", "description_typo", "customer_ref_decoy", "missing:quote_number", "missing:date", "missing:subtotal",
    "missing:total", "missing:validity", "missing:payment_terms",
    *[f"layout:{x}" for x in ["fixed_table", "pipe_table", "item_blocks", "email_list", "prose_email"]],
])
def test_hard_case_coverage(batch, feature):
    assert batch[1]["feature_counts"].get(feature, 0) >= 3


def test_gst_never_mentioned_when_not_stated(batch):
    for r in batch[0]:
        if r["label"]["gst"]["treatment"] == "not_stated":
            assert not re.search(r"\b(GST|VAT|SST|[Tt]ax)\b", r["text"]), r["id"]


def test_bare_dollar_documents_carry_no_currency_token(batch):
    for r in batch[0]:
        if "bare_dollar" in r["meta"]["features"]:
            assert r["label"]["currency"]["state"] == "not_stated"
            assert not re.search(r"(?<![A-Z])(S|A|NZ|US)\$|\bRM\b", r["text"]), r["id"]
            for token in CURRENCY_TOKENS:
                if "$" not in token and token != "RM":
                    assert token not in r["text"], (r["id"], token)


def test_missing_quote_number_is_not_printed(batch):
    for r in batch[0]:
        if r["label"]["quote_number"]["state"] == "not_stated":
            assert not re.search(r"[Qq]uot\w* (No|#|number)|Our quote", r["text"]), r["id"]


def test_supplier_errors_are_the_only_arithmetic_failures(batch):
    for r in batch[0]:
        assert r["meta"]["checks"]["fail"] == len(r["meta"]["expected_check_failures"]), r["id"]
