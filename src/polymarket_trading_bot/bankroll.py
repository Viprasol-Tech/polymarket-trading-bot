"""Kelly bankroll management across multiple simultaneous markets.

Single-market Kelly can over-commit when you hold many positions at once. This
module sizes each +EV bet with fractional Kelly, then proportionally scales the
whole basket down if the combined exposure would breach ``max_total_fraction``.

Part of Polymarket Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from dataclasses import dataclass

from polymarket_trading_bot.config import BotConfig
from polymarket_trading_bot.edge import SizingConfig
from polymarket_trading_bot.scanner import EdgeOpportunity


@dataclass(slots=True, frozen=True)
class Allocation:
    """A sized position for one market."""

    market_key: str
    question: str
    fraction: float  # of total bankroll
    stake: float  # absolute currency amount
    expected_value: float

    @property
    def expected_profit(self) -> float:
        return self.stake * self.expected_value


@dataclass(slots=True, frozen=True)
class Portfolio:
    """A sized basket of positions plus summary statistics."""

    allocations: tuple[Allocation, ...]
    bankroll: float
    scale_applied: float  # <1.0 when the basket was trimmed to fit the cap

    @property
    def total_fraction(self) -> float:
        return sum(a.fraction for a in self.allocations)

    @property
    def total_stake(self) -> float:
        return sum(a.stake for a in self.allocations)

    @property
    def total_expected_profit(self) -> float:
        return sum(a.expected_profit for a in self.allocations)


def _sizing_config(config: BotConfig) -> SizingConfig:
    return SizingConfig(
        kelly_fraction=config.kelly_fraction,
        max_fraction=config.max_fraction,
        min_edge=config.min_edge,
    )


def allocate(
    opportunities: list[EdgeOpportunity],
    bankroll: float,
    config: BotConfig | None = None,
) -> Portfolio:
    """Size a basket of +EV opportunities under a total-exposure cap.

    Each opportunity is sized with its per-market fractional-Kelly stake. If the
    sum of fractions exceeds ``max_total_fraction``, every position is scaled by
    the same factor so the cap is respected while preserving relative weights.
    """
    if bankroll < 0.0:
        raise ValueError("bankroll must be non-negative")
    cfg = config or BotConfig()

    raw = [(o, o.report.stake_fraction) for o in opportunities if o.report.stake_fraction > 0.0]
    gross = sum(frac for _, frac in raw)

    scale = 1.0
    if gross > cfg.max_total_fraction and gross > 0.0:
        scale = cfg.max_total_fraction / gross

    allocations: list[Allocation] = []
    for opp, frac in raw:
        scaled = frac * scale
        key = opp.market.slug if opp.market.slug is not None else opp.market.question
        allocations.append(
            Allocation(
                market_key=key,
                question=opp.market.question,
                fraction=scaled,
                stake=scaled * bankroll,
                expected_value=opp.report.expected_value,
            )
        )

    return Portfolio(
        allocations=tuple(allocations),
        bankroll=bankroll,
        scale_applied=scale,
    )
