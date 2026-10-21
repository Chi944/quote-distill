"""Pricing used for estimates, and the docs/spend.md log that every API job must appear in before it is submitted."""

import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

SPEND_PATH = Path(__file__).resolve().parents[3] / "docs" / "spend.md"

# Message Batches API prices per million tokens (50% of standard), read from
# https://platform.claude.com/docs/en/about-claude/pricing on the date below. Re-check before every job.
PRICING_CHECKED = "2026-10-18"
BATCH_PRICES = {
    "claude-haiku-5-5": (Decimal("0.05"), Decimal("0.25")),  # prompts up to 100K tokens
    "claude-sonnet-5-5": (Decimal("1"), Decimal("5")),
}
CACHE_WRITE_MULTIPLIER = Decimal("1.25")  # we do not set cache_control; counted conservatively if it ever appears

HEADER = ("| Date | Job | Model | Mode | Requests | Input tokens | Output tokens | Est. cost | Actual cost | Running total "
          "| Pricing checked |")
ROW = re.compile(r"^\| (?P<date>[^|]+) \| (?P<job>[^|]+) \| (?P<rest>.*)\|$")


def cost(model: str, input_tokens: int, output_tokens: int, cache_write_tokens: int = 0, cache_read_tokens: int = 0) -> Decimal:
    p_in, p_out = BATCH_PRICES[model]
    m = Decimal(1_000_000)
    return (input_tokens * p_in + cache_write_tokens * p_in * CACHE_WRITE_MULTIPLIER + cache_read_tokens * p_in
            + output_tokens * p_out) / m


def usd(x: Decimal) -> str:
    return f"${x.quantize(Decimal('0.0001')) if x < 1 else x.quantize(Decimal('0.01'))}"


@dataclass
class Row:
    date: str
    job: str
    model: str
    mode: str
    requests: int
    input_tokens: str
    output_tokens: str
    est_cost: str
    actual_cost: str
    running_total: str
    pricing_checked: str

    def render(self) -> str:
        return "| " + " | ".join(str(v) for v in self.__dict__.values()) + " |"


def _read(path: Path) -> tuple[list[str], list[Row]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    rows = []
    for line in lines[lines.index(HEADER) + 2:]:
        if not line.startswith("| "):
            break
        rows.append(Row(*[c.strip() for c in line.strip("|").split("|")]))
    return lines, rows


def _write(path: Path, lines: list[str], rows: list[Row]) -> None:
    start = lines.index(HEADER) + 2
    end = start
    while end < len(lines) and lines[end].startswith("| "):
        end += 1
    tail = [line for line in lines[end:] if line.strip() and not line.startswith(("No jobs yet", "Running total"))]
    total = sum((Decimal(r.actual_cost.lstrip("$")) for r in rows if r.actual_cost.startswith("$")), Decimal(0))
    body = [*lines[:start], *(r.render() for r in rows), "", f"Running total: **{usd(total)}** of US$100.",
            *(["", *tail] if tail else [])]
    path.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")


def find(job: str, path: Path = SPEND_PATH) -> Row | None:
    return next((r for r in _read(path)[1] if r.job == job), None)


def log_estimate(row: Row, path: Path = SPEND_PATH) -> None:
    lines, rows = _read(path)
    if any(r.job == row.job for r in rows):
        raise ValueError(f"job {row.job!r} is already in {path.name}")
    _write(path, lines, [*rows, row])


def log_actual(job: str, input_tokens: int, output_tokens: int, actual: Decimal, path: Path = SPEND_PATH) -> Row:
    lines, rows = _read(path)
    row = next((r for r in rows if r.job == job), None)
    if row is None:
        raise ValueError(f"job {job!r} has no estimate row in {path.name}")
    row.input_tokens, row.output_tokens, row.actual_cost = f"{input_tokens:,}", f"{output_tokens:,}", usd(actual)
    running = Decimal(0)
    for r in rows:
        if r.actual_cost.startswith("$"):
            running += Decimal(r.actual_cost.lstrip("$"))
            r.running_total = usd(running)
    _write(path, lines, rows)
    return row
