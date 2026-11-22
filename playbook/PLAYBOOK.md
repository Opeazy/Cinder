# Omar Delacruz: Playbook

## Mandate
Trend following on top Coinbase spot coins, 4-hour candles (mean reversion
dropped 2026-11-22: no edge in backtest).
1x only, long only. Never go live without Omar's "go live".

## Parameters

| Item | Value |
|---|---|
| Capital | $100 (paper first) |
| Risk per trade | 0.5% (~$0.50), changed from 1% on 2026-11-22 |
| Max open trades | 8 (max 4% open risk), added 2026-11-22 |
| Daily loss limit | 3% (~$3), no new entries until next UTC day |
| Kill switch | -25% from account high (~$25): stop all, keep stops. Changed from -15% on 2026-11-22 |
| Mode | PAPER until Omar says "go live" |
| Time zone | US Mountain, awake from 8:00 am |
| Exchange | Coinbase (spot, no shorting) |
| Fees | Coinbase Advanced Intro tier: maker 0.50%, taker 0.90% (stops are always taker). Was assumed 0.50% flat until 2026-11-22 |

## Golden rules
- No stop on the exchange, no trade.
- No backtest with full costs, no bot.
- No 30+ matching paper trades, no real money.
- No "go live" from Omar, no live mode.

## Open items
- [x] Fee tier: Intro, maker 0.50% / taker 0.90% (screenshot 2026-11-22).
- [x] Rules: trend only, 180-bar breakout (`backtest/config.py` CHOSEN), 20 coins.
- [x] "Matching" paper trade: same coin, entry bar and exit bar as the backtest over the
      same period, entry and exit prices within 0.5% (`paper.py --compare`).
- [x] Paper bot scheduled: Claude scheduled task "Playbook paper bot (every 4h)", 7 min after each 4h close (UTC).
- [ ] Confirm Coinbase MAKER fee rate (decides whether limit entries are worth it).
- [x] Coinbase One (checked 2026-11-22): $500/month zero-fee trading, spread applies, **Coinbase Advanced
      excluded**. The bot needs Advanced (exchange stop orders), so Coinbase One does not lower bot fees.
- [x] Coinbase Advanced rates: Intro tier, maker 0.50% / taker 0.90%.

## Status
- 2026-11-22: Draft rules backtested on 8 coins, 2022 to 2026, full costs
  (`backtest/RESULTS.md`). **Both strategies FAIL golden rule 2. No bot.**
  Trend has a small edge before fees (PF 1.14 at 0% fees) that 0.50%/side fees wipe out.
  Mean reversion loses even with zero fees.
- 2026-11-22: Slower trend-only, 4h bars, 3 variants fixed in advance (`backtest/RESULTS_SLOW.md`).
  Only the 180-bar breakout passes golden rule 2 (PF 1.31 at 0.50% fees, +41% over 2022 to 2026 with limits off).
  **But its drawdown (~-28%) is deeper than the -15% kill switch**, which stops it even at 0.5% risk.
  Decision needed from Omar before paper trading.
- 2026-11-22: **Omar chose option 1**: trend only (180-bar breakout), 0.5% risk, -25% kill switch.
  Universe widened from 8 to 20 coins.
- 2026-11-22: 20-coin test (`backtest/RESULTS_CHOSEN.md`). The 12 new coins, unseen when rules were picked,
  are also profitable (PF 1.13), so the edge holds out of sample, but weaker than on the original 8.
  With 20 coins the -25% kill switch is hit (correlated positions). A cap of 8 open positions
  (max 4% open risk) keeps max drawdown at about -19%. **Decision needed from Omar.**
- 2026-11-22: **Omar chose max 8 open trades.** 20-coin backtest PASSES golden rule 2:
  356 trades, PF 1.25, +23.6% (2022 to 2026), max DD -19%, kill switch never hit.
- 2026-11-22: Paper bot (`backtest/paper.py`) started at the 16:00 UTC bar. State in `paper/`.
  It uses the same trading code as the backtest and never sends orders.
- 2026-11-22: Limit-order entry test (`backtest/RESULTS_LIMIT.md`). Saves fees only on entries.
  At 0.25% maker: +29% vs +23.6% with market buys; at 0.40%: +25%; at 0.50%: no gain.
  Paper bot still uses market entries until Omar decides.
- 2026-11-22: **Real fees are higher than assumed (taker 0.90%, not 0.50%).** Re-run:
  market entries +7.4% (PF 1.08), limit entries +14.5% (PF 1.16), both ~flat or negative after
  June 2024. **The chosen strategy now FAILS golden rule 2 (no backtest with full costs, no bot).**
  RESULTS.md and RESULTS_SLOW.md were made at the old 0.50% assumption. Decision needed from Omar.
- 2026-11-22: **Rethink at real fees** (`backtest/RESULTS_RETHINK.md`), 2 very slow variants fixed in advance.
  A (60-day breakout, 200-day trend filter, wide stops, limit buys): **PASSES** rule 2. PF 1.37,
  +17.7% with limits on, max DD -16%, both periods positive (PF 1.40 / 1.36), positive at 1.20% taker.
  B (90-day) also passes but with fewer trades and a weaker late period. ~38 trades/year for A.
  Decision needed from Omar: switch the paper bot to A.
- 2026-11-22: **Paper bot switched to strategy A** (60-day breakout, limit buys); restarted at the 16:00 UTC bar.
- 2026-11-22: **ETFs** (`backtest/RESULTS_ETF.md`): strategy A on daily bars, 15 liquid ETFs, 2005 to 2026,
  commission-free (Coinbase stocks), 0.05% slippage. **PASSES** rule 2: 783 trades, PF 1.46, +101%,
  max DD -19.6%, both halves positive (PF 1.50 / 1.44). But at 0.25%/side costs it nearly breaks even,
  and buy-and-hold SPY made +752% (max drop -55%). Not yet verified: Coinbase stock stop orders and API.
- 2026-11-22: Omar checked: **no stop orders for stocks/ETFs on Coinbase.** Golden rule 1 (no stop on the
  exchange, no trade) rules out ETFs on Coinbase. ETF results kept for reference; crypto strategy A continues.
