# Chosen strategy: trend only, 180-bar breakout (4h bars)

Rules: close > 200-bar EMA and close > prior 180-bar high; stop 5 x ATR(42) below the signal close, trailing at highest high - 7 x ATR; exit only via the resting stop.

Limits: risk 0.5%/trade incl. costs, daily loss limit 3%, kill switch -25% from high, 1x, long only. Costs: fee 0.50%/side, slippage 0.05%/side, min order $1. Data 2022-01-01 to now.

Original 8 coins: BTC, ETH, SOL, XRP, DOGE, ADA, LINK, AVAX. Added 12 (unseen when the rules were picked): LTC, BCH, DOT, UNI, AAVE, NEAR, ATOM, XLM, HBAR, SHIB, ETC, FIL.

## 1. Playbook as written: limits ON

| Coins | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| All 20 | 302 | 31% | +0.073 | $+0.016 | 1.06 | $+4.74 (+4.7%) | -27.8% | $13.78 | $+18.51 |
| Original 8 | 217 | 36% | +0.214 | $+0.102 | 1.38 | $+22.18 (+22.2%) | -15.4% | $12.54 | $+34.72 |
| Added 12 | 299 | 32% | +0.092 | $+0.032 | 1.13 | $+9.70 (+9.7%) | -20.1% | $13.04 | $+22.74 |

- All 20: kill switch hit 2024-09-30, daily limit hit on 23 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0}
- Original 8: kill switch never hit, daily limit hit on 6 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0}
- Added 12: kill switch never hit, daily limit hit on 10 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0}

## 2. Limits OFF (whole period)

| Coins | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| All 20 | 512 | 34% | +0.151 | $+0.063 | 1.22 | $+32.21 (+32.2%) | -30.0% | $26.89 | $+59.10 |
| Original 8 | 217 | 36% | +0.214 | $+0.102 | 1.38 | $+22.18 (+22.2%) | -15.4% | $12.54 | $+34.72 |
| Added 12 | 299 | 32% | +0.092 | $+0.032 | 1.13 | $+9.70 (+9.7%) | -20.1% | $13.04 | $+22.74 |

## 3. Stability: before vs after 2024-06-01 (limits off)

| Coins | Period | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|---|
| All 20 | early | 268 | 35% | +0.173 | $+0.070 | 1.28 | $+18.89 (+18.9%) | -22.2% | $12.05 | $+30.74 |
| All 20 | late | 244 | 34% | +0.136 | $+0.051 | 1.19 | $+12.54 (+12.5%) | -26.0% | $12.64 | $+25.18 |
| Added 12 | early | 161 | 32% | +0.055 | $+0.011 | 1.04 | $+1.82 (+1.8%) | -19.3% | $6.55 | $+8.32 |
| Added 12 | late | 138 | 33% | +0.138 | $+0.059 | 1.23 | $+8.15 (+8.1%) | -16.5% | $6.40 | $+14.54 |

## 4. Fee sensitivity, all 20 (limits off)

| Fee/side | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| 0.00% | 509 | 36% | +0.276 | $+0.148 | 1.47 | $+75.38 (+75.4%) | -29.3% | $0.00 | $+75.38 |
| 0.25% | 510 | 35% | +0.212 | $+0.101 | 1.34 | $+51.26 (+51.3%) | -29.6% | $15.07 | $+66.32 |
| 0.50% | 512 | 34% | +0.151 | $+0.063 | 1.22 | $+32.21 (+32.2%) | -30.0% | $26.89 | $+59.10 |
| 0.75% | 513 | 33% | +0.096 | $+0.031 | 1.12 | $+15.96 (+16.0%) | -30.2% | $36.13 | $+52.09 |

## 5. R by coin and year, all 20 (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades | total R |
|---|---|---|---|---|---|---|---|
| SHIB | -1.9 | -0.1 | 28.4 | -3.3 | -0.9 | 21 | 22.2 |
| DOGE | 1.6 | 3.4 | 10.1 | -1.4 | 1.8 | 23 | 15.4 |
| NEAR |  | 0.3 | 0.8 | -0.6 | 11 | 21 | 11.4 |
| XLM | -0.9 | -3.1 | 12.9 | -0.1 | 1.3 | 23 | 10.2 |
| ADA | -2.1 | 12.1 | 5.9 | -2.8 | -3.2 | 24 | 10 |
| HBAR |  | 0.7 | 7.7 | 0.6 | -0.1 | 21 | 8.8 |
| XRP |  | -0.4 | 7 | 1.7 | -0.5 | 17 | 7.8 |
| ETH | 1.1 | -0.7 | 3.3 | 2.6 | -0 | 29 | 6.4 |
| SOL | -2.1 | 10.9 | -0 | -0.1 | -3 | 31 | 5.6 |
| ETC | 3 | -4.5 | 4.1 | 1.5 | 0.2 | 21 | 4.3 |
| AVAX | -3.7 | 7.3 | -1.9 | 0.9 | -0.2 | 26 | 2.4 |
| UNI | -1.1 | -2.2 | 3.7 | -0.4 | 1.8 | 29 | 1.8 |
| BTC | -3.3 | 5.7 | 0.2 | -0.9 | -1.5 | 34 | 0.3 |
| BCH | -0.3 | 2.8 | 0.6 | -3.1 | 0.1 | 27 | 0.1 |
| LINK | -2 | 4 | 0.1 | -0.4 | -3.1 | 33 | -1.4 |
| AAVE | -0.5 | -3.2 | -1 | 0.5 | 1.2 | 29 | -3 |
| FIL | 0.9 | 0.8 | 0.6 | -0.8 | -5.1 | 25 | -3.6 |
| DOT | -0.9 | -1.5 | -1.2 | -0.9 | -2.1 | 26 | -6.7 |
| ATOM | -4.5 | -1.5 | 3.1 | -1 | -3.3 | 23 | -7.2 |
| LTC | -3 | -5.2 | 0.4 | 0.8 | -0.4 | 29 | -7.4 |

## Verdict against golden rule 2

>= 100 trades, PF >= 1.2 at 0.50% fees, positive in BOTH halves, positive at 0.75% fees, and the playbook as written (limits ON) must not end in the kill switch.

- **FAIL** — trades >= 100 ✓, PF >= 1.2 ✓, early half positive ✓, late half positive ✓, positive at 0.75% fees ✓, kill switch not hit (limits on) ✗, added 12 coins positive (out of sample) ✓

## Fix options for the kill switch (20 coins, limits ON)

With 20 coins, many correlated positions are open at once, so drawdowns are deeper (-30% with limits off).
Two standard fixes, tested once each (more data mining on the same history, so treat with care):

| Risk/trade | Max open positions | Trades | Return | Max DD | Kill switch (-25%) |
|---|---|---|---|---|---|
| 0.5% | no cap | 302 | +4.7% | -27.8% | hit 2024-09-30 |
| 0.5% | 10 (5% max open risk) | 408 | +33.1% | -22.4% | never |
| 0.5% | 8 (4% max open risk) | 356 | +23.6% | -19.0% | never |
| 0.5% | 6 (3% max open risk) | 300 | +3.1% | -16.4% | never |
| 0.4% | no cap | 313 | +1.4% | -25.8% | hit 2024-11-06 |
| 0.3% | no cap | 516 | +19.6% | -19.9% | never |

Results jump around between neighboring settings (e.g. 6 vs 8 positions), so the exact numbers are
noisy. When the cap is full, new signals are skipped in list order (original 8 coins first).
