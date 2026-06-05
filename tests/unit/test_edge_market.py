"""Tests for binary market math, arbitrage, edge, and Kelly sizing."""

from __future__ import annotations

import math

import pytest

from polymarket_trading_bot.edge import (
    SizingConfig,
    expected_value,
    kelly_fraction,
    stake_fraction,
)
from polymarket_trading_bot.market import BinaryMarket, detect_arbitrage


def test_market_rejects_out_of_range_price() -> None:
    with pytest.raises(ValueError):
        BinaryMarket("Q", yes_price=1.5, no_price=0.5)


def test_arbitrage_when_book_under_one() -> None:
    m = BinaryMarket("Q", yes_price=0.48, no_price=0.49)  # sum 0.97
    arb = detect_arbitrage(m)
    assert arb.exists
    assert math.isclose(arb.profit_per_share, 0.03)


def test_no_arbitrage_when_book_at_one() -> None:
    m = BinaryMarket("Q", yes_price=0.5, no_price=0.5)
    assert not detect_arbitrage(m).exists


def test_expected_value_positive_when_underpriced() -> None:
    # True 60% but priced at 0.50 -> EV = 0.6/0.5 - 1 = +20%.
    assert math.isclose(expected_value(0.60, 0.50), 0.20)


def test_expected_value_negative_when_overpriced() -> None:
    assert expected_value(0.40, 0.50) < 0


def test_kelly_zero_without_edge() -> None:
    # Fair price (price == prob) -> no edge -> Kelly 0.
    assert math.isclose(kelly_fraction(0.50, 0.50), 0.0, abs_tol=1e-9)


def test_kelly_positive_with_edge() -> None:
    assert kelly_fraction(0.60, 0.50) > 0


def test_stake_respects_min_edge_and_cap() -> None:
    # Tiny edge below min_edge -> no stake.
    assert stake_fraction(0.505, 0.50, SizingConfig(min_edge=0.02)) == 0.0
    # Large edge -> capped at max_fraction.
    capped = stake_fraction(0.90, 0.50, SizingConfig(kelly_fraction=1.0, max_fraction=0.2))
    assert math.isclose(capped, 0.2)
