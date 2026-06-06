"""Tests for cross-market Kelly bankroll allocation."""

from __future__ import annotations

import math

import pytest

from polymarket_trading_bot.bankroll import allocate
from polymarket_trading_bot.config import BotConfig
from polymarket_trading_bot.edge import SizingConfig
from polymarket_trading_bot.market import BinaryMarket
from polymarket_trading_bot.scanner import scan_edges


def _opps(beliefs: dict[str, float], sizing: SizingConfig) -> list:
    markets = [
        BinaryMarket("A", 0.50, 0.50, slug="a"),
        BinaryMarket("B", 0.50, 0.50, slug="b"),
        BinaryMarket("C", 0.50, 0.50, slug="c"),
    ]
    return scan_edges(markets, beliefs, sizing)


def test_allocate_sizes_each_position() -> None:
    sizing = SizingConfig(kelly_fraction=0.5, max_fraction=0.5, min_edge=0.02)
    opps = _opps({"a": 0.60, "b": 0.55}, sizing)
    cfg = BotConfig(kelly_fraction=0.5, max_fraction=0.5, max_total_fraction=0.9)
    portfolio = allocate(opps, 1_000.0, cfg)
    assert len(portfolio.allocations) == 2
    assert math.isclose(portfolio.total_stake, portfolio.total_fraction * 1_000.0)


def test_allocate_scales_down_to_total_cap() -> None:
    # Three strong edges that individually fit but together breach the cap.
    sizing = SizingConfig(kelly_fraction=1.0, max_fraction=0.3, min_edge=0.02)
    opps = _opps({"a": 0.70, "b": 0.70, "c": 0.70}, sizing)
    cfg = BotConfig(kelly_fraction=1.0, max_fraction=0.3, max_total_fraction=0.5)
    portfolio = allocate(opps, 1_000.0, cfg)
    assert portfolio.scale_applied < 1.0
    assert portfolio.total_fraction <= 0.5 + 1e-9


def test_allocate_no_scaling_when_within_cap() -> None:
    sizing = SizingConfig(kelly_fraction=0.5, max_fraction=0.2, min_edge=0.02)
    opps = _opps({"a": 0.55}, sizing)
    cfg = BotConfig(kelly_fraction=0.5, max_fraction=0.2, max_total_fraction=0.6)
    portfolio = allocate(opps, 1_000.0, cfg)
    assert portfolio.scale_applied == 1.0


def test_allocate_empty_basket() -> None:
    portfolio = allocate([], 1_000.0)
    assert portfolio.allocations == ()
    assert portfolio.total_stake == 0.0


def test_allocate_rejects_negative_bankroll() -> None:
    with pytest.raises(ValueError):
        allocate([], -1.0)


def test_expected_profit_is_stake_times_ev() -> None:
    sizing = SizingConfig(kelly_fraction=0.5, max_fraction=0.5, min_edge=0.02)
    opps = _opps({"a": 0.60}, sizing)
    portfolio = allocate(opps, 1_000.0, BotConfig(kelly_fraction=0.5, max_fraction=0.5))
    a = portfolio.allocations[0]
    assert math.isclose(a.expected_profit, a.stake * a.expected_value)
