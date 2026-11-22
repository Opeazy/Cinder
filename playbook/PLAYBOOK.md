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
| Fees | Coinbase fee tier, TBD (default 0.10% per side) |

## Golden rules
- No stop on the exchange, no trade.
- No backtest with full costs, no bot.
- No 30+ matching paper trades, no real money.
- No "go live" from Omar, no live mode.

## Open items
- [ ] Confirm actual Coinbase fee tier. The 0.10%/side default is likely far below
      Coinbase Advanced's entry tier for a small account; backtests must use the real number.
- [ ] Define the coin universe ("top" = by what, how many, how often refreshed).
- [ ] Define trend-following and mean-reversion entry/exit rules and stop placement.
- [ ] Define what counts as a "matching" paper trade (vs. backtest expectation).
