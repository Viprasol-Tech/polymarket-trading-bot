"""Smoke tests for the Typer CLI subcommands."""

from __future__ import annotations

from typer.testing import CliRunner

from polymarket_trading_bot import __version__
from polymarket_trading_bot.cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_edge_command_reports_ev() -> None:
    result = runner.invoke(app, ["edge", "--true-prob", "0.6", "--price", "0.5"])
    assert result.exit_code == 0
    assert "Expected value" in result.stdout


def test_arb_command_finds_arbitrage() -> None:
    result = runner.invoke(app, ["arb", "--yes", "0.48", "--no", "0.49"])
    assert result.exit_code == 0
    assert "Arbitrage" in result.stdout


def test_arb_scan_command() -> None:
    result = runner.invoke(app, ["arb-scan"])
    assert result.exit_code == 0


def test_scan_command_lists_opportunities() -> None:
    result = runner.invoke(app, ["scan"])
    assert result.exit_code == 0


def test_allocate_command() -> None:
    result = runner.invoke(app, ["allocate", "--bankroll", "1000"])
    assert result.exit_code == 0
    assert "exposure" in result.stdout.lower()


def test_simulate_command() -> None:
    result = runner.invoke(app, ["simulate", "--trials", "500", "--seed", "1"])
    assert result.exit_code == 0
    assert "PnL" in result.stdout
