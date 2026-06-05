"""Binary prediction-market model and arbitrage detection.

On Polymarket a binary market has YES and NO outcome shares, each priced in
``[0, 1]`` USDC and paying 1 if that outcome occurs. In a perfectly efficient
market ``yes + no == 1``. When they sum to less than 1 you can buy both sides for
a locked-in profit; more than 1 and the sell side is mispriced.

Part of Polymarket Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BinaryMarket:
    """A binary (YES/NO) prediction market."""

    question: str
    yes_price: float  # in [0, 1]
    no_price: float  # in [0, 1]

    def __post_init__(self) -> None:
        for p in (self.yes_price, self.no_price):
            if not 0.0 <= p <= 1.0:
                raise ValueError("prices must be in [0, 1]")

    @property
    def implied_probability(self) -> float:
        """Market-implied probability of YES (the YES price)."""
        return self.yes_price

    @property
    def book_sum(self) -> float:
        """Sum of YES and NO prices (1.0 in an efficient market)."""
        return self.yes_price + self.no_price


@dataclass(slots=True, frozen=True)
class ArbResult:
    """Result of a YES/NO arbitrage check on a single market."""

    profit_per_share: float  # guaranteed profit per $1 outcome, after the buy

    @property
    def exists(self) -> bool:
        return self.profit_per_share > 0


def detect_arbitrage(market: BinaryMarket) -> ArbResult:
    """Buying YES + NO costs ``book_sum`` and always redeems for exactly 1.

    So the guaranteed profit per pair is ``1 - book_sum`` when that is positive.
    """
    return ArbResult(profit_per_share=max(0.0, 1.0 - market.book_sum))
