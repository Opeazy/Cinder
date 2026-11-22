# Backtest results (DRAFT rules)

Data: Coinbase spot, BTC-USD, ETH-USD; 4h bars built from 1h candles; 2022-01-01 to 2026-11-22 UTC. First ~200 bars per coin are indicator warm-up (no trades).

Costs: fee 0.50% per side (every fill, incl. stops), slippage 0.05% per side, min order $1. Capital $100, 1% risk/trade incl. costs, 1x, long only.

## 1. Playbook as written (both strategies, all risk limits)

| Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|
| 69 | 36% | -0.082 | $-0.087 | 0.75 | $-5.84 (-5.8%) | -37.8% | $9.95 | $+3.94 |

- Kill switch (-15% from high): **hit on 2023-01-07**
- Days with daily loss limit hit: 39
- Entries skipped: {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0}

## 2. Edge by strategy (kill switch and daily limit OFF, to see the whole period)

| Strategy | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| Trend | 257 | 30% | +0.005 | $-0.006 | 0.98 | $-1.56 (-1.6%) | -19.3% | $49.75 | $+48.19 |
| Mean reversion | 248 | 44% | -0.217 | $-0.169 | 0.30 | $-41.89 (-41.9%) | -41.9% | $34.44 | $-7.44 |
| Both | 486 | 37% | -0.106 | $-0.087 | 0.68 | $-42.34 (-42.3%) | -47.5% | $69.40 | $+27.07 |

## 3. Stability: before vs after 2024-06-01 (limits off)

| Strategy | Period | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|---|
| Trend | early | 126 | 36% | +0.049 | $+0.041 | 1.12 | $+5.17 (+5.2%) | -11.5% | $23.29 | $+28.46 |
| Trend | late | 131 | 25% | -0.037 | $-0.049 | 0.88 | $-6.39 (-6.4%) | -19.3% | $25.16 | $+18.76 |
| Mean reversion | early | 129 | 50% | -0.181 | $-0.163 | 0.38 | $-21.07 (-21.1%) | -21.8% | $19.37 | $-1.70 |
| Mean reversion | late | 119 | 38% | -0.255 | $-0.222 | 0.21 | $-26.38 (-26.4%) | -26.5% | $19.10 | $-7.28 |

## 4. Fee sensitivity (limits off)

| Strategy | Fee/side | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|---|
| Trend | 0.00% | 257 | 38% | +0.274 | $+0.354 | 1.76 | $+90.91 (+90.9%) | -16.1% | $0.00 | $+90.91 |
| Trend | 0.25% | 257 | 34% | +0.122 | $+0.122 | 1.30 | $+31.48 (+31.5%) | -17.9% | $32.21 | $+63.68 |
| Trend | 0.50% | 257 | 30% | +0.005 | $-0.006 | 0.98 | $-1.56 (-1.6%) | -19.3% | $49.75 | $+48.19 |
| Trend | 0.75% | 257 | 27% | -0.088 | $-0.086 | 0.76 | $-22.02 (-22.0%) | -28.3% | $60.36 | $+38.34 |
| Mean reversion | 0.00% | 248 | 64% | -0.045 | $-0.045 | 0.83 | $-11.24 (-11.2%) | -15.7% | $0.00 | $-11.24 |
| Mean reversion | 0.25% | 248 | 54% | -0.140 | $-0.120 | 0.51 | $-29.74 (-29.7%) | -30.2% | $20.76 | $-8.97 |
| Mean reversion | 0.50% | 248 | 44% | -0.217 | $-0.169 | 0.30 | $-41.89 (-41.9%) | -41.9% | $34.44 | $-7.44 |
| Mean reversion | 0.75% | 248 | 31% | -0.280 | $-0.203 | 0.18 | $-50.38 (-50.4%) | -50.4% | $44.03 | $-6.35 |

## 5. Trend: R by coin and year (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades |
|---|---|---|---|---|---|---|
| BTC | -2.9 | 5.6 | 5.5 | -3.3 | -6.6 | 127 |
| ETH | -0.6 | 0.3 | -1 | 7.2 | -2.7 | 130 |

## 5. Mean reversion: R by coin and year (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades |
|---|---|---|---|---|---|---|
| BTC | -5.7 | -6.1 | -8.9 | -7.1 | -4.4 | 132 |
| ETH | -3.7 | -3.2 | -9.6 | -3 | -2.1 | 116 |

## Verdict against golden rule 2 (draft criteria)

Pass needs, per strategy: >= 100 trades, profit factor >= 1.2 at 0.50% fees, positive expectancy in BOTH halves, and still positive at 0.75% fees.

- **Trend: FAIL** — trades >= 100 ✓, PF >= 1.2 ✗, early half positive ✓, late half positive ✗, positive at 0.75% fees ✗
- **Mean reversion: FAIL** — trades >= 100 ✓, PF >= 1.2 ✗, early half positive ✗, late half positive ✗, positive at 0.75% fees ✗
