# Rethink: very slow trend systems at real fees

Fees: taker 0.90% (stops, fallback buys), maker 0.50% (limit buys), slippage 0.05% on taker fills. 20 coins, 0.5% risk, max 8 open. Variants fixed in advance: see run_rethink.py.

## 1. Playbook as written: limits ON

| Variant | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| current 180 | 356 | 33% | +0.100 | $+0.041 | 1.16 | $+14.49 (+14.5%) | -19.4% | $23.65 | $+38.14 |
| A 60-day | 168 | 33% | +0.230 | $+0.105 | 1.37 | $+17.68 (+17.7%) | -16.3% | $9.66 | $+27.34 |
| B 90-day | 109 | 32% | +0.219 | $+0.099 | 1.38 | $+10.77 (+10.8%) | -15.6% | $4.75 | $+15.52 |

- current 180: kill switch never hit, daily limit 10 days, avg position $4.66, avg hold 12 days, orders {'limit_placed': 1046, 'limit_filled': 351, 'limit_expired': 12, 'fallback_market': 12}
- A 60-day: kill switch never hit, daily limit 4 days, avg position $3.99, avg hold 19 days, orders {'limit_placed': 534, 'limit_filled': 166, 'limit_expired': 3, 'fallback_market': 3}
- B 90-day: kill switch never hit, daily limit 4 days, avg position $3.02, avg hold 32 days, orders {'limit_placed': 452, 'limit_filled': 108, 'limit_expired': 3, 'fallback_market': 3}

## 2. Limits OFF: all coins, original 8, added 12

| Variant | Coins | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|---|
| current 180 | all 20 | 355 | 34% | +0.105 | $+0.043 | 1.17 | $+15.40 (+15.4%) | -19.4% | $23.75 | $+39.15 |
| current 180 | original 8 | 217 | 36% | +0.162 | $+0.073 | 1.27 | $+15.86 (+15.9%) | -15.6% | $16.52 | $+32.38 |
| current 180 | added 12 | 271 | 31% | +0.068 | $+0.022 | 1.09 | $+6.03 (+6.0%) | -19.5% | $15.56 | $+21.59 |
| A 60-day | all 20 | 168 | 33% | +0.232 | $+0.107 | 1.37 | $+17.91 (+17.9%) | -16.3% | $9.67 | $+27.59 |
| A 60-day | original 8 | 93 | 39% | +0.666 | $+0.340 | 2.10 | $+31.66 (+31.7%) | -14.0% | $6.90 | $+38.56 |
| A 60-day | added 12 | 129 | 28% | +0.137 | $+0.052 | 1.18 | $+6.76 (+6.8%) | -15.8% | $6.08 | $+12.84 |
| B 90-day | all 20 | 109 | 32% | +0.222 | $+0.100 | 1.39 | $+10.93 (+10.9%) | -15.6% | $4.75 | $+15.68 |
| B 90-day | original 8 | 66 | 39% | +0.617 | $+0.313 | 2.24 | $+20.67 (+20.7%) | -13.2% | $3.52 | $+24.18 |
| B 90-day | added 12 | 83 | 33% | +0.230 | $+0.103 | 1.44 | $+8.58 (+8.6%) | -15.4% | $3.09 | $+11.67 |

## 3. Stability: before vs after 2024-06-01 (limits off, all 20)

| Variant | Period | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|---|
| current 180 | early | 185 | 36% | +0.186 | $+0.085 | 1.37 | $+15.98 (+16.0%) | -15.0% | $11.12 | $+26.80 |
| current 180 | late | 170 | 31% | +0.026 | $+0.004 | 1.01 | $+0.63 (+0.6%) | -19.4% | $11.02 | $+11.65 |
| A 60-day | early | 85 | 29% | +0.245 | $+0.105 | 1.40 | $+9.03 (+9.0%) | -10.0% | $4.42 | $+13.38 |
| A 60-day | late | 83 | 36% | +0.226 | $+0.103 | 1.36 | $+8.52 (+8.5%) | -16.3% | $4.84 | $+13.36 |
| B 90-day | early | 52 | 29% | +0.321 | $+0.145 | 1.62 | $+7.55 (+7.5%) | -9.4% | $2.06 | $+9.61 |
| B 90-day | late | 57 | 35% | +0.131 | $+0.055 | 1.22 | $+3.14 (+3.1%) | -15.6% | $2.50 | $+5.64 |

## 4. Fee stress: taker 1.20%, maker 0.60% (limits off, all 20)

| Variant | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| current 180 | 355 | 33% | +0.064 | $+0.022 | 1.09 | $+7.80 (+7.8%) | -20.1% | $28.48 | $+36.28 |
| A 60-day | 168 | 32% | +0.195 | $+0.086 | 1.30 | $+14.45 (+14.4%) | -16.6% | $11.91 | $+26.36 |
| B 90-day | 109 | 32% | +0.192 | $+0.085 | 1.33 | $+9.25 (+9.2%) | -15.8% | $5.94 | $+15.18 |

## 5. current 180: R by coin and year (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades | total R |
|---|---|---|---|---|---|---|---|
| SHIB | -1 | -1.9 | 25.9 | -2 | -0 | 10 | 21 |
| ADA | -0.3 | 11.3 | 5.6 | -1.9 | -2.8 | 19 | 11.9 |
| DOGE | 1.2 | 4.8 | 2.7 | -0.9 | 2.3 | 14 | 10.1 |
| NEAR |  | -0.5 | 1.1 | -0.3 | 7.9 | 13 | 8.3 |
| ETH | 1 | 1 | 2.9 | 2.4 | -0.3 | 27 | 7 |
| HBAR |  | -1.5 | 8.1 | 1.3 | -1 | 14 | 6.9 |
| SOL | -1 | 9 | 1.1 | -0.2 | -2.5 | 24 | 6.4 |
| XRP |  | -1.1 | 1.3 | 2 | 1.2 | 9 | 3.5 |
| LINK | -1.5 | 3.3 | 3.8 | -0.7 | -3 | 25 | 1.9 |
| XLM | -1.1 | -0.3 | -0.2 | 0.4 | 1.7 | 11 | 0.4 |
| UNI | -0.5 | -1.5 | 1 | -1 | 1.9 | 21 | -0.2 |
| ETC | 2.8 | -3.2 | -0.2 | 0.1 | -0.6 | 12 | -1.1 |
| BTC | -2.4 | 2.4 | 1.6 | -1.2 | -1.7 | 30 | -1.3 |
| AVAX | -2.9 | 1.7 | -2.1 | 1.1 | 0.6 | 18 | -1.6 |
| AAVE | -2 | -0.9 | -2.2 | 2.4 | -1.6 | 23 | -4.4 |
| FIL |  | 1.5 | -2.9 | 0.5 | -4.1 | 12 | -5 |
| LTC | -2.1 | -3.6 | -0.1 | 0.6 | -0.5 | 23 | -5.7 |
| ATOM | -3.5 | 0.9 | 0.4 | -0.5 | -3.4 | 15 | -6.1 |
| BCH | -0.8 | 2.5 | -6.2 | -3.2 | 0.6 | 23 | -7.2 |
| DOT | -0.9 | -2.8 | -2.4 | -1.3 | -0.2 | 12 | -7.7 |

## 5. A 60-day: R by coin and year (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades | total R |
|---|---|---|---|---|---|---|---|
| SOL |  | -0.3 | 19.9 | -2.8 | 2.4 | 10 | 19.2 |
| DOGE | 2.3 | 1.1 | 12.6 | -1.7 | -1 | 10 | 13.3 |
| NEAR |  |  | 1.3 | -1 | 7.7 | 7 | 8 |
| LINK |  | 3.4 | 2.5 | -0.6 | 1.7 | 10 | 7 |
| BTC |  | 3.3 | 5.1 | -1.6 | -1.3 | 15 | 5.5 |
| ADA |  | 4.1 | 2.1 | -0.9 | -1 | 6 | 4.3 |
| BCH |  | 4.6 | 0.4 | -0.9 | -0.6 | 12 | 3.5 |
| XRP |  |  | 3.7 | -0.3 | -0.1 | 6 | 3.3 |
| ETH |  | -2.3 | 3.5 | 2 | -0.4 | 15 | 2.8 |
| XLM |  | -0.1 |  | 0.4 | -0.4 | 4 | -0.1 |
| ETC | 0.4 | -1.4 | -0.5 |  |  | 4 | -1.6 |
| ATOM |  | 0.1 | -1.9 |  |  | 3 | -1.8 |
| SHIB |  | -0.8 | -0.1 |  | -1 | 4 | -1.9 |
| DOT |  | -1 | -0.7 |  | -1 | 3 | -2.7 |
| FIL |  | 0.2 | -0.2 | -1 | -2 | 5 | -2.9 |
| LTC | -1.8 | -1.4 | 1.2 | -1.9 | 0.8 | 10 | -3 |
| UNI | -1.9 | -2.2 | 0.2 | -2.5 | 3.4 | 16 | -3 |
| AAVE |  | -1.7 | -1.8 | -0.5 | 0.7 | 13 | -3.3 |
| HBAR |  | -1.4 | -3.1 | 0.3 | 0.7 | 8 | -3.5 |
| AVAX |  | -1 | -2 | -1 | 0.1 | 7 | -3.9 |

## 5. B 90-day: R by coin and year (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades | total R |
|---|---|---|---|---|---|---|---|
| SOL |  | -0.6 | 13 | -2.3 | 1.4 | 8 | 11.6 |
| ADA |  | -1.7 | 9.2 |  |  | 4 | 7.5 |
| NEAR |  |  | 5.9 | -1 | 2 | 5 | 6.9 |
| DOGE | -0.1 |  | 7.6 | -1 |  | 4 | 6.5 |
| ETH |  | -1 | 3.3 | 2 | 0.7 | 8 | 5 |
| BTC |  | -0.8 | 4.7 | 1.7 | -1.3 | 11 | 4.4 |
| BCH |  | 3.5 | -0.3 | 0.5 | -0.5 | 7 | 3.2 |
| LINK |  | -2 | 5.4 | -0.7 | 0.4 | 7 | 3.1 |
| AAVE |  | -0.9 | 0.4 | -0 | 1.8 | 9 | 1.3 |
| UNI | -0.9 | -0.9 | 0.8 | -1.1 | 1.4 | 8 | -0.8 |
| DOT |  |  |  |  | -1 | 1 | -1 |
| ATOM |  |  |  | -1 |  | 1 | -1 |
| ETC | -0.6 | -0.2 | -0.7 |  |  | 3 | -1.5 |
| FIL |  | -0.4 | 0.1 | -1 | -0.3 | 4 | -1.6 |
| AVAX |  | -0.9 | -0.5 | -0.3 | -0.2 | 4 | -1.9 |
| HBAR |  | -0.9 | -1.1 | -0.3 |  | 4 | -2.3 |
| XLM |  | -2.4 |  | 0.3 | -0.8 | 5 | -2.8 |
| XRP |  |  | -2 | -0.7 | -0.4 | 5 | -3.1 |
| SHIB |  | -1.7 | -1 |  | -1 | 4 | -3.7 |
| LTC | -1.8 | -0.8 | -1 | -0.8 | -1 | 7 | -5.4 |

## Verdict against golden rule 2 (real fees)

>= 100 trades, PF >= 1.2, positive in BOTH halves, positive under fee stress, kill switch not hit with limits on, added 12 coins positive.

- **current 180: FAIL** — trades >= 100 ✓, PF >= 1.2 ✗, early positive ✓, late positive ✓, fee stress positive ✓, kill switch not hit ✓, added 12 positive ✓
- **A 60-day: PASS** — trades >= 100 ✓, PF >= 1.2 ✓, early positive ✓, late positive ✓, fee stress positive ✓, kill switch not hit ✓, added 12 positive ✓
- **B 90-day: PASS** — trades >= 100 ✓, PF >= 1.2 ✓, early positive ✓, late positive ✓, fee stress positive ✓, kill switch not hit ✓, added 12 positive ✓
