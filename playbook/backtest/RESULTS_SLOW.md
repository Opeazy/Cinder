# Slower trend-only variants (4h bars, full costs)

Variants fixed before any results were seen; see `run_slow.py`. Same data, costs and sizing as RESULTS.md. The 'draft (20)' row repeats the original trend rules for comparison.

## 1. Playbook limits ON (daily limit, -15% kill switch)

| Variant | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| draft (20) | 89 | 31% | -0.141 | $-0.139 | 0.60 | $-12.34 (-12.3%) | -15.1% | $9.52 | $-2.83 |
| slow (55) | 43 | 21% | -0.255 | $-0.258 | 0.50 | $-11.08 (-11.1%) | -17.6% | $4.33 | $-6.75 |
| slower (120) | 32 | 25% | -0.350 | $-0.341 | 0.27 | $-10.92 (-10.9%) | -15.3% | $2.78 | $-8.14 |
| slowest (180) | 64 | 33% | -0.152 | $-0.163 | 0.65 | $-10.44 (-10.4%) | -16.6% | $6.07 | $-4.37 |

- draft (20): kill switch hit 2022-09-18, daily limit hit on 0 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0}
- slow (55): kill switch hit 2022-07-31, daily limit hit on 0 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0}
- slower (120): kill switch hit 2022-09-25, daily limit hit on 1 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0}
- slowest (180): kill switch hit 2023-10-09, daily limit hit on 10 days, skipped entries {'gap_below_stop': 0, 'below_min_notional': 0, 'no_cash': 0}

## 2. Limits OFF (whole period)

| Variant | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|
| draft (20) | 930 | 29% | -0.071 | $-0.059 | 0.80 | $-55.01 (-55.0%) | -59.2% | $93.83 | $+38.82 |
| slow (55) | 540 | 31% | +0.031 | $-0.014 | 0.97 | $-7.44 (-7.4%) | -40.7% | $75.18 | $+67.74 |
| slower (120) | 354 | 34% | +0.054 | $+0.021 | 1.04 | $+7.40 (+7.4%) | -30.3% | $43.32 | $+50.72 |
| slowest (180) | 216 | 37% | +0.217 | $+0.190 | 1.31 | $+41.08 (+41.1%) | -28.4% | $27.54 | $+68.62 |

## 3. Stability: before vs after 2024-06-01 (limits off)

| Variant | Period | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|---|
| draft (20) | early | 447 | 30% | -0.054 | $-0.059 | 0.81 | $-26.54 (-26.5%) | -37.7% | $49.10 | $+22.56 |
| draft (20) | late | 484 | 28% | -0.088 | $-0.080 | 0.78 | $-38.82 (-38.8%) | -49.1% | $60.90 | $+22.07 |
| slow (55) | early | 259 | 29% | +0.090 | $+0.032 | 1.07 | $+8.25 (+8.3%) | -29.5% | $31.41 | $+39.66 |
| slow (55) | late | 281 | 33% | -0.023 | $-0.052 | 0.89 | $-14.50 (-14.5%) | -40.7% | $40.44 | $+25.94 |
| slower (120) | early | 178 | 35% | +0.068 | $+0.050 | 1.11 | $+9.09 (+9.1%) | -20.4% | $19.70 | $+28.66 |
| slower (120) | late | 176 | 34% | +0.044 | $-0.005 | 0.99 | $-0.83 (-0.8%) | -30.3% | $21.82 | $+20.98 |
| slowest (180) | early | 107 | 40% | +0.349 | $+0.329 | 1.68 | $+35.49 (+35.5%) | -16.7% | $11.31 | $+46.48 |
| slowest (180) | late | 109 | 34% | +0.099 | $+0.053 | 1.10 | $+5.81 (+5.8%) | -28.4% | $12.18 | $+17.99 |

## 4. Fee sensitivity (limits off)

| Variant | Fee/side | Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |
|---|---|---|---|---|---|---|---|---|---|---|
| draft (20) | 0.00% | 887 | 33% | +0.091 | $+0.075 | 1.14 | $+66.76 (+66.8%) | -32.7% | $0.00 | $+66.76 |
| draft (20) | 0.25% | 909 | 32% | +0.002 | $-0.015 | 0.96 | $-13.40 (-13.4%) | -40.2% | $68.89 | $+55.50 |
| draft (20) | 0.50% | 930 | 29% | -0.071 | $-0.059 | 0.80 | $-55.01 (-55.0%) | -59.2% | $93.83 | $+38.82 |
| draft (20) | 0.75% | 939 | 27% | -0.138 | $-0.080 | 0.66 | $-75.27 (-75.3%) | -76.4% | $103.79 | $+28.52 |
| slow (55) | 0.00% | 519 | 34% | +0.207 | $+0.192 | 1.27 | $+99.46 (+99.5%) | -30.1% | $0.00 | $+99.46 |
| slow (55) | 0.25% | 530 | 33% | +0.106 | $+0.071 | 1.12 | $+37.70 (+37.7%) | -33.4% | $49.33 | $+87.03 |
| slow (55) | 0.50% | 540 | 31% | +0.031 | $-0.014 | 0.97 | $-7.44 (-7.4%) | -40.7% | $75.18 | $+67.74 |
| slow (55) | 0.75% | 548 | 28% | -0.055 | $-0.065 | 0.85 | $-35.39 (-35.4%) | -48.6% | $90.24 | $+54.85 |
| slower (120) | 0.00% | 349 | 38% | +0.198 | $+0.207 | 1.35 | $+72.07 (+72.1%) | -24.8% | $0.00 | $+72.07 |
| slower (120) | 0.25% | 350 | 36% | +0.116 | $+0.102 | 1.19 | $+35.56 (+35.6%) | -28.1% | $25.92 | $+61.49 |
| slower (120) | 0.50% | 354 | 34% | +0.054 | $+0.021 | 1.04 | $+7.40 (+7.4%) | -30.3% | $43.32 | $+50.72 |
| slower (120) | 0.75% | 356 | 33% | -0.012 | $-0.034 | 0.92 | $-12.08 (-12.1%) | -32.3% | $55.35 | $+43.27 |
| slowest (180) | 0.00% | 215 | 40% | +0.362 | $+0.392 | 1.56 | $+84.33 (+84.3%) | -27.6% | $0.00 | $+84.33 |
| slowest (180) | 0.25% | 215 | 39% | +0.285 | $+0.283 | 1.44 | $+60.89 (+60.9%) | -28.1% | $15.63 | $+76.52 |
| slowest (180) | 0.50% | 216 | 37% | +0.217 | $+0.190 | 1.31 | $+41.08 (+41.1%) | -28.4% | $27.54 | $+68.62 |
| slowest (180) | 0.75% | 217 | 35% | +0.153 | $+0.118 | 1.20 | $+25.64 (+25.6%) | -28.7% | $37.00 | $+62.63 |

## 5. draft (20): R by coin and year (limits off)

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

## 5. slow (55): R by coin and year (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades |
|---|---|---|---|---|---|---|
| ADA | -3 | -0.6 | 4.1 | -0.3 | -2.4 | 66 |
| AVAX | -6 | 2.6 | -2.7 | -6.2 | -0.8 | 73 |
| BTC | -3.1 | 11 | 3.9 | -3.2 | -4.7 | 76 |
| DOGE | -3.7 | -6.2 | 10.3 | 2.5 | -4.2 | 67 |
| ETH | 0.6 | 5.3 | 11.4 | 4.7 | -2.8 | 67 |
| LINK | -4.4 | 8.7 | -1.8 | -1.4 | -1.2 | 73 |
| SOL | -2.2 | 14.3 | 1.9 | -0.5 | 0.5 | 69 |
| XRP |  | -1.3 | 2.3 | -5.5 | 1 | 49 |

## 5. slower (120): R by coin and year (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades |
|---|---|---|---|---|---|---|
| ADA | -1.9 | 2.2 | 6.8 | -1.5 | -1.8 | 41 |
| AVAX | -4 | 3.5 | -2.9 | 1.6 | -3.5 | 48 |
| BTC | -2.7 | 8.5 | 2.8 | 1.8 | -3.7 | 47 |
| DOGE | 1 | -6.7 | 2.1 | 0.8 | 0.8 | 46 |
| ETH | 0.1 | -0.7 | 3.7 | 4.4 | -1.5 | 46 |
| LINK | -2.7 | -1.5 | -2.3 | 1.9 | -0.6 | 49 |
| SOL | -1.5 | 12.3 | 1.8 | 0.4 | -1.7 | 47 |
| XRP |  | 0.3 | 2.1 | 1.1 | 0.5 | 30 |

## 5. slowest (180): R by coin and year (limits off)

| coin | 2022 | 2023 | 2024 | 2025 | 2026 | trades |
|---|---|---|---|---|---|---|
| ADA | -2.1 | 12.1 | 5.9 | -2.8 | -2.8 | 23 |
| AVAX | -3.7 | 7.3 | -1.9 | 0.9 | -0.2 | 26 |
| BTC | -3.3 | 5.7 | 0.2 | -0.9 | -1.5 | 34 |
| DOGE | 1.6 | 3.4 | 10.1 | -1.4 | 1.8 | 23 |
| ETH | 1.1 | -0.7 | 3.3 | 2.6 | -0 | 29 |
| LINK | -2 | 4 | 0.1 | -0.4 | -3.1 | 33 |
| SOL | -2.1 | 10.9 | -0 | -0.1 | -3 | 31 |
| XRP |  | -0.4 | 7 | 1.7 | -0.5 | 17 |

## Verdict against golden rule 2 (same draft criteria)

>= 100 trades, PF >= 1.2 at 0.50% fees, positive in BOTH halves, positive at 0.75% fees.

- **draft (20): FAIL** — trades >= 100 ✓, PF >= 1.2 ✗, early half positive ✗, late half positive ✗, positive at 0.75% fees ✗
- **slow (55): FAIL** — trades >= 100 ✓, PF >= 1.2 ✗, early half positive ✓, late half positive ✗, positive at 0.75% fees ✗
- **slower (120): FAIL** — trades >= 100 ✓, PF >= 1.2 ✗, early half positive ✓, late half positive ✗, positive at 0.75% fees ✗
- **slowest (180): PASS** — trades >= 100 ✓, PF >= 1.2 ✓, early half positive ✓, late half positive ✓, positive at 0.75% fees ✓
## Conflict with the kill switch

The passing variant (slowest, 180) has a natural max drawdown of about -28% at 1% risk.
That is deeper than the playbook's -15% kill switch, so with the playbook's limits on it gets stopped out:

| Risk per trade | Trades before stop | Return | Max DD | Kill switch hit |
|---|---|---|---|---|
| 1.00% | 64 | -10.4% | -16.6% | 2023-10-09 |
| 0.75% | 121 | +17.1% | -17.6% | 2024-09-30 |
| 0.50% | 199 | +16.9% | -15.3% | 2026-07-31 |

Omar must decide: lower risk per trade, widen the kill switch, or keep looking.
