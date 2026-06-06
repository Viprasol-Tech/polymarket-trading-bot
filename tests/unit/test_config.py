"""Tests for the pydantic BotConfig."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from polymarket_trading_bot.config import BotConfig


def test_defaults_are_valid() -> None:
    cfg = BotConfig()
    assert 0.0 < cfg.kelly_fraction <= 1.0
    assert cfg.max_fraction <= cfg.max_total_fraction


def test_rejects_kelly_out_of_range() -> None:
    with pytest.raises(ValidationError):
        BotConfig(kelly_fraction=1.5)


def test_rejects_max_fraction_above_total() -> None:
    with pytest.raises(ValidationError):
        BotConfig(max_fraction=0.7, max_total_fraction=0.6)


def test_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        BotConfig(bogus=1)  # type: ignore[call-arg]


def test_is_frozen() -> None:
    cfg = BotConfig()
    with pytest.raises(ValidationError):
        cfg.kelly_fraction = 0.9  # type: ignore[misc]
