# Playbook backtest

Portfolio backtest of the draft rules below on Coinbase spot data with full costs.
Implements golden rule 2: "No backtest with full costs, no bot."

```
python fetch.py            # download 1h candles from Coinbase (public API), build 4h bars -> data/
python -m pytest -q        # engine sanity tests on synthetic bars
python run.py              # original draft rules -> RESULTS.md
python run_slow.py         # slower trend variants -> RESULTS_SLOW.md
python run_chosen.py       # CHOSEN strategy, 20 coins, Omar's limits -> RESULTS_CHOSEN.md
python run_limit.py        # limit vs market entries -> RESULTS_LIMIT.md
python run_rethink.py      # very slow trend systems at real fees -> RESULTS_RETHINK.md
python stocks.py --fetch   # ETF daily history from Yahoo Finance
python stocks.py           # strategy A on ETFs, daily bars -> RESULTS_ETF.md
python paper.py            # paper bot: process new 4h bars -> ../paper/
python paper.py --status   # paper book
python paper.py --compare  # paper trades vs backtest over the same period (golden rule 3)
python live.py             # DRY RUN: the exact Coinbase orders a live bot would send -> ../paper/dry_run.json
COINBASE_KEY_FILE=~/cdp_api_key.json python live.py --preview            # Coinbase checks orders, places nothing
COINBASE_KEY_FILE=~/cdp_api_key.json PLAYBOOK_GO_LIVE=yes python live.py --live   # REAL ORDERS
```

**Current strategy:** see `CHOSEN` and `Risk` in `config.py` and `RESULTS_CHOSEN.md`.
The draft rules below are kept for the record.

Requires Python 3.10+, pandas, numpy (pytest for tests). All parameters live in `config.py`.

## Draft rules (for Omar to approve or change)

**Universe:** BTC, ETH, SOL, XRP, DOGE, ADA, LINK, AVAX (USD pairs). Fixed list chosen
XRP-USD data starts 2023-07 (relisted on Coinbase then).
today, so the test has survivorship bias: these are coins that are still large now.

**Timeframe:** 4h bars aligned to UTC (00, 04, 08, 12, 16, 20). Decisions at bar close,
orders at the next bar's open. One position per coin at a time.

**Trend following**
- Filter: close above the 200-bar EMA (~33 days).
- Entry: close above the highest high of the prior 20 bars (~3.3 days).
- Stop: entry signal close - 3 x ATR(14), resting on the exchange.
- Trail: stop ratchets up to (highest high since entry - 3 x ATR). Exit only via the stop.

**Mean reversion**
- Filter: close above the 200-bar EMA (buy dips in an uptrend only).
- Entry: RSI(3) below 15.
- Stop: signal close - 3 x ATR(14), resting on the exchange.
- Exit: market sell at the next open after a close above the 20-bar SMA, or after 18 bars (3 days).
- If a coin triggers both, trend wins.

**Sizing and limits (from the playbook)**
- Size so a stop-out loses 1% of equity *including* both fees and slippage.
- 1x: never spend more than available cash.
- Daily loss limit 3% vs equity at UTC day start: no new entries until the next UTC day.
- Kill switch -15% from equity high: no new entries, no more management, resting stops stay.

**Costs**
- Fee 0.50% per side on every fill, stops included (Omar's tier).
- Slippage 0.05% per side. Stops that gap fill at the bar open.
- Coinbase minimum order $1.

## Known limits of this test
- 4h bars: the engine can't see the order of moves inside a bar. It assumes the stop
  is checked after the open, which is right for gaps but rough for wild bars.
- No partial fills, and the exchange is assumed to be online. Fixed slippage.
- Fixed universe (survivorship bias, see above). Results look better than reality would.
- Parameters are round-number defaults, not tuned. Tuning on this same data would overfit.
