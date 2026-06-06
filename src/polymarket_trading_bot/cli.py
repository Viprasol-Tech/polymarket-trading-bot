"""CLI for Polymarket Trading Bot.

Subcommands:

* ``version``   — print the installed version.
* ``edge``      — full edge/EV/Kelly report for one YES bet.
* ``arb``       — YES/NO arbitrage check on one market.
* ``arb-scan``  — rank risk-free arbitrage across the sample basket.
* ``scan``      — rank +EV directional bets across the sample basket.
* ``allocate``  — Kelly-size a portfolio across markets under an exposure cap.
* ``simulate``  — Monte-Carlo the sized portfolio's resolution outcomes.

Part of Polymarket Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from polymarket_trading_bot import __version__
from polymarket_trading_bot.bankroll import allocate as allocate_portfolio
from polymarket_trading_bot.config import BotConfig
from polymarket_trading_bot.edge import SizingConfig, analyze_edge
from polymarket_trading_bot.market import BinaryMarket, detect_arbitrage
from polymarket_trading_bot.resolution import positions_from_allocations, simulate
from polymarket_trading_bot.sample_data import sample_beliefs, sample_markets
from polymarket_trading_bot.scanner import scan_arbitrage, scan_edges

app = typer.Typer(add_completion=False, help="Polymarket Trading Bot - by Viprasol Tech.")
console = Console()


def _sizing(min_edge: float, kelly: float, cap: float) -> SizingConfig:
    return SizingConfig(kelly_fraction=kelly, max_fraction=cap, min_edge=min_edge)


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(f"polymarket-trading-bot [bold cyan]{__version__}[/] - by Viprasol Tech")


@app.command()
def edge(true_prob: float = 0.60, price: float = 0.50, bankroll: float = 1_000.0) -> None:
    """Evaluate edge, EV, Kelly and growth for a YES bet."""
    report = analyze_edge(true_prob, price)
    console.print(f"Your prob {true_prob:.0%} vs market price {price:.2f}")
    color = "green" if report.expected_value > 0 else "red"
    console.print(f"Expected value: [bold {color}]{report.expected_value:+.1%}[/] per $1 staked")
    console.print(f"Probability edge: [bold]{report.prob_edge:+.1%}[/]")
    console.print(f"Full Kelly: [bold]{report.full_kelly:.1%}[/]")
    stake = bankroll * report.stake_fraction
    console.print(
        f"Recommended stake: [bold]${stake:,.2f}[/] ({report.stake_fraction:.1%} of bankroll)"
    )
    console.print(f"Expected log-growth: [bold]{report.growth_rate:+.4f}[/] per bet")


@app.command()
def arb(yes: float = 0.48, no: float = 0.49, capital: float = 1_000.0) -> None:
    """Check a YES/NO arbitrage on a single binary market."""
    market = BinaryMarket(question="Will event X happen?", yes_price=yes, no_price=no)
    result = detect_arbitrage(market)
    console.print(f"YES {yes:.2f} + NO {no:.2f} = book sum {market.book_sum:.2f}")
    if result.exists:
        profit = result.profit_on(capital)
        console.print(
            f"[bold green]Arbitrage:[/] +{result.profit_per_share:.3f} per pair "
            f"-> [bold]${profit:,.2f}[/] on ${capital:,.0f}"
        )
    else:
        console.print("[yellow]No arbitrage[/] (book sums to >= 1.00)")


@app.command(name="arb-scan")
def arb_scan() -> None:
    """Rank risk-free arbitrage across the built-in sample basket."""
    opps = scan_arbitrage(sample_markets())
    if not opps:
        console.print("[yellow]No arbitrage in the sample basket[/]")
        return
    table = Table(title="Arbitrage opportunities")
    table.add_column("Market")
    table.add_column("Book sum", justify="right")
    table.add_column("Profit/pair", justify="right")
    for o in opps:
        table.add_row(o.market.question, f"{o.market.book_sum:.2f}", f"+{o.profit_per_share:.3f}")
    console.print(table)


@app.command()
def scan(min_edge: float = 0.02, kelly: float = 0.5, cap: float = 0.2) -> None:
    """Rank +EV directional bets across the built-in sample basket."""
    cfg = _sizing(min_edge, kelly, cap)
    opps = scan_edges(sample_markets(), sample_beliefs(), cfg)
    if not opps:
        console.print("[yellow]No +EV bets meet the edge gate[/]")
        return
    table = Table(title="+EV opportunities")
    table.add_column("Market")
    table.add_column("Price", justify="right")
    table.add_column("Your prob", justify="right")
    table.add_column("EV", justify="right")
    table.add_column("Stake %", justify="right")
    for o in opps:
        r = o.report
        table.add_row(
            o.market.question,
            f"{r.price:.2f}",
            f"{r.true_prob:.0%}",
            f"{r.expected_value:+.1%}",
            f"{r.stake_fraction:.1%}",
        )
    console.print(table)


@app.command()
def allocate(
    bankroll: float = 1_000.0,
    min_edge: float = 0.02,
    kelly: float = 0.5,
    cap: float = 0.2,
    max_total: float = 0.6,
) -> None:
    """Kelly-size a portfolio across the sample basket under an exposure cap."""
    sizing = _sizing(min_edge, kelly, cap)
    opps = scan_edges(sample_markets(), sample_beliefs(), sizing)
    bot_cfg = BotConfig(
        kelly_fraction=kelly, max_fraction=cap, max_total_fraction=max_total, min_edge=min_edge
    )
    portfolio = allocate_portfolio(opps, bankroll, bot_cfg)
    if not portfolio.allocations:
        console.print("[yellow]No positions sized[/]")
        return
    table = Table(title="Portfolio allocation")
    table.add_column("Market")
    table.add_column("Stake", justify="right")
    table.add_column("Fraction", justify="right")
    table.add_column("Exp. profit", justify="right")
    for a in portfolio.allocations:
        table.add_row(
            a.question, f"${a.stake:,.2f}", f"{a.fraction:.1%}", f"${a.expected_profit:,.2f}"
        )
    console.print(table)
    if portfolio.scale_applied < 1.0:
        console.print(f"[dim]Exposure cap hit: scaled basket by {portfolio.scale_applied:.2f}[/]")
    console.print(
        f"Total exposure [bold]{portfolio.total_fraction:.1%}[/] "
        f"(${portfolio.total_stake:,.2f}); expected profit "
        f"[bold green]${portfolio.total_expected_profit:,.2f}[/]"
    )


def simulate_cmd(
    bankroll: float = 1_000.0,
    trials: int = 10_000,
    seed: int = 42,
    kelly: float = 0.5,
    cap: float = 0.2,
) -> None:
    """Monte-Carlo the sized portfolio's resolution outcomes."""
    sizing = _sizing(0.02, kelly, cap)
    markets = sample_markets()
    beliefs = sample_beliefs()
    opps = scan_edges(markets, beliefs, sizing)
    bot_cfg = BotConfig(kelly_fraction=kelly, max_fraction=cap)
    portfolio = allocate_portfolio(opps, bankroll, bot_cfg)
    prices = {m.slug or m.question: m.yes_price for m in markets}
    positions = positions_from_allocations(portfolio.allocations, prices, beliefs)
    if not positions:
        console.print("[yellow]No positions to simulate[/]")
        return
    result = simulate(positions, trials=trials, seed=seed)
    console.print(f"Simulated [bold]{result.trials:,}[/] resolutions of {len(positions)} markets")
    console.print(f"Mean PnL: [bold green]${result.mean_pnl:,.2f}[/]")
    console.print(f"Median PnL: [bold]${result.median_pnl:,.2f}[/]")
    console.print(f"Std dev: [bold]${result.stdev_pnl:,.2f}[/]")
    console.print(f"Win rate: [bold]{result.win_rate:.1%}[/]")
    console.print(f"Best / Worst: [green]${result.best:,.2f}[/] / [red]${result.worst:,.2f}[/]")
    console.print(f"95% VaR: [bold red]${result.value_at_risk_95:,.2f}[/]")


# Register the simulate command under the name "simulate" (avoids shadowing import).
app.command(name="simulate")(simulate_cmd)


if __name__ == "__main__":
    app()
