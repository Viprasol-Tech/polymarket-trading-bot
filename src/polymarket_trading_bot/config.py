"""Typed configuration for the Polymarket Trading Bot.

Uses pydantic for validated, self-documenting settings shared across the
scanner, bankroll allocator and resolution simulator.

Part of Polymarket Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class BotConfig(BaseModel):
    """Validated bot configuration.

    All fractions are of the *current* bankroll. ``kelly_fraction`` scales the
    full-Kelly stake (0.5 == half-Kelly); ``max_fraction`` caps any single
    market; ``max_total_fraction`` caps the sum of all simultaneous stakes.
    """

    model_config = {"frozen": True, "extra": "forbid"}

    kelly_fraction: float = Field(default=0.5, gt=0.0, le=1.0)
    max_fraction: float = Field(default=0.2, gt=0.0, le=1.0)
    max_total_fraction: float = Field(default=0.6, gt=0.0, le=1.0)
    min_edge: float = Field(default=0.02, ge=0.0)
    taker_fee: float = Field(default=0.0, ge=0.0, lt=1.0)

    @model_validator(mode="after")
    def _check_consistency(self) -> BotConfig:
        if self.max_fraction > self.max_total_fraction:
            raise ValueError("max_fraction cannot exceed max_total_fraction")
        return self
