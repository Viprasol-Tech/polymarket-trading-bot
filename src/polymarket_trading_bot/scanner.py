"""Multi-market scanning: rank arbitrage and +EV opportunities across markets.

Given a basket of binary markets (and optionally your probability estimates),
the scanner surfaces the best risk-free arbitrage and the best +EV directional
bets, sorted so the most attractive opportunities come first.

Part of Polymarket Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from polymarket_trading_bot.edge import EdgeReport, SizingConfig, analyze_edge
from polymarket_trading_bot.market import ArbResult, BinaryMarket, detect_arbitrage


@dataclass(slots=True, frozen=True)
class ArbOpportunity:
    """A ranked arbitrage opportunity for one market."""

    market: BinaryMarket
    result: ArbResult

    @property
    def profit_per_share(self) -> float:
        return self.result.profit_per_share


@dataclass(slots=True, frozen=True)
class EdgeOpportunity:
    """A ranked directional (+EV) opportunity for one market."""

    market: BinaryMarket
    report: EdgeReport

    @property
    def expected_value(self) -> float:
        return self.report.expected_value


def scan_arbitrage(markets: Iterable[BinaryMarket]) -> list[ArbOpportunity]:
    """Return all profitable arbitrage opportunities, best (highest edge) first."""
    opps = [ArbOpportunity(m, detect_arbitrage(m)) for m in markets]
    profitable = [o for o in opps if o.result.exists]
    profitable.sort(key=lambda o: o.profit_per_share, reverse=True)
    return profitable


def scan_edges(
    markets: Iterable[BinaryMarket],
    beliefs: Mapping[str, float],
    config: SizingConfig | None = None,
) -> list[EdgeOpportunity]:
    """Rank +EV directional bets across markets, best EV first.

    ``beliefs`` maps a market's ``slug`` (or ``question`` when no slug is set)
    to your estimated true probability of YES. Markets without a belief, or that
    are not actionable under ``config``, are skipped.
    """
    cfg = config or SizingConfig()
    opps: list[EdgeOpportunity] = []
    for m in markets:
        key = m.slug if m.slug is not None else m.question
        if key not in beliefs:
            continue
        report = analyze_edge(beliefs[key], m.yes_price, cfg)
        if report.is_actionable:
            opps.append(EdgeOpportunity(m, report))
    opps.sort(key=lambda o: o.expected_value, reverse=True)
    return opps
