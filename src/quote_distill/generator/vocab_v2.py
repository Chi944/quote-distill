"""Wider vocabulary for generator style v2. Every v1 entry is kept; v2 adds to it.

Fictional, like vocab.py: supplier names are random word combinations, and any match with a real business is
unintended. This file was written from general variation axes (synonyms, trades, term wordings), not from the
hand-written out-of-distribution set in data/ood/, which must never be copied into training data.
"""

import random

from .vocab import CUSTOMERS, ITEMS, LUMP_SUMS, NAME_FIRST, NAME_SECOND, PAYMENT_TERMS

NAME_FIRST_V2 = ["Amberline", "Bellbird", "Cinderford", "Driftwood", "Eastvale", "Foxglove", "Glenrock", "Hollowbrook",
                 "Inkwell", "Jarrah", "Kowhai", "Lanternfield", "Moonvale", "Nettlecombe", "Orchard Lane", "Pelican Bay",
                 "Quarrymoor", "Riverbend", "Sandpiper", "Thornbury", "Upland", "Violet Hill", "Westerly", "Yellowtail"]
NAME_SECOND_V2 = ["Print & Signage", "Event Hire", "IT Services", "Catering", "Nurseries", "Scientific", "Roofing",
                  "Glass & Glazing", "Cleaning Services", "Air Conditioning", "Joinery", "Fencing", "Pest Control",
                  "Office Furniture", "Medical Supplies", "Packaging", "Audio Visual", "Landscapes", "Training",
                  "Logistics", "Solar & Energy", "Tiling", "Security Systems", "Software"]
CUSTOMERS_V2 = ["Kauri Ridge Primary", "Seabreeze Apartments Body Corporate", "Old Mill Brewery", "St Clement's Hall",
                "Harbour Lights Dental", "Greenfield Council Depot", "Northshore Physio", "Palm Court Hotel"]

# (description, canonical unit, min price, max price, decimal quantities allowed, max quantity); units are in
# normalise.UNIT_SYNONYMS.
ITEMS_V2 = [
    ("Pull-up banner 850 x 2000mm, printed", "each", "95", "260", False, 10),
    ("Business cards, 350gsm, box of 250", "box", "35", "90", False, 20),
    ("Vinyl window decal, cut to size", "m2", "45", "120", True, 30),
    ("Folding chair hire, white", "each", "2.5", "8", False, 300),
    ("Trestle table hire 1.8m", "each", "9", "22", False, 60),
    ("Lunch buffet, standard menu", "each", "14", "38", False, 150),
    ("Morning tea platter", "each", "45", "110", False, 20),
    ("Laptop 14in, 16GB RAM, 512GB SSD", "each", "950", "1900", False, 12),
    ("24in monitor, IPS", "each", "180", "420", False, 20),
    ("Network switch, 24-port managed", "each", "260", "780", False, 6),
    ("Help desk support", "hour", "85", "160", True, 40),
    ("Software licence, annual, per user", "each", "60", "420", False, 50),
    ("Email hosting per mailbox", "month", "4", "12", False, 24),
    ("Potted lilly pilly 45L", "each", "60", "150", False, 30),
    ("Garden mulch, bark", "m3", "55", "120", True, 20),
    ("Instant turf", "m2", "9", "22", True, 400),
    ("Pipette tips 200uL, rack of 96", "box", "8", "25", False, 40),
    ("Centrifuge tubes 50mL, pack of 25", "pack", "10", "30", False, 40),
    ("Colorbond roofing sheet 0.42mm", "m", "18", "40", True, 200),
    ("Gutter guard mesh", "m", "9", "25", True, 120),
    ("Solar panel 440W mono", "each", "180", "380", False, 30),
    ("Split system air conditioner 7kW", "each", "1400", "2600", False, 4),
    ("Office cleaning, standard visit", "each", "90", "260", False, 20),
    ("Carpet steam clean", "m2", "4", "11", True, 300),
    ("Ergonomic office chair", "each", "220", "690", False, 20),
    ("Standing desk frame, electric", "each", "390", "980", False, 12),
    ("Cardboard cartons 600x400x400", "pack", "28", "65", False, 40),
    ("Bubble wrap 500mm x 50m", "roll", "18", "45", False, 30),
    ("Pallet freight, metro", "each", "65", "180", False, 12),
    ("First aid kit refill, workplace", "set", "45", "140", False, 10),
    ("Anti-slip floor coating", "l", "35", "80", True, 40),
    ("Timber fence paling 1.8m", "each", "3", "8", False, 400),
    ("CCTV camera 4MP, installed", "each", "240", "520", False, 16),
    ("Training course, half day, per person", "each", "180", "450", False, 20),
    ("Project manager", "day", "800", "1500", True, 15),
    ("Courier van with driver", "hour", "70", "120", True, 24),
]
LUMP_SUMS_V2 = ["Design and artwork", "Site survey", "Setup and pack-down", "Data migration", "Waste removal",
                "Travel and call-out", "Commissioning and handover", "Scaffold erection and dismantle", "Project management",
                "Pre-start safety briefing"]
PAYMENT_TERMS_V2 = ["Payment due on completion", "Net 7", "Strictly 14 days", "Due on receipt", "EOM + 30",
                    "30% deposit to confirm, balance on completion", "Progress claims monthly, payable within 10 days",
                    "Payable by bank transfer within 21 days", "7 days from invoice date", "Credit card or EFT on order",
                    "45 days from end of month", "Deposit 40%, balance net 14"]

V2 = {
    "NAME_FIRST": NAME_FIRST + NAME_FIRST_V2,
    "NAME_SECOND": NAME_SECOND + NAME_SECOND_V2,
    "CUSTOMERS": CUSTOMERS + CUSTOMERS_V2,
    "ITEMS": ITEMS + ITEMS_V2,
    "LUMP_SUMS": LUMP_SUMS + LUMP_SUMS_V2,
    "PAYMENT_TERMS": PAYMENT_TERMS + PAYMENT_TERMS_V2,
}

# Header words the layouts print through Quote.h(); the first entry is the v1 word, so v1 stays one of the choices.
SYNONYMS = {
    "Quotation": ["Quotation", "Quote", "Price Quote", "Estimate", "Proposal", "Offer", "Pro Forma Quote"],
    "Description": ["Description", "Item", "Particulars", "Details", "Item description", "Product / service"],
    "Subtotal": ["Subtotal", "Sub-total", "Sub total", "Items total", "Net amount", "Sum"],
    "Discount": ["Discount", "Disc.", "Less", "Rebate"],
    "Total": ["Total", "Grand total", "Total payable", "Amount due", "Total amount", "Nett total", "Total price"],
    "Validity": ["Validity", "Quote validity", "Offer validity"],
    "Payment": ["Payment", "Settlement", "Credit"],
    "Quantity": ["Quantity", "Qty", "No. of units", "Units"],
}


def sample_words(rng: random.Random) -> dict[str, str]:
    """One document's header words. About a third of words keep their v1 form."""
    return {w: options[0] if rng.random() < 0.35 else rng.choice(options[1:]) for w, options in SYNONYMS.items()}
