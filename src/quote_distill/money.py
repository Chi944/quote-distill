"""Exact decimal helpers. Money never touches a float."""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def round_money(x: Decimal) -> Decimal:
    """Round half-up to cents, the schema's only rounding rule."""
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


def money_value(x: Decimal) -> str:
    """Schema money value: exactly two decimals, no separators."""
    return f"{round_money(x):.2f}"


def price_value(x: Decimal) -> str:
    """Schema unit price value: two to four decimals, trailing zeros beyond two removed."""
    text = f"{x:.4f}"
    whole, frac = text.split(".")
    frac = frac.rstrip("0").ljust(2, "0")
    return f"{whole}.{frac}"


def decimal_value(x: Decimal) -> str:
    """Schema quantity or rate value: no trailing zeros, no exponent."""
    text = f"{x:f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def grouped(x: Decimal, places: int = 2) -> str:
    """Render with thousands separators, as many documents print money."""
    return f"{x:,.{places}f}"


def is_half_cent_tie(x: Decimal) -> bool:
    """True when x sits exactly halfway between two cents, where half-up and banker's rounding differ."""
    return (x * 1000) % 10 == 5 and (x * 1000) == (x * 1000).to_integral_value()
