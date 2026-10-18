"""Fictional vocabulary. Supplier names are random word combinations; any match with a real business is unintended."""

from decimal import Decimal as D

LOCALES = {
    "SG": {"currency": "SGD", "gst": D("9"), "tokens": ["SGD", "S$", "Singapore dollars"],
           "suffixes": ["Pte. Ltd.", "Pte Ltd", "Trading", "Enterprise"],
           "places": ["Ubi Avenue 3, Singapore 408867", "Kaki Bukit Road 2, Singapore 417868", "Woodlands Loop, Singapore 738310"]},
    "AU": {"currency": "AUD", "gst": D("10"), "tokens": ["AUD", "A$", "Australian dollars"],
           "suffixes": ["Pty Ltd", "Pty. Ltd.", "Supplies", "Group"],
           "places": ["Lot 7 Quarry Rd, Toowoomba QLD 4350", "14 Dunlop St, Geelong VIC 3220", "3/88 Hammer Ave, Osborne Park WA 6017"]},
    "NZ": {"currency": "NZD", "gst": D("15"), "tokens": ["NZD", "NZ$", "New Zealand dollars"],
           "suffixes": ["Ltd", "Limited", "Co. Ltd"],
           "places": ["21 Wharf Rd, Tauranga 3110", "6 Kaimai St, Hamilton 3204", "102 Ferry Rd, Christchurch 8011"]},
    "MY": {"currency": "MYR", "gst": None, "tokens": ["MYR", "RM", "Ringgit"],
           "suffixes": ["Sdn. Bhd.", "Sdn Bhd", "Trading", "Enterprise"],
           "places": ["Jalan Perusahaan 4, 81400 Senai, Johor", "Lot 22, Jalan PJS 11/7, 46150 Petaling Jaya"]},
    "US": {"currency": "USD", "gst": None, "tokens": ["USD", "US$", "US dollars"],
           "suffixes": ["Inc.", "LLC", "Corp."],
           "places": ["2210 Wexley Avenue, Columbus OH 43215, USA", "48 Mill Pond Rd, Nashua NH 03062, USA"]},
}

NAME_FIRST = ["Kestrel", "Bramblewood", "Harrowgate", "Larkspur", "Ironbark", "Tamarind", "Coldwater", "Saltmarsh", "Redgum",
              "Juniper", "Halcyon", "Stonechat", "Wattlebank", "Merrow", "Copperleaf", "Northgate", "Fernhill", "Ashby",
              "Quillon", "Tidewell", "Greyhaven", "Brightwater", "Oakmere", "Silverbirch"]
NAME_SECOND = ["Hardware", "Building Supplies", "Industrial", "Electrical", "Office Solutions", "Civil Supplies", "Timber",
               "Instruments", "Fasteners", "Safety", "Plumbing", "Facilities Services", "Engineering", "Trade Supplies"]
CUSTOMERS = ["Ridgeback Builders", "Pinecrest Utilities", "Facilities Dept, Harbourview Clinic", "Lowland Property Services",
             "Orchid Bay School", "Matai Street Cafe", "Bluegum Landscaping", "Tern Point Marina"]

# (description, canonical unit, min price, max price, decimal quantities allowed, max quantity)
ITEMS = [
    ("Cordless drill 18V, 2 batteries", "each", "120", "320", False, 6),
    ("Drill bit set (19 pc)", "set", "15", "60", False, 10),
    ("Nitrile safety gloves, box of 100", "box", "6", "18", False, 40),
    ("Safety glasses, clear lens", "pair", "3", "12", False, 50),
    ("Hi-vis vest, class D", "each", "6", "20", False, 40),
    ("Pre-mix concrete 32MPa, 20mm agg.", "m3", "220", "320", True, 12),
    ("Reinforcing mesh SL82 6.0 x 2.4", "sheet", "70", "120", False, 40),
    ("Formwork ply 17mm 2400x1200", "sheet", "50", "90", False, 40),
    ("Treated pine 90x45 H3.2, 4.8m", "length", "8", "18", False, 80),
    ("Galvanised pipe 25mm x 6m", "length", "25", "60", False, 60),
    ("Copper tube 15mm", "m", "6", "14", True, 120),
    ("Electrical cable 2.5mm TPS", "m", "1.2", "4", True, 300),
    ("Electrical cable 2.5mm TPS, 100m drum", "roll", "120", "260", False, 10),
    ("Elbow 90deg 25mm (galv)", "each", "1.5", "6", False, 100),
    ("Decking screws 10g x 65mm, box of 200", "box", "12", "35", False, 20),
    ("Hex bolt M12 x 80, zinc", "each", "0.15", "0.95", False, 500),
    ("Cement, general purpose 20kg", "bag", "8", "16", False, 80),
    ("Road base", "tonne", "35", "70", True, 30),
    ("Exterior paint, low sheen", "l", "12", "30", True, 60),
    ("Floor tiles 600x600, matt grey", "m2", "28", "75", True, 90),
    ("Silicone sealant, clear 300g", "each", "6", "15", False, 48),
    ("Duct tape 48mm x 30m", "roll", "4", "12", False, 48),
    ("A4 copy paper 80gsm, 5 reams", "box", "22", "40", False, 30),
    ("Toner cartridge, black", "each", "60", "180", False, 8),
    ("Cable ties 300mm, pack of 100", "pack", "4", "14", False, 30),
    ("Digital multimeter, CAT IV", "each", "90", "260", False, 6),
    ("Test leads kit", "each", "12", "40", False, 6),
    ("Electrician labour", "hour", "75", "140", True, 40),
    ("Site supervisor", "day", "450", "900", True, 10),
    ("Scaffold hire", "week", "180", "420", False, 8),
    ("Portable toilet hire", "week", "90", "180", False, 8),
    ("Cloud backup service, 2 TB", "month", "25", "90", False, 12),
    ("Excavator 5t hire incl. operator", "day", "650", "1200", True, 5),
    ("Grease, lithium 450g", "kg", "8", "20", True, 25),
]
LUMP_SUMS = ["Delivery to site", "Freight (courier)", "Installation and commissioning", "Line pump hire incl. operator (4hr)",
             "Site setup and establishment", "Disposal of offcuts", "Crane lift"]

PAYMENT_TERMS = ["Net 30 days", "30 days end of month", "Net 14 days", "COD", "100% T/T in advance",
                 "50% deposit, balance before delivery", "Payment within 7 days of invoice", "20th of the month following"]

HEADER_TYPOS = {
    "Quotation": ["Quotaton", "Qoutation", "Quotatoin"],
    "Description": ["Descripton", "Desciption"],
    "Subtotal": ["Sub-totl", "Subtotl", "Sub totla"],
    "Discount": ["Disount", "Discont"],
    "Total": ["Totl", "Toatl"],
    "Validity": ["Validty", "Valdity"],
    "Payment": ["Paymnet", "Payemnt"],
    "Quantity": ["Quantiy", "Qauntity"],
}
