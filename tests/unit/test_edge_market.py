"""Tests for binary market math, arbitrage, edge, and Kelly sizing."""

from __future__ import annotations

import math

import pytest

from polymarket_trading_bot.edge import (
    EdgeReport,
    SizingConfig,
    analyze_edge,
    edge_probability,
    expected_value,
    growth_rate,
    kelly_fraction,
    stake_fraction,
)
from polymarket_trading_bot.market import BinaryMarket, detect_arbitrage


def test_market_rejects_out_of_range_price() -> None:
    with pytest.raises(ValueError):
        BinaryMarket("Q", yes_price=1.5, no_price=0.5)


def test_market_rejects_out_of_range_fee() -> None:
    with pytest.raises(ValueError):
        BinaryMarket("Q", yes_price=0.5, no_price=0.5, fee=1.0)


def test_arbitrage_when_book_under_one() -> None:
    m = BinaryMarket("Q", yes_price=0.48, no_price=0.49)  # sum 0.97
    arb = detect_arbitrage(m)
    assert arb.exists
    assert math.isclose(arb.profit_per_share, 0.03)


def test_no_arbitrage_when_book_at_one() -> None:
    m = BinaryMarket("Q", yes_price=0.5, no_price=0.5)
    assert not detect_arbitrage(m).exists


def test_arbitrage_eroded_by_fee() -> None:
    # 0.97 book with a 4% taker fee on each leg wipes out the 3% edge.
    m = BinaryMarket("Q", yes_price=0.48, no_price=0.49, fee=0.04)
    assert not detect_arbitrage(m).exists


def test_arb_profit_on_capital_scales() -> None:
    m = BinaryMarket("Q", yes_price=0.48, no_price=0.49)  # 0.03 edge, cost 0.97
    arb = detect_arbitrage(m)
    # pairs = 1000 / 0.97, profit = pairs * 0.03
    assert math.isclose(arb.profit_on(1000.0), (1000.0 / 0.97) * 0.03)


def test_no_arb_profit_when_no_edge() -> None:
    m = BinaryMarket("Q", yes_price=0.5, no_price=0.5)
    assert detect_arbitrage(m).profit_on(1000.0) == 0.0


def test_vig_and_normalized_probability() -> None:
    m = BinaryMarket("Q", yes_price=0.55, no_price=0.50)  # sum 1.05
    assert math.isclose(m.vig, 0.05)
    assert math.isclose(m.normalized_probability(), 0.55 / 1.05)


def test_expected_value_positive_when_underpriced() -> None:
    # True 60% but priced at 0.50 -> EV = 0.6/0.5 - 1 = +20%.
    assert math.isclose(expected_value(0.60, 0.50), 0.20)


def test_expected_value_negative_when_overpriced() -> None:
    assert expected_value(0.40, 0.50) < 0


def test_expected_value_rejects_bad_price() -> None:
    with pytest.raises(ValueError):
        expected_value(0.6, 0.0)


def test_edge_probability() -> None:
    assert math.isclose(edge_probability(0.60, 0.50), 0.10)


def test_kelly_zero_without_edge() -> None:
    # Fair price (price == prob) -> no edge -> Kelly 0.
    assert math.isclose(kelly_fraction(0.50, 0.50), 0.0, abs_tol=1e-9)


def test_kelly_positive_with_edge() -> None:
    assert kelly_fraction(0.60, 0.50) > 0


def test_kelly_clamped_at_extremes() -> None:
    # Certain YES (p=1) at any sub-1 price -> stake the whole bankroll.
    assert kelly_fraction(1.0, 0.01) == 1.0
    # Degenerate prices (0 or 1) return 0 (no position).
    assert kelly_fraction(0.5, 0.0) == 0.0
    assert kelly_fraction(0.5, 1.0) == 0.0


def test_growth_rate_zero_without_stake() -> None:
    assert growth_rate(0.6, 0.5, 0.0) == 0.0


def test_growth_rate_positive_at_kelly() -> None:
    # The full-Kelly stake should yield positive expected log-growth.
    f = kelly_fraction(0.60, 0.50)
    assert growth_rate(0.60, 0.50, f) > 0.0


def test_growth_rate_maximized_at_kelly() -> None:
    p, price = 0.60, 0.50
    f_star = kelly_fraction(p, price)
    g_star = growth_rate(p, price, f_star)
    # Perturbing the stake either way reduces growth.
    assert growth_rate(p, price, f_star * 0.5) < g_star
    assert growth_rate(p, price, min(0.99, f_star * 1.5)) < g_star


def test_stake_respects_min_edge_and_cap() -> None:
    # Tiny edge below min_edge -> no stake.
    assert stake_fraction(0.505, 0.50, SizingConfig(min_edge=0.02)) == 0.0
    # Large edge -> capped at max_fraction.
    capped = stake_fraction(0.90, 0.50, SizingConfig(kelly_fraction=1.0, max_fraction=0.2))
    assert math.isclose(capped, 0.2)


def test_analyze_edge_bundles_report() -> None:
    report = analyze_edge(0.60, 0.50)
    assert isinstance(report, EdgeReport)
    assert report.is_actionable
    assert math.isclose(report.expected_value, 0.20)
    assert report.full_kelly > report.stake_fraction  # half-Kelly default


def test_analyze_edge_not_actionable_below_gate() -> None:
    report = analyze_edge(0.505, 0.50)
    assert not report.is_actionable
    assert report.stake_fraction == 0.0
