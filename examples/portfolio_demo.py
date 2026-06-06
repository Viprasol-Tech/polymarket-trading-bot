"""End-to-end example: scan, size, and simulate a basket of binary markets.

Run with::

    PYTHONPATH=src python examples/portfolio_demo.py

This uses the built-in illustrative sample basket (not live Polymarket data),
so it runs offline and deterministically.

Part of Polymarket Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from polymarket_trading_bot.bankroll import allocate
from polymarket_trading_bot.config import BotConfig
from polymarket_trading_bot.edge import SizingConfig
from polymarket_trading_bot.resolution import positions_from_allocations, simulate
from polymarket_trading_bot.sample_data import sample_beliefs, sample_markets
from polymarket_trading_bot.scanner import scan_arbitrage, scan_edges


def main() -> None:
    markets = sample_markets()
    beliefs = sample_beliefs()
    bankroll = 1_000.0

    # 1) Risk-free arbitrage across the basket.
    print("== Arbitrage ==")
    for opp in scan_arbitrage(markets):
        print(f"  {opp.market.question}: +{opp.profit_per_share:.3f}/pair")

    # 2) Rank +EV directional bets.
    sizing = SizingConfig(kelly_fraction=0.5, max_fraction=0.2, min_edge=0.02)
    opps = scan_edges(markets, beliefs, sizing)
    print("\n== +EV opportunities ==")
    for opp in opps:
        print(f"  {opp.market.question}: EV {opp.report.expected_value:+.1%}")

    # 3) Size a portfolio under a total-exposure cap.
    portfolio = allocate(opps, bankroll, BotConfig(kelly_fraction=0.5, max_fraction=0.2))
    print(f"\n== Portfolio (exposure {portfolio.total_fraction:.1%}) ==")
    for a in portfolio.allocations:
        print(f"  {a.question}: ${a.stake:,.2f}")

    # 4) Monte-Carlo the resolution outcomes.
    prices = {m.slug or m.question: m.yes_price for m in markets}
    positions = positions_from_allocations(portfolio.allocations, prices, beliefs)
    result = simulate(positions, trials=10_000, seed=42)
    print("\n== Simulation ==")
    print(f"  Mean PnL: ${result.mean_pnl:,.2f}")
    print(f"  Win rate: {result.win_rate:.1%}")
    print(f"  95% VaR:  ${result.value_at_risk_95:,.2f}")


if __name__ == "__main__":
    main()
