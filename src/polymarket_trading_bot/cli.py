"""CLI for Polymarket Trading Bot.

``polymarket-trading-bot edge`` evaluates a bet given your probability estimate;
``polymarket-trading-bot arb`` checks a YES/NO arbitrage on a sample market.

Part of Polymarket Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import typer
from rich.console import Console

from polymarket_trading_bot import __version__
from polymarket_trading_bot.edge import expected_value, stake_fraction
from polymarket_trading_bot.market import BinaryMarket, detect_arbitrage

app = typer.Typer(add_completion=False, help="Polymarket Trading Bot — by Viprasol Tech.")
console = Console()


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"polymarket-trading-bot [bold cyan]{__version__}[/] — by Viprasol Tech")


@app.command()
def edge(true_prob: float = 0.60, price: float = 0.50, bankroll: float = 1_000.0) -> None:
    """Evaluate edge and recommended stake for a YES bet."""
    ev = expected_value(true_prob, price)
    frac = stake_fraction(true_prob, price)
    console.print(f"Your prob {true_prob:.0%} vs market price {price:.2f}")
    color = "green" if ev > 0 else "red"
    console.print(f"Expected value: [bold {color}]{ev:+.1%}[/] per $1 staked")
    console.print(f"Recommended stake: [bold]${bankroll * frac:,.2f}[/] ({frac:.1%} of bankroll)")


@app.command()
def arb(yes: float = 0.48, no: float = 0.49) -> None:
    """Check a YES/NO arbitrage on a sample binary market."""
    market = BinaryMarket(question="Will event X happen?", yes_price=yes, no_price=no)
    result = detect_arbitrage(market)
    console.print(f"YES {yes:.2f} + NO {no:.2f} = book sum {market.book_sum:.2f}")
    if result.exists:
        console.print(f"[bold green]Arbitrage:[/] +{result.profit_per_share:.3f} profit per pair")
    else:
        console.print("[yellow]No arbitrage[/] (book sums to >= 1.00)")


if __name__ == "__main__":
    app()
