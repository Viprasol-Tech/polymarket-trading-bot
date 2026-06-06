"""A small built-in basket of binary markets for demos and tests.

These are illustrative, hand-crafted numbers — not live Polymarket data — so the
CLI demos run offline and deterministically.

Part of Polymarket Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from polymarket_trading_bot.market import BinaryMarket


def sample_markets() -> list[BinaryMarket]:
    """Return a fixed basket of binary markets."""
    return [
        BinaryMarket("Will it rain in NYC tomorrow?", 0.48, 0.49, slug="nyc-rain"),
        BinaryMarket("Will Team A win the final?", 0.62, 0.40, slug="team-a-final"),
        BinaryMarket("Will the bill pass this session?", 0.30, 0.71, slug="bill-pass"),
        BinaryMarket("Will the rocket launch on schedule?", 0.55, 0.46, slug="rocket-launch"),
    ]


def sample_beliefs() -> dict[str, float]:
    """Your true-probability estimates keyed by market slug."""
    return {
        "nyc-rain": 0.50,
        "team-a-final": 0.72,
        "bill-pass": 0.28,
        "rocket-launch": 0.60,
    }
