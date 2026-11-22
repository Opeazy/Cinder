# Omar Delacruz: Playbook

## Mandate
Trend following and mean reversion on top Coinbase spot coins, 4-hour candles.
1x only, long only. Never go live without Omar's "go live".

## Parameters

| Item | Value |
|---|---|
| Capital | $100 (paper first) |
| Risk per trade | 1% (~$1) |
| Daily loss limit | 3% (~$3), no new entries until next UTC day |
| Kill switch | -15% from account high (~$15): stop all, keep stops |
| Mode | PAPER until Omar says "go live" |
| Time zone | US Mountain, awake from 8:00 am |
| Exchange | Coinbase (spot, no shorting) |
| Fees | 0.50% per side (Omar's Coinbase tier) |

## Golden rules
- No stop on the exchange, no trade.
- No backtest with full costs, no bot.
- No 30+ matching paper trades, no real money.
- No "go live" from Omar, no live mode.

## Open items
- [x] Fee tier: 0.50% per side.
- [ ] Approve or change the draft universe and entry/exit rules in `backtest/README.md`.
- [ ] Define what counts as a "matching" paper trade (vs. backtest expectation).

## Status
- 2026-11-22: Draft rules backtested on 8 coins, 2022 to 2026, full costs
  (`backtest/RESULTS.md`). **Both strategies FAIL golden rule 2. No bot.**
  Trend has a small edge before fees (PF 1.14 at 0% fees) that 0.50%/side fees wipe out.
  Mean reversion loses even with zero fees.
- 2026-11-22: Slower trend-only, 4h bars, 3 variants fixed in advance (`backtest/RESULTS_SLOW.md`).
  Only the 180-bar breakout passes golden rule 2 (PF 1.31 at 0.50% fees, +41% over 2022 to 2026 with limits off).
  **But its drawdown (~-28%) is deeper than the -15% kill switch**, which stops it even at 0.5% risk.
  Decision needed from Omar before paper trading.
