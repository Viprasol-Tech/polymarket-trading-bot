"""Edge and Kelly sizing for binary prediction-market bets.

If you believe the true probability of YES is ``p`` and the market sells YES at
price ``price`` (which pays 1 on success), your expected value per $1 staked is
``p / price - 1``. The Kelly fraction for this binary bet maximises long-run
growth; a fractional-Kelly cap keeps it sane.

Part of Polymarket Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def expected_value(true_prob: float, price: float) -> float:
    """Expected profit per $1 staked buying YES at ``price`` (pays 1 on win).

    Positive means a +EV bet. ``price`` must be in (0, 1].
    """
    if not 0.0 < price <= 1.0:
        raise ValueError("price must be in (0, 1]")
    return true_prob / price - 1.0


def edge_probability(true_prob: float, price: float) -> float:
    """Probability edge: how much your estimate exceeds the market price.

    A positive value means the market under-prices YES relative to your belief.
    """
    return true_prob - price


def kelly_fraction(true_prob: float, price: float) -> float:
    """Full-Kelly fraction of bankroll for a binary YES bet at ``price``.

    A YES share bought at ``price`` pays 1, so net odds ``b = (1 - price) / price``.
    Kelly: ``f = (b*p - (1-p)) / b``. Clamped to ``[0, 1]`` (long/flat only).
    """
    if not 0.0 < price < 1.0:
        return 0.0
    b = (1.0 - price) / price
    q = 1.0 - true_prob
    f = (b * true_prob - q) / b
    return max(0.0, min(1.0, f))


def growth_rate(true_prob: float, price: float, fraction: float) -> float:
    """Expected log-growth of bankroll per bet at the given stake ``fraction``.

    This is the quantity Kelly maximises: ``E[log(1 + f * outcome)]`` where a
    win returns ``b`` per unit staked and a loss returns ``-1``. Returns 0 when
    nothing is staked.
    """
    if fraction <= 0.0:
        return 0.0
    if not 0.0 < price < 1.0:
        return 0.0
    b = (1.0 - price) / price
    win_term = true_prob * math.log(1.0 + fraction * b)
    lose_factor = 1.0 - fraction
    if lose_factor <= 0.0:
        return float("-inf")
    lose_term = (1.0 - true_prob) * math.log(lose_factor)
    return win_term + lose_term


@dataclass(slots=True)
class SizingConfig:
    """Sizing parameters (lightweight, dependency-free)."""

    kelly_fraction: float = 0.5  # use half-Kelly by default
    max_fraction: float = 0.2  # never stake more than 20% on one market
    min_edge: float = 0.02  # require at least 2% EV to bet


@dataclass(slots=True, frozen=True)
class EdgeReport:
    """A full diagnostic of a single YES bet opportunity."""

    true_prob: float
    price: float
    expected_value: float
    prob_edge: float
    full_kelly: float
    stake_fraction: float
    growth_rate: float

    @property
    def is_actionable(self) -> bool:
        return self.stake_fraction > 0.0


def stake_fraction(true_prob: float, price: float, config: SizingConfig | None = None) -> float:
    """Fraction of bankroll to stake, applying the min-edge gate and caps."""
    cfg = config or SizingConfig()
    if expected_value(true_prob, price) < cfg.min_edge:
        return 0.0
    sized = kelly_fraction(true_prob, price) * cfg.kelly_fraction
    return min(sized, cfg.max_fraction)


def analyze_edge(true_prob: float, price: float, config: SizingConfig | None = None) -> EdgeReport:
    """Bundle EV, probability edge, Kelly and expected growth into one report."""
    cfg = config or SizingConfig()
    frac = stake_fraction(true_prob, price, cfg)
    return EdgeReport(
        true_prob=true_prob,
        price=price,
        expected_value=expected_value(true_prob, price),
        prob_edge=edge_probability(true_prob, price),
        full_kelly=kelly_fraction(true_prob, price),
        stake_fraction=frac,
        growth_rate=growth_rate(true_prob, price, frac),
    )
