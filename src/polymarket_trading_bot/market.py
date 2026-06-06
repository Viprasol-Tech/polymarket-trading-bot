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
    """A binary (YES/NO) prediction market.

    ``slug`` is an optional stable identifier (e.g. the Polymarket market slug);
    ``fee`` is the proportional taker fee applied per fill in ``[0, 1)``.
    """

    question: str
    yes_price: float  # in [0, 1]
    no_price: float  # in [0, 1]
    slug: str | None = None
    fee: float = 0.0

    def __post_init__(self) -> None:
        for p in (self.yes_price, self.no_price):
            if not 0.0 <= p <= 1.0:
                raise ValueError("prices must be in [0, 1]")
        if not 0.0 <= self.fee < 1.0:
            raise ValueError("fee must be in [0, 1)")

    @property
    def implied_probability(self) -> float:
        """Market-implied probability of YES (the YES price)."""
        return self.yes_price

    @property
    def book_sum(self) -> float:
        """Sum of YES and NO prices (1.0 in an efficient market)."""
        return self.yes_price + self.no_price

    @property
    def vig(self) -> float:
        """Bookmaker overround: how much the book sum exceeds 1.0.

        Positive vig means the market is taking a margin (sum > 1); negative
        vig is an arbitrage opportunity (sum < 1).
        """
        return self.book_sum - 1.0

    def normalized_probability(self) -> float:
        """YES probability with the vig removed (de-vigged fair estimate)."""
        if self.book_sum == 0.0:
            return 0.0
        return self.yes_price / self.book_sum


@dataclass(slots=True, frozen=True)
class ArbResult:
    """Result of a YES/NO arbitrage check on a single market."""

    profit_per_share: float  # guaranteed profit per $1 outcome, after the buy

    @property
    def exists(self) -> bool:
        return self.profit_per_share > 0

    def profit_on(self, capital: float) -> float:
        """Guaranteed profit from deploying ``capital`` across the pair.

        Buying one YES and one NO costs ``book_sum`` and redeems for exactly 1,
        so the return on capital scales linearly with the per-share edge.
        """
        cost_per_pair = 1.0 - self.profit_per_share
        if cost_per_pair <= 0.0:
            return 0.0
        pairs = capital / cost_per_pair
        return pairs * self.profit_per_share


def detect_arbitrage(market: BinaryMarket) -> ArbResult:
    """Buying YES + NO costs ``book_sum`` (plus fees) and always redeems for 1.

    So the guaranteed profit per pair is ``1 - book_sum - fee_cost`` when that is
    positive. Fees are charged on each of the two legs at ``market.fee``.
    """
    fee_cost = market.fee * market.book_sum
    return ArbResult(profit_per_share=max(0.0, 1.0 - market.book_sum - fee_cost))
