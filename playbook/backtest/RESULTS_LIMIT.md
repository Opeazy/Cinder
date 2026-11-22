# Limit-order entries vs market entries (chosen strategy, 20 coins, all limits ON)

See `run_limit.py` for the variants and fill rules. Taker fee 0.50% for market buys and all stops, slippage 0.05% on taker fills. Omar's maker fee is not confirmed yet, so three maker rates are shown.

## 1. Whole period, 2022 to now

| Entry | Maker fee | Trades | Limit fill rate | Win % | Profit factor | Return | Max DD | Fees | Kill switch |
|---|---|---|---|---|---|---|---|---|---|
| market | n/a (taker 0.50%) | 356 | n/a | 33% | 1.25 | +23.6% | -19.0% | $18.13 | never |
| limit@close | 0.25% | 357 | 34% | 34% | 1.30 | +29.0% | -18.9% | $14.40 | never |
| limit+fallback | 0.25% | 356 | 34% | 34% | 1.30 | +29.3% | -18.9% | $14.38 | never |
| limit-dip | 0.25% | 343 | 39% | 34% | 1.31 | +31.9% | -21.3% | $15.45 | never |
| limit@close | 0.40% | 357 | 34% | 34% | 1.26 | +25.2% | -19.0% | $16.70 | never |
| limit+fallback | 0.40% | 356 | 34% | 34% | 1.27 | +25.6% | -18.9% | $16.65 | never |
| limit-dip | 0.40% | 343 | 39% | 34% | 1.27 | +27.9% | -21.3% | $17.89 | never |
| limit@close | 0.50% | 357 | 34% | 33% | 1.24 | +22.9% | -19.1% | $18.16 | never |
| limit+fallback | 0.50% | 356 | 34% | 33% | 1.24 | +23.2% | -19.0% | $18.08 | never |
| limit-dip | 0.50% | 343 | 39% | 34% | 1.25 | +25.4% | -21.4% | $19.42 | never |

## 2. Stability at 0.40% maker: before vs after 2024-06-01

| Entry | Period | Trades | Limit fill rate | Win % | Profit factor | Return | Max DD | Fees | Kill switch |
|---|---|---|---|---|---|---|---|---|---|
| market | early | 186 | n/a | 37% | 1.48 | +20.8% | -13.8% | $8.33 | never |
| market | late | 170 | n/a | 31% | 1.08 | +3.5% | -19.0% | $8.21 | never |
| limit@close | early | 187 | 36% | 36% | 1.48 | +21.0% | -13.7% | $7.66 | never |
| limit@close | late | 170 | 32% | 31% | 1.11 | +4.7% | -19.0% | $7.57 | never |
| limit+fallback | early | 186 | 36% | 37% | 1.49 | +21.1% | -13.7% | $7.60 | never |
| limit+fallback | late | 170 | 32% | 31% | 1.11 | +4.8% | -18.9% | $7.56 | never |
| limit-dip | early | 182 | 42% | 36% | 1.51 | +24.2% | -13.4% | $8.21 | never |
| limit-dip | late | 161 | 37% | 31% | 1.09 | +3.9% | -20.6% | $7.86 | never |
## Reading this

- A signal usually lasts several bars (price stays above the 180-bar high), and a new limit is
  placed on each of them. So only ~34% of single orders fill, but almost every signal ends up
  bought, and the trade count barely changes.
- The whole benefit is the fee difference. At a 0.50% maker fee (same as taker), limits make no
  real difference. Stops stay taker, so at most half of the fees can be saved.
- "limit-dip" looks best, but the gap is small and its worst drop is deeper. Treat the gaps between
  the limit variants as noise.
- In a real bot, a post-only order at the last close can be rejected if it would cross the spread;
  the live version would place it at the best bid. The paper bot can measure real fill rates.
