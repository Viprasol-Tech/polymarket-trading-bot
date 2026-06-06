"""Tests for the market resolution Monte-Carlo simulator."""

from __future__ import annotations

import math

import pytest

from polymarket_trading_bot.bankroll import Allocation
from polymarket_trading_bot.resolution import (
    Position,
    positions_from_allocations,
    simulate,
)


def test_position_pnl_win_and_lose() -> None:
    pos = Position("a", stake=100.0, price=0.50, true_prob=0.6)
    assert math.isclose(pos.shares, 200.0)
    assert math.isclose(pos.pnl_on(True), 100.0)  # 200 shares - 100 stake
    assert math.isclose(pos.pnl_on(False), -100.0)


def test_position_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        Position("a", stake=10.0, price=0.0, true_prob=0.5)
    with pytest.raises(ValueError):
        Position("a", stake=10.0, price=0.5, true_prob=1.5)
    with pytest.raises(ValueError):
        Position("a", stake=-1.0, price=0.5, true_prob=0.5)


def test_simulate_is_deterministic_with_seed() -> None:
    positions = [Position("a", 100.0, 0.50, 0.6), Position("b", 100.0, 0.40, 0.5)]
    r1 = simulate(positions, trials=2_000, seed=7)
    r2 = simulate(positions, trials=2_000, seed=7)
    assert r1 == r2


def test_simulate_certain_win_is_profitable() -> None:
    # A market that always resolves YES, bought below 1, must always profit.
    pos = Position("sure", stake=100.0, price=0.50, true_prob=1.0)
    result = simulate([pos], trials=500, seed=1)
    assert result.is_profitable_on_average
    assert result.win_rate == 1.0
    assert math.isclose(result.worst, 100.0)


def test_simulate_certain_loss() -> None:
    pos = Position("doomed", stake=100.0, price=0.50, true_prob=0.0)
    result = simulate([pos], trials=500, seed=1)
    assert not result.is_profitable_on_average
    assert result.win_rate == 0.0
    assert math.isclose(result.best, -100.0)


def test_simulate_var_not_above_median() -> None:
    positions = [Position("a", 100.0, 0.50, 0.55), Position("b", 100.0, 0.45, 0.50)]
    result = simulate(positions, trials=3_000, seed=3)
    assert result.value_at_risk_95 <= result.median_pnl
    assert result.worst <= result.value_at_risk_95


def test_simulate_rejects_zero_trials() -> None:
    with pytest.raises(ValueError):
        simulate([Position("a", 10.0, 0.5, 0.5)], trials=0)


def test_positions_from_allocations() -> None:
    allocs = [Allocation("a", "Q A", 0.1, 100.0, 0.2)]
    prices = {"a": 0.50}
    beliefs = {"a": 0.60}
    positions = positions_from_allocations(allocs, prices, beliefs)
    assert len(positions) == 1
    assert positions[0].price == 0.50
    assert positions[0].true_prob == 0.60
