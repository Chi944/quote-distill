"""Shared normalisation tables: the generator writes surface forms from them and the checker reads them back."""

UNIT_SYNONYMS: dict[str, list[str]] = {
    "each": ["ea", "each", "pcs", "pc", "units", "nos"],
    "pair": ["pr", "pair", "pairs"],
    "box": ["box", "bx", "boxes"],
    "pack": ["pk", "pack", "packs"],
    "set": ["set", "sets"],
    "sheet": ["sheet", "sheets", "sht", "sh"],
    "length": ["length", "lengths", "lgth"],
    "roll": ["roll", "rolls"],
    "bag": ["bag", "bags"],
    "m": ["m", "lm", "metre", "metres"],
    "m2": ["m2", "m²", "sqm"],
    "m3": ["m3", "m³", "cu m"],
    "kg": ["kg", "kgs"],
    "tonne": ["t", "tonne", "tonnes"],
    "l": ["l", "litre", "litres"],
    "hour": ["hr", "hrs", "hour", "hours"],
    "day": ["day", "days"],
    "week": ["wk", "week", "weeks"],
    "month": ["mth", "month", "months"],
    "lot": ["lot", "l/s", "lump sum", "flat"],
}
UNIT_BY_RAW = {raw: unit for unit, raws in UNIT_SYNONYMS.items() for raw in raws}

# Only codes, prefixed symbols and names are stated currency; a bare "$" never is.
CURRENCY_TOKENS: dict[str, str] = {
    "SGD": "SGD", "S$": "SGD", "Singapore dollars": "SGD", "Singapore dollars (S$)": "SGD",
    "AUD": "AUD", "A$": "AUD", "Australian dollars": "AUD",
    "NZD": "NZD", "NZ$": "NZD", "New Zealand dollars": "NZD",
    "MYR": "MYR", "RM": "MYR", "Ringgit": "MYR",
    "USD": "USD", "US$": "USD", "US dollars": "USD",
}

DATE_FORMATS: dict[str, list[str]] = {
    "SG": ["%d %b %Y", "%d %B %Y", "%d/%m/%Y", "%a, %d %b %Y"],
    "AU": ["%d/%m/%Y", "%d %B %Y", "%d %b %Y", "%a, %d %b %Y"],
    "NZ": ["%d %B %Y", "%d/%m/%Y", "%d %b %Y", "%a, %d %b %Y"],
    "MY": ["%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%a, %d %b %Y"],
    "US": ["%B %d, %Y", "%m/%d/%Y", "%b %d, %Y", "%a, %d %b %Y"],
}

NUMBER_WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())}
FREE_WORDS = {"foc", "free", "n/c", "no charge"}


def collapse(text: str) -> str:
    return " ".join(text.split())


def normalise_payment_terms(raw: str) -> str:
    return collapse(raw).casefold().rstrip(".")
