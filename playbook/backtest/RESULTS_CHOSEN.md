# Chosen strategy: trend only, 180-bar breakout (4h bars)

Rules: close > 200-bar EMA and close > prior 180-bar high; stop 5 x ATR(42) below the signal close, trailing at highest high - 7 x ATR; exit only via the resting stop.

Limits: risk 0.5%/trade incl. costs, daily loss limit 3%, kill switch -25% from high, max 8 open trades, 1x, long only. Costs: fee 0.50%/side, slippage 0.05%/side, min order $1. Data 2022-01-01 to now.

Original 8 coins: BTC, ETH, SOL, XRP, DOGE, ADA, LINK, AVAX. Added 12 (unseen when the rules were picked): LTC, BCH, DOT, UNI, AAVE, NEAR, ATOM, XLM, HBAR, SHIB, ETC, FIL.

## 1. Playbook as written: limits ON

| Coins | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| All 20 | 356 | 33% | +0.145 | $+0.066 | 1.25 | $+23.63 (+23.6%) | -19.0% | $18.13 | $+41.76 |
| Original 8 | 217 | 36% | +0.214 | $+0.102 | 1.38 | $+22.18 (+22.2%) | -15.4% | $12.54 | $+34.72 |
| Added 12 | 271 | 32% | +0.105 | $+0.042 | 1.17 | $+11.28 (+11.3%) | -18.5% | $11.67 | $+22.95 |

- All 20: kill switch never hit, daily limit hit on 10 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0, 'max_positions': 694}
- Original 8: kill switch never hit, daily limit hit on 6 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0, 'max_positions': 0}
- Added 12: kill switch never hit, daily limit hit on 7 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0, 'max_positions': 103}

## 2. Limits OFF (whole period)

| Coins | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| All 20 | 355 | 34% | +0.150 | $+0.069 | 1.26 | $+24.62 (+24.6%) | -19.0% | $18.21 | $+42.82 |
| Original 8 | 217 | 36% | +0.214 | $+0.102 | 1.38 | $+22.18 (+22.2%) | -15.4% | $12.54 | $+34.72 |
| Added 12 | 271 | 32% | +0.105 | $+0.042 | 1.17 | $+11.28 (+11.3%) | -18.5% | $11.67 | $+22.95 |

## 3. Stability: before vs after 2024-06-01 (limits off)

| Coins | Period | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|---|
| All 20 | early | 185 | 37% | +0.242 | $+0.117 | 1.51 | $+21.75 (+21.8%) | -13.8% | $8.33 | $+29.88 |
| All 20 | late | 170 | 31% | +0.061 | $+0.021 | 1.08 | $+3.51 (+3.5%) | -19.0% | $8.21 | $+11.72 |
| Added 12 | early | 152 | 30% | +0.046 | $+0.007 | 1.03 | $+1.10 (+1.1%) | -18.5% | $6.11 | $+7.15 |
| Added 12 | late | 119 | 34% | +0.187 | $+0.088 | 1.36 | $+10.49 (+10.5%) | -13.7% | $5.51 | $+16.00 |

## 4. Fee sensitivity, all 20 (limits off)

| Fee/side | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| 0.00% | 355 | 36% | +0.276 | $+0.151 | 1.52 | $+53.77 (+53.8%) | -18.0% | $0.00 | $+53.77 |
| 0.25% | 355 | 35% | +0.209 | $+0.106 | 1.38 | $+37.66 (+37.7%) | -18.4% | $10.09 | $+47.75 |
| 0.50% | 355 | 34% | +0.150 | $+0.069 | 1.26 | $+24.62 (+24.6%) | -19.0% | $18.21 | $+42.82 |
| 0.75% | 355 | 33% | +0.097 | $+0.039 | 1.15 | $+13.87 (+13.9%) | -19.5% | $24.86 | $+38.73 |

## 5. R by coin and year, all 20 (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades | total R |
|---|---|---|---|---|---|---|---|
| SHIB | -1 | -1.9 | 27.3 | -2 | 0.1 | 10 | 22.5 |
| ADA | -0.3 | 12.1 | 5.9 | -1.9 | -2.8 | 19 | 13.1 |
| DOGE | 2.5 | 5.2 | 2.9 | -0.8 | 2.5 | 14 | 12.2 |
| NEAR |  | -0.4 | 1.3 | -0.2 | 8.2 | 13 | 8.8 |
| ETH | 1.1 | 1.3 | 3.3 | 2.6 | -0 | 27 | 8.4 |
| HBAR |  | -1.3 | 8.4 | 1.4 | -1 | 14 | 7.5 |
| SOL | -0.9 | 9.4 | 1.3 | -0.1 | -2.4 | 24 | 7.2 |
| XRP |  | -1.1 | 1.4 | 2.2 | 1.4 | 9 | 3.9 |
| LINK | -1.4 | 3.7 | 4 | -0.7 | -2.8 | 25 | 2.9 |
| UNI | -0.5 | -1.4 | 2.3 | -0.9 | 2 | 21 | 1.4 |
| XLM | -1.1 | -0.2 | -0.2 | 0.5 | 1.7 | 11 | 0.8 |
| BTC | -2.3 | 2.9 | 2.1 | -0.9 | -1.5 | 30 | 0.2 |
| ETC | 3 | -3.2 | -0.1 | 0.1 | -0.5 | 12 | -0.8 |
| AVAX | -2.8 | 1.9 | -2.1 | 1.2 | 0.8 | 18 | -1.1 |
| AAVE | -2 | -0.7 | -2.1 | 2.5 | -1.6 | 23 | -3.9 |
| FIL |  | 1.6 | -2.9 | 0.5 | -4.1 | 12 | -4.8 |
| LTC | -2 | -3.5 | 0 | 0.8 | -0.4 | 23 | -5.1 |
| ATOM | -3.5 | 1.1 | 0.4 | -0.5 | -3.3 | 15 | -5.8 |
| BCH | -0.8 | 2.7 | -6.2 | -3.1 | 0.8 | 23 | -6.6 |
| DOT | -0.9 | -2.8 | -2.4 | -1.3 | -0.2 | 12 | -7.5 |

## Verdict against golden rule 2

>= 100 trades, PF >= 1.2 at 0.50% fees, positive in BOTH halves, positive at 0.75% fees, and the playbook as written (limits ON) must not end in the kill switch.

- **PASS** — trades >= 100 ✓, PF >= 1.2 ✓, early half positive ✓, late half positive ✓, positive at 0.75% fees ✓, kill switch not hit (limits on) ✓, added 12 coins positive (out of sample) ✓
