from decimal import Decimal as D

from quote_distill.money import decimal_value, is_half_cent_tie, money_value, price_value, round_money


def test_round_half_up_not_bankers():
    assert round_money(D("24.745")) == D("24.75")
    assert round_money(D("24.735")) == D("24.74")
    assert round_money(D("-0.005")) == D("-0.01")


def test_value_formats():
    assert money_value(D("65")) == "65.00"
    assert price_value(D("0.1250")) == "0.125"
    assert price_value(D("-40")) == "-40.00"
    assert decimal_value(D("6.50")) == "6.5"
    assert decimal_value(D("24")) == "24"


def test_half_cent_tie():
    assert is_half_cent_tie(D("24.745"))
    assert not is_half_cent_tie(D("24.7425"))
    assert not is_half_cent_tie(D("24.74"))
