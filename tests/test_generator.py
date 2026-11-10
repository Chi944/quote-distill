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


# ---------- generator v2 ----------

def test_v1_output_is_unchanged_by_v2():
    """Style v1 must keep producing the documents the published students and the test set came from."""
    import hashlib
    kept, _ = generate(200, seed=7, split="dev")
    digest = hashlib.sha256(json.dumps(kept, sort_keys=True).encode()).hexdigest()
    assert digest == "b34963027b978b967da9a793f7e5f3f3a13a6f95ba6a1c8dc7ca81488b230349"


@pytest.fixture(scope="module")
def batch_v2():
    return generate(N, seed=7, split="dev", style="v2")


def test_v2_every_document_passes_checks_and_aligns(batch_v2):
    from quote_distill.student.spans import align
    kept, stats = batch_v2
    assert stats["n_rejected"] == 0, stats["rejected_examples"]
    assert all(align(r["label"], r["text"]).complete for r in kept)
    assert {r["meta"]["style"] for r in kept} == {"v2"}


def test_v2_deterministic_and_distinct_from_v1():
    a, _ = generate(20, seed=3, split="dev", style="v2")
    b, _ = generate(20, seed=3, split="dev", style="v2")
    v1, _ = generate(20, seed=3, split="dev")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert not {r["text"] for r in a} & {r["text"] for r in v1}


@pytest.mark.parametrize("layout", ["kv_table", "delimited", "totals_first", "numbered_lines", "bare_columns",
                                    "fixed_table", "pipe_table", "item_blocks", "email_list", "prose_email"])
def test_v2_covers_old_and_new_layouts(batch_v2, layout):
    assert batch_v2[1]["feature_counts"].get(f"layout:{layout}", 0) >= 10


def test_v2_uses_the_wider_wording(batch_v2):
    from quote_distill.generator.vocab_v2 import SYNONYMS
    texts = "\n".join(r["text"] for r in batch_v2[0])
    for word in ("Estimate", "Proposal", "Grand total", "Amount due", "Particulars"):
        assert word in texts
    assert all(options[0] == word for word, options in SYNONYMS.items())


def test_v2_shares_no_line_with_the_hand_written_set(batch_v2):
    from quote_distill.student.data import held_out_lines, shares_held_out_line
    banned = held_out_lines()
    assert len(banned) > 100
    assert not [r["id"] for r in batch_v2[0] if shares_held_out_line(r["text"], banned)]
    some_line = sorted(banned)[0]
    assert shares_held_out_line(f"header\n  {some_line.upper()}  \nfooter", banned)
