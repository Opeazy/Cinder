# Chosen strategy: trend only, 180-bar breakout (4h bars)

Rules: close > 200-bar EMA and close > prior 180-bar high; stop 5 x ATR(42) below the signal close, trailing at highest high - 7 x ATR; exit only via the resting stop.

Limits: risk 0.5%/trade incl. costs, daily loss limit 3%, kill switch -25% from high, max 8 open trades, 1x, long only. Costs: fee 0.90%/side, slippage 0.05%/side, min order $1. Data 2022-01-01 to now.

Original 8 coins: BTC, ETH, SOL, XRP, DOGE, ADA, LINK, AVAX. Added 12 (unseen when the rules were picked): LTC, BCH, DOT, UNI, AAVE, NEAR, ATOM, XLM, HBAR, SHIB, ETC, FIL.

## 1. Playbook as written: limits ON

| Coins | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| All 20 | 356 | 33% | +0.062 | $+0.021 | 1.08 | $+7.44 (+7.4%) | -19.9% | $28.19 | $+35.63 |
| Original 8 | 217 | 35% | +0.119 | $+0.050 | 1.19 | $+10.83 (+10.8%) | -16.3% | $19.77 | $+30.60 |
| Added 12 | 271 | 30% | +0.031 | $+0.004 | 1.02 | $+1.12 (+1.1%) | -20.7% | $18.77 | $+19.89 |

- All 20: kill switch never hit, daily limit hit on 9 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0, 'max_positions': 694}
- Original 8: kill switch never hit, daily limit hit on 5 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0, 'max_positions': 0}
- Added 12: kill switch never hit, daily limit hit on 5 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0, 'max_positions': 103}

## 2. Limits OFF (whole period)

| Coins | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| All 20 | 355 | 33% | +0.067 | $+0.023 | 1.09 | $+8.29 (+8.3%) | -19.9% | $28.30 | $+36.59 |
| Original 8 | 217 | 35% | +0.119 | $+0.050 | 1.19 | $+10.83 (+10.8%) | -16.3% | $19.77 | $+30.60 |
| Added 12 | 271 | 30% | +0.031 | $+0.004 | 1.02 | $+1.12 (+1.1%) | -20.7% | $18.77 | $+19.89 |

## 3. Stability: before vs after 2024-06-01 (limits off)

| Coins | Period | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|---|
| All 20 | early | 185 | 35% | +0.151 | $+0.066 | 1.29 | $+12.52 (+12.5%) | -15.6% | $13.52 | $+25.74 |
| All 20 | late | 170 | 31% | -0.014 | $-0.015 | 0.94 | $-2.63 (-2.6%) | -19.9% | $13.30 | $+10.66 |
| Added 12 | early | 152 | 29% | -0.026 | $-0.026 | 0.90 | $-3.91 (-3.9%) | -20.7% | $10.10 | $+6.10 |
| Added 12 | late | 119 | 31% | +0.109 | $+0.047 | 1.19 | $+5.64 (+5.6%) | -14.6% | $9.07 | $+14.71 |

## 4. Fee sensitivity, all 20 (limits off; same fee on every fill)

| Fee/side | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| 0.00% | 355 | 36% | +0.276 | $+0.151 | 1.52 | $+53.77 (+53.8%) | -18.0% | $0.00 | $+53.77 |
| 0.25% | 355 | 35% | +0.209 | $+0.106 | 1.38 | $+37.66 (+37.7%) | -18.4% | $10.09 | $+47.75 |
| 0.50% | 355 | 34% | +0.150 | $+0.069 | 1.26 | $+24.62 (+24.6%) | -19.0% | $18.21 | $+42.82 |
| 0.75% | 355 | 33% | +0.097 | $+0.039 | 1.15 | $+13.87 (+13.9%) | -19.5% | $24.86 | $+38.73 |
| 0.90% | 355 | 33% | +0.067 | $+0.023 | 1.09 | $+8.29 (+8.3%) | -19.9% | $28.30 | $+36.59 |

## 5. R by coin and year, all 20 (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades | total R |
|---|---|---|---|---|---|---|---|
| SHIB | -1 | -2 | 24.9 | -2 | -0.1 | 10 | 19.8 |
| ADA | -0.3 | 10.3 | 5.3 | -1.9 | -2.8 | 19 | 10.5 |
| DOGE | 2.2 | 4.4 | 2.5 | -0.9 | 2 | 14 | 10.2 |
| NEAR |  | -0.6 | 1 | -0.3 | 7.6 | 13 | 7.7 |
| HBAR |  | -1.6 | 7.8 | 1.2 | -1 | 14 | 6.3 |
| ETH | 0.8 | 0.6 | 2.4 | 2 | -0.5 | 27 | 5.4 |
| SOL | -1 | 8.4 | 0.9 | -0.4 | -2.7 | 24 | 5.3 |
| XRP |  | -1.1 | 1.2 | 1.8 | 1 | 9 | 2.9 |
| LINK | -1.5 | 2.9 | 3.5 | -0.8 | -3.2 | 25 | 0.9 |
| UNI | -0.6 | -1.5 | 1.5 | -1 | 1.7 | 21 | 0.1 |
| XLM | -1.2 | -0.5 | -0.2 | 0.3 | 1.6 | 11 | -0.1 |
| ETC | 2.6 | -3.3 | -0.2 | 0 | -0.6 | 12 | -1.5 |
| AVAX | -2.9 | 1.4 | -2.2 | 0.9 | 0.5 | 18 | -2.2 |
| BTC | -2.5 | 2 | 1.1 | -1.5 | -2 | 30 | -3 |
| AAVE | -2 | -1.1 | -2.4 | 2.3 | -1.7 | 23 | -5 |
| FIL |  | 1.4 | -3 | 0.5 | -4.1 | 12 | -5.2 |
| ATOM | -3.6 | 0.7 | 0.3 | -0.5 | -3.4 | 15 | -6.5 |
| LTC | -2.3 | -3.7 | -0.3 | 0.4 | -0.6 | 23 | -6.5 |
| BCH | -0.9 | 2.3 | -6.3 | -3.3 | 0.5 | 23 | -7.7 |
| DOT | -1 | -2.8 | -2.4 | -1.3 | -0.3 | 12 | -7.8 |

## Verdict against golden rule 2

>= 100 trades, PF >= 1.2 at real fees, positive in BOTH halves, positive at the real 0.90% taker fee, and the playbook as written (limits ON) must not end in the kill switch.

- **FAIL** — trades >= 100 ✓, PF >= 1.2 ✗, early half positive ✓, late half positive ✗, positive at 0.90% taker (real) ✓, kill switch not hit (limits on) ✓, added 12 coins positive (out of sample) ✓
