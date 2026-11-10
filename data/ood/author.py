"""Write the out-of-distribution set: 30 hand-written quotations and their labels (docs/ood.md).

    python data/ood/author.py          # writes ood-NN.doc.txt, ood-NN.label.json and manifest.json here
    python -m quote_distill.checks data/ood

Each quotation below is written by hand, not by the generator: new layouts, new wording for the same fields, new
kinds of goods and services, and suppliers outside the generator's name lists. Labels are written as the printed
`raw` text; this script derives each `value` with the schema's rules, and the checker then verifies every raw is in
the document, every value re-derives from it, and every total adds up. Everything is fictional.
"""

import json
import re
from decimal import Decimal
from pathlib import Path

from quote_distill.money import decimal_value, money_value, price_value
from quote_distill.normalise import CURRENCY_TOKENS, NUMBER_WORDS, UNIT_BY_RAW, collapse, normalise_payment_terms

HERE = Path(__file__).resolve().parent
NS = {"state": "not_stated"}
NUMBER = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def _num(raw: str) -> Decimal:
    if raw.strip().lower() in NUMBER_WORDS:
        return Decimal(NUMBER_WORDS[raw.strip().lower()])
    n = Decimal(NUMBER.search(raw).group().replace(",", ""))
    return -abs(n) if raw.strip().startswith(("-", "(")) else n


def _s(raw, value):
    return NS if raw is None else {"state": "stated", "value": value, "raw": raw}


def text(raw):
    return _s(raw, raw and collapse(raw))


def money(raw):
    return _s(raw, raw and money_value(_num(raw)))


def price(raw):
    return _s(raw, raw and price_value(_num(raw)))


def num(raw):
    return _s(raw, raw and decimal_value(_num(raw)))


def unit(raw):
    return _s(raw, raw and UNIT_BY_RAW[raw.strip().lower()])


def currency(raw):
    return _s(raw, raw and CURRENCY_TOKENS[raw.strip()])


def terms(raw):
    return _s(raw, raw and normalise_payment_terms(raw))


def item(desc, qty, u, unit_price, total, disc=None):
    d = NS
    if disc:
        kind, raw = disc
        d = {"state": "stated", "kind": kind, "raw": raw,
             "value": decimal_value(_num(raw)) if kind == "percent" else money_value(_num(raw))}
    return {"description": text(desc), "quantity": num(qty), "unit": unit(u), "unit_price": price(unit_price),
            "discount": d, "line_total": money(total)}


def ddisc(desc, kind, rate, amount):
    return {"description": text(desc), "kind": kind, "rate": num(rate), "amount": money(amount)}


def label(supplier, quote_number, date, cur, items, subtotal, total, gst=("not_stated", None, None), discounts=(),
          validity=None, payment=None):
    """date and validity are (raw, value) pairs: their value can't be derived from raw without the locale."""
    treatment, rate, amount = gst
    return {"schema_version": "1.0.0", "supplier": text(supplier), "quote_number": text(quote_number),
            "date": _s(*date) if date else NS, "currency": currency(cur), "line_items": list(items),
            "discounts": list(discounts), "gst": {"treatment": treatment, "rate": num(rate), "amount": money(amount)},
            "subtotal": money(subtotal), "total": money(total), "validity": _s(*validity) if validity else NS,
            "payment_terms": terms(payment)}


DOCS = []


def doc(id_, locale, layout, hard_cases, body, lab):
    DOCS.append((id_, locale, layout, hard_cases, body.strip("\n") + "\n", lab))


# ---------------------------------------------------------------- Singapore

doc("ood-01", "SG", "plain email reply, prices in sentences", ["prices inside sentences, no table", "GST added in a sentence"], """
Subject: Re: Quote for meeting-room AV refresh

Hi Mr Lim,

Thanks for the site visit. As discussed, here is our quotation ref. NVT/AV/2611-07, dated 3 Nov 2026.

We propose 3 units of the 65-inch interactive display at S$412.50 per month (rental), totalling S$1,237.50, plus
one-time cabling and setup of S$86.00 for 1 lot.

Sub-total: S$1,323.50
GST at 9%: S$119.12
Amount payable: S$1,442.62

This offer is valid for 21 days. Payment: 50% deposit, balance on installation.

Best regards,
Daryl Ong
Novatone AV Rentals Pte. Ltd.
""", label("Novatone AV Rentals Pte. Ltd.", "NVT/AV/2611-07", ("3 Nov 2026", "2026-11-03"), "S$", [
    item("65-inch interactive display", "3", "units", "S$412.50", "S$1,237.50"),
    item("one-time cabling and setup", "1", "lot", "S$86.00", "S$86.00"),
], "S$1,323.50", "S$1,442.62", ("exclusive", "9%", "S$119.12"), validity=("valid for 21 days", "P21D"),
    payment="50% deposit, balance on installation."))

doc("ood-02", "SG", "key: value blocks per item", ["one item per block of key: value lines", "document discount as a percentage line"], """
PEARLSHORE PRINT STUDIO PTE LTD
Estimate no. PS-EST-55102
Issued: 09/11/2026
Currency: SGD

-- Item A --
Product: A1 foam board posters, full colour
Qty: 4
Unit: pcs
Price each: 129.00
Line amount: 516.00

-- Item B --
Product: Roll-up banner stand 85x200cm
Qty: 2
Unit: sets
Price each: 58.40
Line amount: 116.80

-- Item C --
Product: Name card printing, 100 per box
Qty: 10
Unit: boxes
Price each: 6.85
Line amount: 68.50

Items total ........ 701.30
Loyalty discount 3% ........ 21.04
GST 9% ........ 61.22
Grand total ........ 741.48

Estimate good until 30/11/2026. Terms: cash or PayNow on collection.
""", label("PEARLSHORE PRINT STUDIO PTE LTD", "PS-EST-55102", ("09/11/2026", "2026-11-09"), "SGD", [
    item("A1 foam board posters, full colour", "4", "pcs", "129.00", "516.00"),
    item("Roll-up banner stand 85x200cm", "2", "sets", "58.40", "116.80"),
    item("Name card printing, 100 per box", "10", "boxes", "6.85", "68.50"),
], "701.30", "741.48", ("exclusive", "9%", "61.22"),
    [ddisc("Loyalty discount 3%", "percent", "3%", "21.04")], ("30/11/2026", "2026-11-30"),
    "cash or PayNow on collection."))

doc("ood-03", "SG", "semicolon-separated rows", ["CSV-like rows with a header line", "GST-inclusive prices"], """
Mintleaf Catering Supplies Pte. Ltd. ; Quotation ; MCS-Q-0918
Date ; 12 November 2026
Prices in S$, inclusive of GST 9%

description;qty;uom;unit price;amount
Disposable lunch boxes, 50 per pack;12;pk;18.90;226.80
Insulated food carrier 20L;6;each;42.00;252.00
Chafing dish fuel, carton;1;box;150.00;150.00

Total (GST inclusive);628.80
GST included;51.92

Quote validity: 14 days. Payment within 7 days of delivery.
""", label("Mintleaf Catering Supplies Pte. Ltd.", "MCS-Q-0918", ("12 November 2026", "2026-11-12"), "S$", [
    item("Disposable lunch boxes, 50 per pack", "12", "pk", "18.90", "226.80"),
    item("Insulated food carrier 20L", "6", "each", "42.00", "252.00"),
    item("Chafing dish fuel, carton", "1", "box", "150.00", "150.00"),
], None, "628.80", ("inclusive", "9%", "51.92"), validity=("14 days", "P14D"),
    payment="Payment within 7 days of delivery."))

doc("ood-04", "SG", "totals first, items after", ["summary box above the line items", "service rows in days and hours"], """
QUOTATION SUMMARY                       Ref: CLD-2026-1144
Total payable (incl. 9% GST):   SGD 3,553.40
  of which GST:                 SGD 293.40
  before GST:                   SGD 3,260.00

Cloudmere IT Services Pte. Ltd.        Date: Fri, 06 Nov 2026

Breakdown
  Network audit and report        2 days   @ 1,250.00  = 2,500.00
  Engineer on-site support        8 hrs    @ 95.00     = 760.00

Valid for 30 days from the date above. Payment terms: 30 days from invoice.
""", label("Cloudmere IT Services Pte. Ltd.", "CLD-2026-1144", ("Fri, 06 Nov 2026", "2026-11-06"), "SGD", [
    item("Network audit and report", "2", "days", "1,250.00", "2,500.00"),
    item("Engineer on-site support", "8", "hrs", "95.00", "760.00"),
], "3,260.00", "3,553.40", ("exclusive", "9%", "293.40"), validity=("Valid for 30 days", "P30D"),
    payment="30 days from invoice."))

doc("ood-05", "SG", "chat message", ["informal chat text", "no GST mentioned", "no quote number"], """
[WhatsApp] Jun from Greenhook Garden Centre:
hi! quote for the planters as requested 👍
- 25 x terracotta pot 20cm @ $3.48 = $87.00
- 40 x seedling tray @ $1.15 = $46.00
- 5 x potting mix 25L bag @ $27.60 = $138.00
total $271.00
can deliver sat. payment cash on delivery
""", label("Greenhook Garden Centre", None, None, None, [
    item("terracotta pot 20cm", "25", None, "$3.48", "$87.00"),
    item("seedling tray", "40", None, "$1.15", "$46.00"),
    item("potting mix 25L bag", "5", None, "$27.60", "$138.00"),
], None, "$271.00", payment="cash on delivery"))

doc("ood-06", "SG", "boxed table with SKU column", ["SKU column to leave out of descriptions", "fixed-amount document discount"], """
+-----------+------------------------------------+-----+------+----------+-----------+
| SKU       | Item                               | Qty | UOM  | Rate S$  | Amount S$ |
+-----------+------------------------------------+-----+------+----------+-----------+
| LAB-FH-12 | Benchtop fume hood, 1.2 m          | 1   | ea   | 2,980.00 | 2,980.00  |
| LAB-PP-50 | Pipette pump set                   | 3   | set  | 145.00   | 435.00    |
| SVC-INST  | Installation and calibration       | 1   | lot  | 320.00   | 320.00    |
+-----------+------------------------------------+-----+------+----------+-----------+
Seller: Quartzline Scientific Pte Ltd     Quote No: QS/26/0331     Date: 02/11/2026
Subtotal 3,735.00 | Special discount -200.00 | GST 9% 318.15 | TOTAL S$3,853.15
Offer valid until 31 Dec 2026. Payment: 100% within 30 days of installation.
""", label("Quartzline Scientific Pte Ltd", "QS/26/0331", ("02/11/2026", "2026-11-02"), "S$", [
    item("Benchtop fume hood, 1.2 m", "1", "ea", "2,980.00", "2,980.00"),
    item("Pipette pump set", "3", "set", "145.00", "435.00"),
    item("Installation and calibration", "1", "lot", "320.00", "320.00"),
], "3,735.00", "S$3,853.15", ("exclusive", "9%", "318.15"),
    [ddisc("Special discount", "amount", None, "200.00")], ("31 Dec 2026", "2026-12-31"),
    "100% within 30 days of installation."))

# ---------------------------------------------------------------- Australia

doc("ood-07", "AU", "letter with numbered paragraphs", ["items in numbered paragraphs", "'plus GST' wording"], """
Saltbush Event Hire Pty Ltd
ABN 00 111 222 333

Our ref: SEH-4471                                    10/11/2026

Dear Ms Nguyen,

Re: Marquee hire, Spring Fair

1. Supply and erect 6x12 m marquee: 2 days at $645.00 per day, $1,290.00.
2. Trestle tables: 4 each at $88.50, $354.00.
3. Delivery and pick-up: $95.00 flat.

Total $1,739.00 plus GST of $173.90, making $1,912.90 (AUD).

This quote holds for 30 days. A 20% deposit confirms the booking; the balance is due 7 days before the event.

Kind regards,
Saltbush Event Hire Pty Ltd
""", label("Saltbush Event Hire Pty Ltd", "SEH-4471", ("10/11/2026", "2026-11-10"), "AUD", [
    item("Supply and erect 6x12 m marquee", "2", "days", "$645.00", "$1,290.00"),
    item("Trestle tables", "4", "each", "$88.50", "$354.00"),
    item("Delivery and pick-up", None, "flat", None, "$95.00"),
], "$1,739.00", "$1,912.90", ("exclusive", None, "$173.90"), validity=("30 days", "P30D"),
    payment="A 20% deposit confirms the booking; the balance is due 7 days before the event."))

doc("ood-08", "AU", "trade quote with decimal metres", ["decimal quantity in metres", "two-line header"], """
GUMLEAF FENCING CONTRACTORS PTY LTD
QUOTE  Q-26-889      Date 04/11/2026      AUD

Description                               Qty    Unit    Rate      Total
Colorbond fence panel supply & install    18.5   lm      64.00     1,184.00
Post concreting                           6      ea      32.75     196.50
                                                       Sub total    1,380.50
                                                       GST 10%        138.05
                                                       TOTAL        1,518.55
Payment: COD. Quote valid until 04/12/2026.
""", label("GUMLEAF FENCING CONTRACTORS PTY LTD", "Q-26-889", ("04/11/2026", "2026-11-04"), "AUD", [
    item("Colorbond fence panel supply & install", "18.5", "lm", "64.00", "1,184.00"),
    item("Post concreting", "6", "ea", "32.75", "196.50"),
], "1,380.50", "1,518.55", ("exclusive", "10%", "138.05"), validity=("04/12/2026", "2026-12-04"), payment="COD."))

doc("ood-09", "AU", "markdown bullet list, GST inclusive", ["bullet list with bold prices", "GST included in prices"], """
## Quote from Wombat Ridge Solar Pty Ltd
**Quote #:** WRS-0451  **Date:** 12/11/2026

- **Battery inverter 5 kW** × 3 @ $219.00 (monthly lease) = **$657.00**
- **Install and commissioning** × 1 @ $1,480.00 = **$1,480.00**

**Total (incl. GST): $2,137.00**
*GST component: $194.27 (10%)*

Prices in Australian dollars. Payment 14 days. Valid 45 days.
""", label("Wombat Ridge Solar Pty Ltd", "WRS-0451", ("12/11/2026", "2026-11-12"), "Australian dollars", [
    item("Battery inverter 5 kW", "3", None, "$219.00", "$657.00"),
    item("Install and commissioning", "1", None, "$1,480.00", "$1,480.00"),
], None, "$2,137.00", ("inclusive", "10%", "$194.27"), validity=("Valid 45 days", "P45D"), payment="Payment 14 days."))

doc("ood-10", "AU", "wide table with columns in a new order", ["amount column first", "early-payment discount is conditional"], """
Tea Tree Office Furniture Pty Ltd       Quotation TT-77310
Prepared 03/11/2026 for Kurrajong Legal

Amount ($)   Qty  Unit  Unit $   Description
496.00       40   ea    12.40    Desk cable tray
158.00       40   ea    3.95     Cable tie mount
370.00       2    ea    185.00   Mobile pedestal, 3 drawer

Net 1,024.00
Volume discount 5% (51.20)
GST 10% 97.28
Total AUD 1,070.08

Terms: 30 days; 2% off if paid within 7 days. Quote valid 60 days.
""", label("Tea Tree Office Furniture Pty Ltd", "TT-77310", ("03/11/2026", "2026-11-03"), "AUD", [
    item("Desk cable tray", "40", "ea", "12.40", "496.00"),
    item("Cable tie mount", "40", "ea", "3.95", "158.00"),
    item("Mobile pedestal, 3 drawer", "2", "ea", "185.00", "370.00"),
], "1,024.00", "1,070.08", ("exclusive", "10%", "97.28"),
    [ddisc("Volume discount 5%", "percent", "5%", "51.20")], ("valid 60 days", "P60D"),
    "30 days; 2% off if paid within 7 days."))

doc("ood-11", "AU", "export quote, GST-free", ["GST-free export wording", "monthly service row"], """
BLUEWREN MARINE ELECTRONICS PTY LTD — EXPORT QUOTATION
No. BME-EX-2026-019    Date: 11 November 2026    Currency: AUD

1  Radar and chartplotter package, fitted     1 lot      3,600.00     3,600.00
2  Remote monitoring subscription             12 months  48.00        576.00

Subtotal                    4,176.00
GST                         Nil (GST-free export)
Total                       4,176.00

Valid until 31 December 2026. Payment by telegraphic transfer before shipment.
""", label("BLUEWREN MARINE ELECTRONICS PTY LTD", "BME-EX-2026-019", ("11 November 2026", "2026-11-11"), "AUD", [
    item("Radar and chartplotter package, fitted", "1", "lot", "3,600.00", "3,600.00"),
    item("Remote monitoring subscription", "12", "months", "48.00", "576.00"),
], "4,176.00", "4,176.00", ("not_charged", None, None), validity=("31 December 2026", "2026-12-31"),
    payment="Payment by telegraphic transfer before shipment."))

doc("ood-12", "AU", "receipt-style narrow columns", ["narrow receipt layout", "quantity after the price"], """
  KOOKABURRA CLEANING CO PTY LTD
     QUOTE KCC-2210
     01/11/2026
--------------------------------
Floor scrubber pads
  74.90 x 5 box        374.50
Microfibre cloths
  19.90 x 5 pk          99.50
Callout fee
  45.00 x 1             45.00
--------------------------------
SUBTOTAL               519.00
GST 10%                 51.90
TOTAL A$               570.90
--------------------------------
  Valid 7 days. EFT on order.
""", label("KOOKABURRA CLEANING CO PTY LTD", "KCC-2210", ("01/11/2026", "2026-11-01"), "A$", [
    item("Floor scrubber pads", "5", "box", "74.90", "374.50"),
    item("Microfibre cloths", "5", "pk", "19.90", "99.50"),
    item("Callout fee", "1", None, "45.00", "45.00"),
], "519.00", "570.90", ("exclusive", "10%", "51.90"), validity=("Valid 7 days", "P7D"), payment="EFT on order."))

# ---------------------------------------------------------------- New Zealand

doc("ood-13", "NZ", "proposal with a fee table", ["consulting fees in days", "GST line labelled 'Add GST'"], """
Fernglade Consulting Limited
Proposal and fee quote — reference FGC-P-118
5 November 2026

Fees
  Stage 1 workshop facilitation ......... 2 days x $1,125.00 = $2,250.00
  Travel and materials ................... 1 lot  x $389.00   = $389.00

Fees excl. GST     $2,639.00
Add GST 15%        $395.85
Total incl. GST    $3,034.85
All figures in NZD.

This proposal is open for 30 days. Invoices are payable on the 20th of the month following.
""", label("Fernglade Consulting Limited", "FGC-P-118", ("5 November 2026", "2026-11-05"), "NZD", [
    item("Stage 1 workshop facilitation", "2", "days", "$1,125.00", "$2,250.00"),
    item("Travel and materials", "1", "lot", "$389.00", "$389.00"),
], "$2,639.00", "$3,034.85", ("exclusive", "15%", "$395.85"), validity=("open for 30 days", "P30D"),
    payment="Invoices are payable on the 20th of the month following."))

doc("ood-14", "NZ", "pipe table, GST inclusive", ["prices include GST", "number words for quantity"], """
Kowhai Kitchenware Ltd | Quote KK-3020 | 9 November 2026 | NZ$

| What | How many | Each | Line |
|---|---|---|---|
| Stainless gastronorm pan 1/1 | 30 | 22.50 | 675.00 |
| Silicone spatula | 15 | 9.80 | 147.00 |
| Freight to Napier | one | 120.00 | 120.00 |

Total incl GST: 942.00 (includes GST of 122.87 at 15%)
Price valid for 14 days. Payment on the 20th of the following month.
""", label("Kowhai Kitchenware Ltd", "KK-3020", ("9 November 2026", "2026-11-09"), "NZ$", [
    item("Stainless gastronorm pan 1/1", "30", None, "22.50", "675.00"),
    item("Silicone spatula", "15", None, "9.80", "147.00"),
    item("Freight to Napier", "one", None, "120.00", "120.00"),
], None, "942.00", ("inclusive", "15%", "122.87"), validity=("valid for 14 days", "P14D"),
    payment="Payment on the 20th of the following month."))

doc("ood-15", "NZ", "two-column layout with notes", ["notes column beside items", "percentage discount on the whole quote"], """
TUATARA TRAINING SERVICES LTD                         QUOTE TTS-6602
                                                       Date: 02/11/2026
Course                          Seats  Fee/seat   Total     Notes
First aid level 1               8      142.00     1,136.00  on site
Fire warden refresher           8      36.00      288.00    online module

                                       Subtotal   1,424.00
                                       Less 10% group discount  142.40
                                       GST @ 15%  192.24
                                       Total NZD  1,473.84
Booking confirmed on payment; quote valid for 30 days.
""", label("TUATARA TRAINING SERVICES LTD", "TTS-6602", ("02/11/2026", "2026-11-02"), "NZD", [
    item("First aid level 1", "8", None, "142.00", "1,136.00"),
    item("Fire warden refresher", "8", None, "36.00", "288.00"),
], "1,424.00", "1,473.84", ("exclusive", "15%", "192.24"),
    [ddisc("10% group discount", "percent", "10%", "142.40")], ("valid for 30 days", "P30D"),
    "Booking confirmed on payment"))

doc("ood-16", "NZ", "plant nursery list, rates per unit in cents", ["many small unit prices", "GST line starts with the rate"], """
Matai Grove Nursery Limited
Quote no. MGN/2611/04 — 12/11/2026

Seedlings, flax (Phormium), 1 L pots    120 pcs @ 2.35    282.00
Native grass plugs, tray of 10           60 pcs @ 4.10    246.00

Total before tax     528.00
15% GST              79.20
To pay (NZD)         607.20
Valid until 12/12/2026. Payment 7 days.
""", label("Matai Grove Nursery Limited", "MGN/2611/04", ("12/11/2026", "2026-11-12"), "NZD", [
    item("Seedlings, flax (Phormium), 1 L pots", "120", "pcs", "2.35", "282.00"),
    item("Native grass plugs, tray of 10", "60", "pcs", "4.10", "246.00"),
], "528.00", "607.20", ("exclusive", "15%", "79.20"), validity=("12/12/2026", "2026-12-12"), payment="Payment 7 days."))

doc("ood-17", "NZ", "email, no GST mentioned", ["GST never mentioned", "bare $ with NZ address"], """
From: quotes@pohutukawa-signs.example
To: office@client.example
Subject: Signage quote PS-2026-552

Kia ora Hemi,

Pohutukawa Signs Limited is happy to quote as follows (quote PS-2026-552, 6 November 2026):

  Shopfront lightbox 2400 x 600 ........ 1 at $860.00 ........ $860.00
  Vinyl window graphics ................ 3 at $215.00 ........ $645.00
  A-frame footpath sign ................ 2 at $64.50 ......... $129.00

Total $1,634.00. Payment 50% upfront, 50% on install. Ngā mihi.
""", label("Pohutukawa Signs Limited", "PS-2026-552", ("6 November 2026", "2026-11-06"), None, [
    item("Shopfront lightbox 2400 x 600", "1", None, "$860.00", "$860.00"),
    item("Vinyl window graphics", "3", None, "$215.00", "$645.00"),
    item("A-frame footpath sign", "2", None, "$64.50", "$129.00"),
], None, "$1,634.00", payment="Payment 50% upfront, 50% on install."))

doc("ood-18", "NZ", "tabbed columns, labour and parts", ["labour hours and parts mixed", "'Grand Total' label"], """
Rimu Valley Auto Electrical Ltd
QUOTE RVA-0087	Date 10 November 2026	NZ$
Item	Qty	Unit	Rate	Amount
Alternator rebuild	6	each	310.00	1,860.00
Labour	6	hrs	45.00	270.00
Diagnostics	1	flat	180.00	180.00
Subtotal	2,310.00
GST 15%	346.50
Grand Total	2,656.50
Quote valid 14 days. Account customers 20th of month.
""", label("Rimu Valley Auto Electrical Ltd", "RVA-0087", ("10 November 2026", "2026-11-10"), "NZ$", [
    item("Alternator rebuild", "6", "each", "310.00", "1,860.00"),
    item("Labour", "6", "hrs", "45.00", "270.00"),
    item("Diagnostics", "1", "flat", "180.00", "180.00"),
], "2,310.00", "2,656.50", ("exclusive", "15%", "346.50"), validity=("valid 14 days", "P14D"),
    payment="Account customers 20th of month."))

# ---------------------------------------------------------------- Malaysia

doc("ood-19", "MY", "bilingual headings", ["Malay and English headings", "no tax line"], """
SEBUT HARGA / QUOTATION
Cendana Lab Glassware Sdn. Bhd.
No. Rujukan / Ref No: CLG-SH-26-212      Tarikh / Date: 05-11-2026
Mata wang / Currency: RM

Bil  Perkara / Description          Kuantiti / Qty   Harga Seunit / Unit Price   Jumlah / Amount
1    Beaker 500 ml, borosilicate    10 pcs           38.50                       385.00
2    Measuring cylinder 100 ml      10 pcs           12.20                       122.00
3    Burette with PTFE stopcock     4 pcs            88.00                       352.00

Jumlah Keseluruhan / Grand Total: RM 859.00
Sah sehingga / Valid until: 05-12-2026
Terma / Terms: 30 hari / 30 days
""", label("Cendana Lab Glassware Sdn. Bhd.", "CLG-SH-26-212", ("05-11-2026", "2026-11-05"), "RM", [
    item("Beaker 500 ml, borosilicate", "10", "pcs", "38.50", "385.00"),
    item("Measuring cylinder 100 ml", "10", "pcs", "12.20", "122.00"),
    item("Burette with PTFE stopcock", "4", "pcs", "88.00", "352.00"),
], None, "RM 859.00", validity=("05-12-2026", "2026-12-05"), payment="30 hari / 30 days"))

doc("ood-20", "MY", "machinery quote with fixed discount", ["fixed-amount discount", "'Nett Total' label"], """
Kenanga Industrial Pumps Sdn Bhd
QUOTATION KIP/Q/2026/0778
Date: 09/11/2026      Currency: MYR

No | Description                              | Qty | Unit | U/Price  | Total
1  | Centrifugal pump 7.5 kW c/w motor        | 2   | set  | 1,890.00 | 3,780.00
2  | Pressure gauge and valve kit             | 2   | set  | 240.00   | 480.00

Gross Total      4,260.00
Less: Discount   150.00
Nett Total       4,110.00

Delivery 4-6 weeks. Validity 30 days. Payment: 30% with PO, 70% before delivery.
""", label("Kenanga Industrial Pumps Sdn Bhd", "KIP/Q/2026/0778", ("09/11/2026", "2026-11-09"), "MYR", [
    item("Centrifugal pump 7.5 kW c/w motor", "2", "set", "1,890.00", "3,780.00"),
    item("Pressure gauge and valve kit", "2", "set", "240.00", "480.00"),
], "4,260.00", "4,110.00", discounts=[ddisc("Discount", "amount", None, "150.00")],
    validity=("Validity 30 days", "P30D"), payment="30% with PO, 70% before delivery."))

doc("ood-21", "MY", "stationery list with kg and rolls", ["weight and roll units", "currency as a word"], """
Teratai Stationery & Packaging Enterprise
Quote: TSP-1904 / Date: 11/11/2026 / Ringgit

Packing string, natural jute ..... 50 kg ..... @7.60 ..... 380.00
Bubble wrap 1m x 50m ............. 20 roll ... @15.25 .... 305.00

TOTAL 685.00
Prices valid 7 days. Cash or cheque upon delivery.
""", label("Teratai Stationery & Packaging Enterprise", "TSP-1904", ("11/11/2026", "2026-11-11"), "Ringgit", [
    item("Packing string, natural jute", "50", "kg", "7.60", "380.00"),
    item("Bubble wrap 1m x 50m", "20", "roll", "15.25", "305.00"),
], None, "685.00", validity=("valid 7 days", "P7D"), payment="Cash or cheque upon delivery."))

doc("ood-22", "MY", "export quote, tax not applicable", ["tax explicitly not applicable", "lump-sum installation"], """
MERANTI SOLAR SYSTEMS SDN. BHD.
Proforma quotation  MSS-PQ-0093
Date: 02/11/2026   Currency: USD (for export to Brunei)

1. Rooftop PV array 10 kWp, supply only        1 lot   4,200.00   4,200.00
2. Mounting rails and clamps                   1 lot     650.00     650.00
3. Site survey                                 3 days    120.00     360.00

Sub-total            5,210.00
Sales tax            Not applicable (export)
Total payable        5,210.00

Offer valid until 31-12-2026. Payment: irrevocable L/C at sight.
""", label("MERANTI SOLAR SYSTEMS SDN. BHD.", "MSS-PQ-0093", ("02/11/2026", "2026-11-02"), "USD", [
    item("Rooftop PV array 10 kWp, supply only", "1", "lot", "4,200.00", "4,200.00"),
    item("Mounting rails and clamps", "1", "lot", "650.00", "650.00"),
    item("Site survey", "3", "days", "120.00", "360.00"),
], "5,210.00", "5,210.00", ("not_charged", None, None), validity=("31-12-2026", "2026-12-31"),
    payment="irrevocable L/C at sight."))

doc("ood-23", "MY", "food supplier price confirmation", ["'price confirmation' instead of quotation", "litre units"], """
PRICE CONFIRMATION
Seri Pandan Food Ingredients Sdn Bhd          Doc no: SPF-PC-4410
Date: 06/11/2026                               RM

Coconut milk, UHT 1 litre carton    24 l   11.75   282.00
Palm sugar block                     12 kg   26.40   316.80

Total RM 598.80
Prices hold until 30/11/2026. Payment 14 days from delivery.
""", label("Seri Pandan Food Ingredients Sdn Bhd", "SPF-PC-4410", ("06/11/2026", "2026-11-06"), "RM", [
    item("Coconut milk, UHT 1 litre carton", "24", "l", "11.75", "282.00"),
    item("Palm sugar block", "12", "kg", "26.40", "316.80"),
], None, "598.80", validity=("30/11/2026", "2026-11-30"), payment="Payment 14 days from delivery."))

doc("ood-24", "MY", "dash-separated rows, no headers", ["rows without column headers", "unit word inside the description"], """
Rafflesia Scaffold Rental Enterprise - quote RSR/26/115 - 10-11-2026 - MYR

Frame scaffold set (rental) - 3 set - 980.00 - 2,940.00
Safety netting roll (rental) - 3 roll - 125.00 - 375.00

Total: 3,315.00
Rental period 4 weeks; quote valid 10 days. Payment in advance.
""", label("Rafflesia Scaffold Rental Enterprise", "RSR/26/115", ("10-11-2026", "2026-11-10"), "MYR", [
    item("Frame scaffold set (rental)", "3", "set", "980.00", "2,940.00"),
    item("Safety netting roll (rental)", "3", "roll", "125.00", "375.00"),
], None, "3,315.00", validity=("quote valid 10 days", "P10D"), payment="Payment in advance."))

# ---------------------------------------------------------------- United States

doc("ood-25", "US", "web-store style cart quote", ["cart layout", "subtotal and total both printed"], """
Bayou Bend Office Tech LLC — Quote #BB-104417
Created: November 4, 2026        Prices in USD

Item                                Price      Qty    Subtotal
27" monitor, USB-C                  $349.99    4      $1,399.96
Monitor arm, single                 $79.99     4      $319.96
Setup service                       $49.00     1      $49.00

Order subtotal: $1,768.92
Quote total: $1,768.92

Quote expires December 4, 2026. Net 30 for approved accounts.
""", label("Bayou Bend Office Tech LLC", "BB-104417", ("November 4, 2026", "2026-11-04"), "USD", [
    item('27" monitor, USB-C', "4", None, "$349.99", "$1,399.96"),
    item("Monitor arm, single", "4", None, "$79.99", "$319.96"),
    item("Setup service", "1", None, "$49.00", "$49.00"),
], "$1,768.92", "$1,768.92", validity=("December 4, 2026", "2026-12-04"), payment="Net 30 for approved accounts."))

doc("ood-26", "US", "fasteners list with sub-dollar prices", ["sub-dollar unit prices", "MM/DD/YYYY date"], """
Prairie Lark Fastener Supply Inc.
Quote PLF-77-2091    Date 11/09/2026

QTY   UNIT   PART DESCRIPTION                     EACH     EXTENDED
200   ea     Hex bolt 3/8-16 x 1-1/2, zinc        0.42     84.00
50    bx     Wood screw #8 x 1-1/4, box of 100    3.15     157.50
1     lot    Freight, LTL                         75.00    75.00

TOTAL US$ 316.50
Terms Net 30. Pricing good 30 days.
""", label("Prairie Lark Fastener Supply Inc.", "PLF-77-2091", ("11/09/2026", "2026-11-09"), "US$", [
    item("Hex bolt 3/8-16 x 1-1/2, zinc", "200", "ea", "0.42", "84.00"),
    item("Wood screw #8 x 1-1/4, box of 100", "50", "bx", "3.15", "157.50"),
    item("Freight, LTL", "1", "lot", "75.00", "75.00"),
], None, "316.50", validity=("good 30 days", "P30D"), payment="Net 30."))

doc("ood-27", "US", "contractor bid", ["'bid' instead of quotation", "fractional percent discount"], """
GRANITE NOTCH ROOFING CORP.
BID / PROPOSAL No. GNR-B-3318
Date: November 2, 2026
Project: Library annex re-roof

Scope                                        Qty   Unit    Unit Cost    Cost
Tear-off and re-roof, 30-yr shingle          2     lot     2,450.00     4,900.00
Replace rotted decking                       16    sheets  95.00        1,520.00

Base bid                                                  6,420.00
Municipal discount 7.5%                                   481.50
Bid total (USD)                                           5,938.50

This bid may be withdrawn if not accepted within 45 days. Payment: progress billing, net 15.
""", label("GRANITE NOTCH ROOFING CORP.", "GNR-B-3318", ("November 2, 2026", "2026-11-02"), "USD", [
    item("Tear-off and re-roof, 30-yr shingle", "2", "lot", "2,450.00", "4,900.00"),
    item("Replace rotted decking", "16", "sheets", "95.00", "1,520.00"),
], "6,420.00", "5,938.50", discounts=[ddisc("Municipal discount 7.5%", "percent", "7.5%", "481.50")],
    validity=("45 days", "P45D"), payment="progress billing, net 15."))

doc("ood-28", "US", "medical supply quote, no tax line", ["case and box units", "dates spelled 'Nov 10, 2026'"], """
Cedar Hollow Medical Supply, LLC
Quotation CHM-Q-56012 | Nov 10, 2026 | US dollars

Exam gloves, nitrile, case of 10 boxes      12 boxes   $64.80    $777.60
Sharps container 8 qt                        6 each     $129.50   $777.00

Total: $1,554.60
Quote valid through Dec 10, 2026. Payment terms: Net 45.
""", label("Cedar Hollow Medical Supply, LLC", "CHM-Q-56012", ("Nov 10, 2026", "2026-11-10"), "US dollars", [
    item("Exam gloves, nitrile, case of 10 boxes", "12", "boxes", "$64.80", "$777.60"),
    item("Sharps container 8 qt", "6", "each", "$129.50", "$777.00"),
], None, "$1,554.60", validity=("Dec 10, 2026", "2026-12-10"), payment="Net 45."))

doc("ood-29", "US", "software and services quote", ["monthly licences", "one-off onboarding"], """
QUOTE
Northfield Byteworks Inc.  ·  Q-2026-1187  ·  November 6, 2026

Line 1 — Onboarding and data migration — 1 lot — $1,200.00 — $1,200.00
Line 2 — Helpdesk seat licence, first month — 10 each — $45.00 — $450.00
Line 3 — Backup storage add-on, first month — 10 each — $18.00 — $180.00

Subtotal $1,830.00 · Total due USD 1,830.00
Valid for 30 days. Billing: monthly in advance, net 15.
""", label("Northfield Byteworks Inc.", "Q-2026-1187", ("November 6, 2026", "2026-11-06"), "USD", [
    item("Onboarding and data migration", "1", "lot", "$1,200.00", "$1,200.00"),
    item("Helpdesk seat licence, first month", "10", "each", "$45.00", "$450.00"),
    item("Backup storage add-on, first month", "10", "each", "$18.00", "$180.00"),
], "$1,830.00", "1,830.00", validity=("Valid for 30 days", "P30D"), payment="monthly in advance, net 15."))

doc("ood-30", "US", "export quote to Singapore, tax not charged", ["export wording", "'pairs' unit"], """
Ridgeline Safety Footwear Inc.
EXPORT QUOTE RSF-EXP-0442      November 12, 2026
Ship to: Singapore      All prices US$

Steel-toe boot, size run 7-12        3 pairs    575.00     1,725.00
Replacement insoles                   3 pairs     62.25       186.75

Subtotal          1,911.75
Sales tax         not charged on export
Total             1,911.75

Valid 30 days. Payment: wire transfer in advance.
""", label("Ridgeline Safety Footwear Inc.", "RSF-EXP-0442", ("November 12, 2026", "2026-11-12"), "US$", [
    item("Steel-toe boot, size run 7-12", "3", "pairs", "575.00", "1,725.00"),
    item("Replacement insoles", "3", "pairs", "62.25", "186.75"),
], "1,911.75", "1,911.75", ("not_charged", None, None), validity=("Valid 30 days", "P30D"),
    payment="wire transfer in advance."))


def main() -> None:
    entries = []
    for id_, locale, layout, hard_cases, body, lab in DOCS:
        (HERE / f"{id_}.doc.txt").write_text(body, encoding="utf-8")
        (HERE / f"{id_}.label.json").write_text(json.dumps(lab, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        entries.append({"id": id_, "layout": layout, "hard_cases": hard_cases, "locale": locale,
                        "expected_check_failures": []})
    manifest = {"description": "Out-of-distribution quotations, written by hand in layouts and wording the generator "
                               "never produces (docs/ood.md). All suppliers, people, addresses and prices are "
                               "fictional. Never used for training or prompt tuning.",
                "seeds": entries}
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} documents to {HERE}")


if __name__ == "__main__":
    main()
