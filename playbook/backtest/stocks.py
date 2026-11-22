"""ETF backtest: strategy A translated to DAILY bars, run on liquid US ETFs.

Usage:
    python stocks.py --fetch   # download daily history from Yahoo Finance -> data/stocks/
    python stocks.py           # backtest -> RESULTS_ETF.md

Fixed BEFORE any results were seen:
  * Universe: SPY QQQ IWM DIA, sector ETFs XLK XLF XLE XLV XLY XLP XLI XLU, GLD, TLT (15).
  * Rules = strategy A on daily bars: close > 200-day EMA and close > prior 60-day high;
    stop 2.5 x ATR(14) below the signal close; trail at highest high - 3.5 x ATR(14).
    (A on 4h used 6 / 9 x a 4h ATR; a daily ATR is ~2.45x a 4h ATR -> ~2.5 / ~3.7.)
  * Market buy at next open (commission-free, so limit orders add nothing).
  * Costs: commission 0 (Coinbase stocks), slippage 0.05% per side for spread + stop slippage,
    min order $1 (fractional shares). Gaps through the stop fill at the open.
  * Same risk rules as the crypto playbook: 0.5% risk, max 8 open, 3% daily limit, -25% kill switch.
  * Data: Yahoo Finance daily bars, adjusted for splits and dividends (total return).
"""
import argparse
import io
import time
import urllib.request
from dataclasses import replace
from pathlib import Path

import pandas as pd

from config import DATA_DIR, Costs, EntryParams, Risk, TrendParams
from engine import run, stats
from run import HDR, MIN_PF, MIN_TRADES, fmt, md_table

ETFS = ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLU", "GLD", "TLT"]
ETFS.insert(4, "EFA")  # developed markets ex-US, for breadth -> 15 total
SDIR = DATA_DIR / "stocks"
OUT = Path(__file__).parent
DAILY_A = TrendParams(regime_ema=200, breakout=60, atr=14, init_stop_atr=2.5, trail_atr=3.5)
ETF_COSTS = Costs(fee=0.0, maker_fee=0.0, slippage=0.0005, min_notional=1.0)
SPLIT = pd.Timestamp("2016-01-01", tz="UTC")


def fetch():
    """Daily bars from Yahoo Finance's chart API, adjusted for splits AND dividends (total return)."""
    import json
    SDIR.mkdir(parents=True, exist_ok=True)
    for t in ETFS:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?period1=946684800&period2={int(time.time())}&interval=1d&events=div,split"
        for i in range(5):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                j = json.loads(urllib.request.urlopen(req, timeout=60).read())
                break
            except Exception as e:
                print(f"  {t}: retry {i + 1} ({e})", flush=True)
                time.sleep(3 * (i + 1))
        else:
            raise SystemExit(f"could not download {t}")
        r = j["chart"]["result"][0]
        q = r["indicators"]["quote"][0]
        df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close", "volume")},
                          index=pd.to_datetime(r["timestamp"], unit="s", utc=True).normalize())
        df["adj"] = r["indicators"]["adjclose"][0]["adjclose"]
        df = df.dropna()
        f = df["adj"] / df["close"]  # back-adjust OHLC so dividends count as return
        for k in ("open", "high", "low", "close"):
            df[k] = df[k] * f
        df = df[~df.index.duplicated(keep="last")].drop(columns="adj")
        df.index.name = "time"
        df.to_csv(SDIR / f"{t}.csv")
        print(f"{t}: {len(df)} days {df.index[0]:%Y-%m-%d} .. {df.index[-1]:%Y-%m-%d}", flush=True)
        time.sleep(1)


def load(start="2005-01-01"):
    data = {}
    for t in ETFS:
        f = SDIR / f"{t}.csv"
        if f.exists():
            d = pd.read_csv(f, index_col=0, parse_dates=True)
            data[t] = d[d.index >= pd.Timestamp(start, tz="UTC")]
    return data


def main():
    data = load()
    on = Risk()
    off = replace(on, kill_switch=1.0, daily_loss_limit=1.0)
    go = lambda **kw: run(data, tp=DAILY_A, strategies=("trend",), costs=kw.pop("costs", ETF_COSTS), **kw)
    first = min(d.index[0] for d in data.values())
    last = max(d.index[-1] for d in data.values())
    L = []
    w = L.append
    w("# ETFs: strategy A on daily bars\n")
    w(f"{len(data)} ETFs ({', '.join(data)}), daily bars {first:%Y-%m-%d} to {last:%Y-%m-%d}. "
      "Rules and costs fixed in advance: see stocks.py. Prices include dividends.\n")

    w("## 1. Playbook as written: limits ON\n")
    w(H := HDR); r_on = go(risk=on); w(fmt(stats(r_on)))
    w(f"\n- Kill switch: {'hit ' + f'{r_on.kill_time:%Y-%m-%d}' if r_on.kill_time is not None else 'never hit'}; "
      f"daily limit hit on {r_on.blocked_days} days; avg position ${r_on.trades.notional.mean():.2f}; "
      f"avg hold {r_on.trades.bars.mean():.0f} trading days\n")
    r_on.trades.to_csv(OUT / "trades_etf.csv", index=False)

    w("## 2. Limits OFF, and stability before vs after 2016\n")
    w("| Period | " + H.split("\n")[0][2:]); w("|---" + H.split("\n")[1])
    full = stats(go(risk=off)); w("| all " + fmt(full))
    early = stats(go(risk=off, end=SPLIT)); w("| before 2016 " + fmt(early))
    late = stats(go(risk=off, start=SPLIT)); w("| 2016 on " + fmt(late))
    w("")

    w("## 3. Cost stress: 0.25% per side (as if wide spreads or a commission)\n")
    w(H); stress = stats(go(risk=off, costs=replace(ETF_COSTS, fee=0.0025, maker_fee=0.0025))); w(fmt(stress)); w("")

    w("## 4. Benchmark: buy and hold, same period (with dividends)\n")
    w("| ETF | Return | Max drop |\n|---|---|---|")
    for t in ("SPY", "QQQ", "TLT", "GLD"):
        if t in data:
            s = data[t].close
            w(f"| {t} | {s.iloc[-1] / s.iloc[0] - 1:+.0%} | {(s / s.cummax() - 1).min():.0%} |")
    w("")

    tr = go(risk=off).trades
    tr = tr.assign(year=tr.exit_time.dt.year)
    piv = tr.pivot_table(index="year", columns="coin", values="R", aggfunc="sum").round(1)
    w("## 5. R by year and ETF (limits off)\n")
    w(md_table(piv) + "\n")
    w("| ETF | trades | total R |\n|---|---|---|")
    for c, g in tr.groupby("coin"):
        w(f"| {c} | {len(g)} | {g.R.sum():+.1f} |")
    w("")

    w("## Verdict against golden rule 2\n")
    checks = {
        f"trades >= {MIN_TRADES}": full["trades"] >= MIN_TRADES,
        f"PF >= {MIN_PF}": full["profit_factor"] >= MIN_PF,
        "before 2016 positive": early["expectancy_usd"] > 0,
        "2016 on positive": late["expectancy_usd"] > 0,
        "cost stress positive": stress["expectancy_usd"] > 0,
        "kill switch not hit": r_on.kill_time is None,
    }
    ok = all(checks.values())
    w(f"- **{'PASS' if ok else 'FAIL'}** — " + ", ".join(f"{k} {'✓' if v else '✗'}" for k, v in checks.items()))
    (OUT / "RESULTS_ETF.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    fetch() if a.fetch else main()
