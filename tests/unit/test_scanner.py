"""Tests for the multi-market scanner."""

from __future__ import annotations

from polymarket_trading_bot.edge import SizingConfig
from polymarket_trading_bot.market import BinaryMarket
from polymarket_trading_bot.scanner import scan_arbitrage, scan_edges


def test_scan_arbitrage_ranks_best_first() -> None:
    markets = [
        BinaryMarket("A", 0.49, 0.50, slug="a"),  # sum 0.99 -> 0.01 edge
        BinaryMarket("B", 0.45, 0.45, slug="b"),  # sum 0.90 -> 0.10 edge
        BinaryMarket("C", 0.50, 0.50, slug="c"),  # sum 1.00 -> none
    ]
    opps = scan_arbitrage(markets)
    assert [o.market.slug for o in opps] == ["b", "a"]
    assert opps[0].profit_per_share > opps[1].profit_per_share


def test_scan_arbitrage_empty_when_efficient() -> None:
    markets = [BinaryMarket("A", 0.5, 0.5), BinaryMarket("B", 0.6, 0.45)]
    assert scan_arbitrage(markets) == []


def test_scan_edges_ranks_and_filters() -> None:
    markets = [
        BinaryMarket("A", 0.50, 0.50, slug="a"),  # belief 0.60 -> +20% EV
        BinaryMarket("B", 0.50, 0.50, slug="b"),  # belief 0.55 -> +10% EV
        BinaryMarket("C", 0.50, 0.50, slug="c"),  # belief 0.50 -> 0 EV (filtered)
    ]
    beliefs = {"a": 0.60, "b": 0.55, "c": 0.50}
    opps = scan_edges(markets, beliefs, SizingConfig(min_edge=0.02))
    assert [o.market.slug for o in opps] == ["a", "b"]
    assert opps[0].expected_value > opps[1].expected_value


def test_scan_edges_skips_markets_without_belief() -> None:
    markets = [BinaryMarket("A", 0.50, 0.50, slug="a")]
    assert scan_edges(markets, {}, SizingConfig()) == []


def test_scan_edges_uses_question_when_no_slug() -> None:
    markets = [BinaryMarket("Will X?", 0.50, 0.50)]
    opps = scan_edges(markets, {"Will X?": 0.60}, SizingConfig())
    assert len(opps) == 1
