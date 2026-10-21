"""The teacher prompt: one system prompt shared by every request, and the document text as the user turn.

The system prompt is built from docs/schema.md and the JSON Schema, so the teacher reads the same rules the
generator, checker and metrics follow. Its SHA-256 is recorded with every job so a result can be tied to a prompt.
"""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RULES_PATH = ROOT / "docs" / "schema.md"
SCHEMA_PATH = ROOT / "schema" / "quotation.schema.json"

INSTRUCTIONS = """You extract structured data from supplier quotations.

Read the quotation in the user turn and reply with one JSON object that validates against the JSON Schema below. \
Reply with the JSON only: no prose, no code fence.

The rules below say how to read each field. The most important ones:
- Record what the document prints. Never compute, infer or correct a value. If a printed line total or total is \
arithmetically wrong, copy it as printed.
- Use {"state": "not_stated"} for anything the document does not print. Do not guess a currency from an address, \
a GST rate from a country, or a total from the line items.
- Money values are decimal strings with exactly two decimals ("1214.64", "-80.00"). Never use JSON numbers.
- Every stated field carries "raw": the exact characters copied from the document, and "value": the normalised form.
- Set "schema_version" to "1.0.0".
"""


def _rules() -> str:
    text = RULES_PATH.read_text(encoding="utf-8")
    # Links to repository files mean nothing to the model.
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text).strip()


def _schema() -> str:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return json.dumps(schema, separators=(",", ":"), ensure_ascii=False)


def system_prompt() -> str:
    return f"{INSTRUCTIONS}\n# Rules\n\n{_rules()}\n\n# JSON Schema\n\n{_schema()}\n"


def prompt_sha256() -> str:
    return hashlib.sha256(system_prompt().encode("utf-8")).hexdigest()


def user_turn(text: str) -> str:
    return f"<quotation>\n{text}</quotation>"


def parse_output(text: str):
    """Parse the model's reply as JSON with no repair (pilot gate 1). Returns (label or None, problem or None)."""
    try:
        value = json.loads(text)
    except json.JSONDecodeError as e:
        fenced = text.strip().startswith("```")
        return None, ("wrapped in a code fence" if fenced else f"not JSON: {e.msg} at character {e.pos}")
    if not isinstance(value, dict):
        return None, f"JSON is a {type(value).__name__}, not an object"
    return value, None
