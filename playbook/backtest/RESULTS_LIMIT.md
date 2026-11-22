# Limit-order entries vs market entries (chosen strategy, 20 coins, all limits ON)

See `run_limit.py` for the variants and fill rules. Taker fee 0.90% for market buys and all stops, slippage 0.05% on taker fills. Real Intro-tier fees: taker 0.90%, maker 0.50%.

## 1. Whole period, 2022 to now

| Entry | Maker fee | Trades | Limit fill rate | Win % | Profit factor | Return | Max DD | Fees | Kill switch |
|---|---|---|---|---|---|---|---|---|---|
| market | n/a (taker 0.90%) | 356 | n/a | 33% | 1.08 | +7.4% | -19.9% | $28.19 | never |
| limit@close | 0.50% | 357 | 34% | 33% | 1.15 | +14.2% | -19.5% | $23.69 | never |
| limit+fallback | 0.50% | 356 | 34% | 33% | 1.16 | +14.5% | -19.4% | $23.65 | never |
| limit-dip | 0.50% | 343 | 39% | 34% | 1.16 | +16.1% | -21.6% | $25.21 | never |

## 2. Stability at 0.50% maker: before vs after 2024-06-01

| Entry | Period | Trades | Limit fill rate | Win % | Profit factor | Return | Max DD | Fees | Kill switch |
|---|---|---|---|---|---|---|---|---|---|
| market | early | 186 | n/a | 34% | 1.26 | +11.6% | -15.6% | $13.53 | never |
| market | late | 170 | n/a | 31% | 0.94 | -2.6% | -19.9% | $13.30 | never |
| limit@close | early | 187 | 36% | 35% | 1.34 | +14.9% | -14.8% | $11.19 | never |
| limit@close | late | 170 | 32% | 31% | 1.01 | +0.6% | -19.5% | $11.02 | never |
| limit+fallback | early | 186 | 36% | 35% | 1.34 | +15.1% | -15.0% | $11.12 | never |
| limit+fallback | late | 170 | 32% | 31% | 1.01 | +0.6% | -19.4% | $11.02 | never |
| limit-dip | early | 182 | 42% | 36% | 1.38 | +17.7% | -14.0% | $11.95 | never |
| limit-dip | late | 161 | 37% | 31% | 0.99 | -0.4% | -21.1% | $11.38 | never |
