# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[SemVer](https://semver.org/).

## [0.2.0] - 2025

### Added
- **Multi-market scanner** (`scanner.py`): `scan_arbitrage` ranks risk-free YES/NO
  arbitrage and `scan_edges` ranks +EV directional bets across a basket of markets.
- **Cross-market Kelly bankroll management** (`bankroll.py`): sizes each +EV bet with
  fractional Kelly, then proportionally trims the whole basket to a total-exposure cap.
- **Market resolution simulator** (`resolution.py`): seeded Monte-Carlo over outcomes
  producing mean/median PnL, win rate, volatility, best/worst and a 95% value-at-risk.
- **Richer edge analytics** (`edge.py`): probability edge, expected log-growth, and an
  `analyze_edge` bundling EV, Kelly, stake and growth into an `EdgeReport`.
- **Typed configuration** (`config.py`): a frozen, validated pydantic `BotConfig`.
- **Market model** gains fee-aware arbitrage, `vig`, de-vigged `normalized_probability`,
  market `slug`, and `ArbResult.profit_on(capital)`.
- **New CLI subcommands**: `arb-scan`, `scan`, `allocate`, and `simulate`; `edge` and
  `arb` now report deeper diagnostics.
- **Example** `examples/portfolio_demo.py` walking the full scan -> size -> simulate flow.
- Test suite expanded from 8 to 52 tests covering all new and existing behaviour.

### Changed
- Bumped version to 0.2.0.

## [0.1.0] - 2025

### Added
- Initial release of polymarket-trading-bot: Polymarket prediction-market bot: edge, YES/NO arbitrage, Kelly sizing.
