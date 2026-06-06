"""Market resolution simulator.

Estimate the distribution of outcomes for a sized portfolio by Monte Carlo:
each market resolves YES with its (true) probability, paying out 1 per share
held and forfeiting the stake otherwise. This produces expected return, win
rate, volatility and a value-at-risk style worst-case estimate — useful for
sanity-checking a basket before risking capital.

The simulator is dependency-light (uses the stdlib ``random`` and ``statistics``
modules) and fully deterministic when given a seed.

Part of Polymarket Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import random
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from polymarket_trading_bot.bankroll import Allocation


@dataclass(slots=True, frozen=True)
class Position:
    """A held YES position to be resolved."""

    market_key: str
    stake: float
    price: float  # entry price (pays 1 on YES)
    true_prob: float

    def __post_init__(self) -> None:
        if not 0.0 < self.price <= 1.0:
            raise ValueError("price must be in (0, 1]")
        if not 0.0 <= self.true_prob <= 1.0:
            raise ValueError("true_prob must be in [0, 1]")
        if self.stake < 0.0:
            raise ValueError("stake must be non-negative")

    @property
    def shares(self) -> float:
        return self.stake / self.price

    def pnl_on(self, won: bool) -> float:
        """Profit/loss if the market resolves YES (``won``) or NO."""
        if won:
            return self.shares - self.stake  # redeem 1 per share, minus cost
        return -self.stake


@dataclass(slots=True, frozen=True)
class SimulationResult:
    """Summary statistics from a resolution simulation."""

    trials: int
    mean_pnl: float
    median_pnl: float
    stdev_pnl: float
    win_rate: float  # fraction of trials with positive total PnL
    best: float
    worst: float
    value_at_risk_95: float  # 5th-percentile PnL (loss is negative)

    @property
    def is_profitable_on_average(self) -> bool:
        return self.mean_pnl > 0.0


def positions_from_allocations(
    allocations: Sequence[Allocation],
    prices: Mapping[str, float],
    beliefs: Mapping[str, float],
) -> list[Position]:
    """Build resolvable positions from sized allocations.

    ``prices`` and ``beliefs`` map each allocation's ``market_key`` to its entry
    price and your true-probability estimate respectively.
    """
    positions: list[Position] = []
    for a in allocations:
        positions.append(
            Position(
                market_key=a.market_key,
                stake=a.stake,
                price=prices[a.market_key],
                true_prob=beliefs[a.market_key],
            )
        )
    return positions


def simulate(
    positions: Sequence[Position],
    trials: int = 10_000,
    seed: int | None = None,
) -> SimulationResult:
    """Monte-Carlo the total PnL of a basket over many resolutions.

    Each market independently resolves YES with probability ``true_prob``.
    Returns aggregate statistics across ``trials`` independent draws.
    """
    if trials <= 0:
        raise ValueError("trials must be positive")
    rng = random.Random(seed)

    outcomes: list[float] = []
    wins = 0
    for _ in range(trials):
        total = 0.0
        for pos in positions:
            won = rng.random() < pos.true_prob
            total += pos.pnl_on(won)
        outcomes.append(total)
        if total > 0.0:
            wins += 1

    outcomes.sort()
    var_index = max(0, int(0.05 * trials) - 1)
    stdev = statistics.pstdev(outcomes) if len(outcomes) > 1 else 0.0

    return SimulationResult(
        trials=trials,
        mean_pnl=statistics.fmean(outcomes),
        median_pnl=statistics.median(outcomes),
        stdev_pnl=stdev,
        win_rate=wins / trials,
        best=outcomes[-1],
        worst=outcomes[0],
        value_at_risk_95=outcomes[var_index],
    )
