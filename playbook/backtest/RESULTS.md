# Backtest results (DRAFT rules)

Data: Coinbase spot, BTC-USD, ETH-USD, SOL-USD, XRP-USD, DOGE-USD, ADA-USD, LINK-USD, AVAX-USD; 4h bars built from 1h candles; 2022-01-01 to 2026-11-22 UTC. First ~200 bars per coin are indicator warm-up (no trades).

Costs: fee 0.50% per side (every fill, incl. stops), slippage 0.05% per side, min order $1. Capital $100, 1% risk/trade incl. costs, 1x, long only.

## 1. Playbook as written (both strategies, all risk limits)

| Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|
| 72 | 38% | -0.190 | $-0.185 | 0.53 | $-13.30 (-13.3%) | -15.9% | $7.48 | $-5.82 |

- Kill switch (-15% from high): **hit on 2022-06-26**
- Days with daily loss limit hit: 1
- Entries skipped: {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0}

## 2. Edge by strategy (kill switch and daily limit OFF, to see the whole period)

| Strategy | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| Trend | 930 | 29% | -0.071 | $-0.059 | 0.80 | $-55.01 (-55.0%) | -59.2% | $93.83 | $+38.82 |
| Mean reversion | 795 | 49% | -0.176 | $-0.096 | 0.40 | $-76.31 (-76.3%) | -76.5% | $55.68 | $-20.64 |
| Both | 1639 | 38% | -0.121 | $-0.054 | 0.66 | $-88.21 (-88.2%) | -88.6% | $95.28 | $+7.08 |

## 3. Stability: before vs after 2024-06-01 (limits off)

| Strategy | Period | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|---|
| Trend | early | 447 | 30% | -0.054 | $-0.059 | 0.81 | $-26.54 (-26.5%) | -37.7% | $49.10 | $+22.56 |
| Trend | late | 484 | 28% | -0.088 | $-0.080 | 0.78 | $-38.82 (-38.8%) | -49.1% | $60.90 | $+22.07 |
| Mean reversion | early | 380 | 53% | -0.129 | $-0.105 | 0.47 | $-39.88 (-39.9%) | -40.8% | $35.66 | $-4.21 |
| Mean reversion | late | 417 | 46% | -0.217 | $-0.145 | 0.29 | $-60.56 (-60.6%) | -60.8% | $33.32 | $-27.24 |

## 4. Fee sensitivity (limits off)

| Strategy | Fee/side | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|---|
| Trend | 0.00% | 887 | 33% | +0.091 | $+0.075 | 1.14 | $+66.76 (+66.8%) | -32.7% | $0.00 | $+66.76 |
| Trend | 0.25% | 909 | 32% | +0.002 | $-0.015 | 0.96 | $-13.40 (-13.4%) | -40.2% | $68.89 | $+55.50 |
| Trend | 0.50% | 930 | 29% | -0.071 | $-0.059 | 0.80 | $-55.01 (-55.0%) | -59.2% | $93.83 | $+38.82 |
| Trend | 0.75% | 939 | 27% | -0.138 | $-0.080 | 0.66 | $-75.27 (-75.3%) | -76.4% | $103.79 | $+28.52 |
| Mean reversion | 0.00% | 781 | 63% | -0.054 | $-0.048 | 0.77 | $-37.67 (-37.7%) | -41.6% | $0.00 | $-37.67 |
| Mean reversion | 0.25% | 790 | 57% | -0.123 | $-0.080 | 0.55 | $-63.38 (-63.4%) | -63.6% | $35.16 | $-28.22 |
| Mean reversion | 0.50% | 795 | 49% | -0.176 | $-0.096 | 0.40 | $-76.31 (-76.3%) | -76.5% | $55.68 | $-20.64 |
| Mean reversion | 0.75% | 798 | 42% | -0.225 | $-0.105 | 0.27 | $-84.08 (-84.1%) | -84.2% | $67.49 | $-16.59 |

## 5. Trend: R by coin and year (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades |
|---|---|---|---|---|---|---|
| ADA | -7.6 | -1.8 | -3.7 | 0.6 | -4.2 | 114 |
| AVAX | -2.4 | 1.1 | -3.5 | -2.9 | -7.8 | 114 |
| BTC | -2.9 | 5.6 | 5.5 | -3.3 | -6.6 | 127 |
| DOGE | 1.8 | -11 | 0.1 | 4.1 | -5.4 | 115 |
| ETH | -0.6 | 0.3 | -1 | 7.3 | -1.9 | 128 |
| LINK | -0 | -3.4 | -3 | -5.1 | -5.2 | 130 |
| SOL | -2.1 | 8.5 | 0.6 | -0 | -3.2 | 125 |
| XRP |  | -1.7 | 0.5 | -5.7 | -5.8 | 77 |

## 5. Mean reversion: R by coin and year (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades |
|---|---|---|---|---|---|---|
| ADA | -2.2 | -0.2 | -2.4 | -2.6 | -3.3 | 80 |
| AVAX | -5.3 | -2.9 | -10.8 | 0.1 | -1.7 | 86 |
| BTC | -5.7 | -6.1 | -8.9 | -7.1 | -4.4 | 132 |
| DOGE | -1.9 | 1.8 | -3.5 | -3.1 | -2.3 | 94 |
| ETH | -3.7 | -3.2 | -9.6 | -3 | -2.1 | 116 |
| LINK | -3.6 | -1.2 | -4.9 | -4.3 | -0.6 | 108 |
| SOL | -2.6 | -1.7 | -8.1 | -4.8 | -5.1 | 114 |
| XRP |  | -0.8 | -5.2 | -3.2 | -0.2 | 65 |

## Verdict against golden rule 2 (draft criteria)

Pass needs, per strategy: >= 100 trades, profit factor >= 1.2 at 0.50% fees, positive expectancy in BOTH halves, and still positive at 0.75% fees.

- **Trend: FAIL** — trades >= 100 ✓, PF >= 1.2 ✗, early half positive ✗, late half positive ✗, positive at 0.75% fees ✗
- **Mean reversion: FAIL** — trades >= 100 ✓, PF >= 1.2 ✗, early half positive ✗, late half positive ✗, positive at 0.75% fees ✗
