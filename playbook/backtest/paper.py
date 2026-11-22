"""Paper-trading bot. PAPER ONLY: it never sends an order to Coinbase.

Run it once after each 4h bar closes (UTC 00, 04, 08, 12, 16, 20; a few minutes after):
    python paper.py            # process any new completed bars, update ../paper/
    python paper.py --status   # print the book without fetching
    python paper.py --compare  # re-run the backtest over the paper period and compare trades

Uses exactly the same Book.step() as the backtest, the chosen rules in config.py,
and Coinbase's public candles. If runs are missed, it catches up bar by bar.
Stops are simulated as resting exchange stops (filled at the stop, or the open on a gap).
"""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from config import CHOSEN, CHOSEN_ENTRY, UNIVERSE, Costs, MeanRevParams, Risk
from engine import Book, add_indicators, bar_rows
from fetch import fetch_hourly, to_4h

MODE = "PAPER"  # Live trading is NOT implemented. Golden rule: no "go live" from Omar, no live mode.
DIR = Path(__file__).parent.parent / "paper"
STATE = DIR / "state.json"
HISTORY_DAYS = 500  # 200-day EMA (1200 bars) needs ~2.5x its length to settle; 60-day breakout
STRATS = ("trend",)


def make_book():
    return Book(UNIVERSE, Costs(), Risk(), CHOSEN, MeanRevParams(), STRATS, CHOSEN_ENTRY)


def last_complete_boundary(now):
    return now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=now.hour % 4)


def fetch_all(end):
    start = end - timedelta(days=HISTORY_DAYS)
    data, complete = {}, True
    for c in UNIVERSE:
        h = fetch_hourly(f"{c}-USD", start, end)
        complete &= h.index[-1] >= pd.Timestamp(end) - pd.Timedelta(hours=1)
        data[c] = add_indicators(to_4h(h), CHOSEN, MeanRevParams())
    # If any coin's final hour isn't published yet, don't act on the newest bar; next run will.
    usable_end = pd.Timestamp(end) if complete else pd.Timestamp(end) - pd.Timedelta(hours=4)
    return data, usable_end


def save(book, meta):
    DIR.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({"meta": meta, "book": book.to_dict()}, indent=1))
    pd.DataFrame(book.trades).to_csv(DIR / "trades.csv", index=False)
    (DIR / "journal.log").write_text("\n".join(book.events) + "\n")


def load():
    s = json.loads(STATE.read_text())
    return make_book().load_dict(s["book"]), s["meta"]


def status(book, meta):
    eq = book.equity[-1][1] if book.equity else book.cash
    lines = [f"MODE {MODE} | started {meta['started']} | last bar {book.last_bar} | equity ${eq:.2f} "
             f"(high ${book.eq_high:.2f}) | cash ${book.cash:.2f}",
             f"closed trades {len(book.trades)} | kill switch {'HIT ' + book.killed_at if book.killed_at else 'ok'} | "
             f"daily limit {'BLOCKED today' if book.day_blocked else 'ok'}"]
    for c, p in book.pos.items():
        lines.append(f"  OPEN {c}: qty {p.qty:.8g} @ {p.entry:.6g}, resting stop {p.stop:.6g}, risk ${p.risk_usd:.2f}, "
                     f"since {p.entry_time}")
    for c, strat, stop in book.pending_entries:
        lines.append(f"  NEXT OPEN: market buy {c} ({strat}), stop {stop:.6g}")
    for c, strat, stop, limit, left in book.working:
        lines.append(f"  RESTING LIMIT BUY {c} @ {limit:.6g} ({left} bar(s) left), stop {stop:.6g}")
    return "\n".join(lines)


def main():
    if MODE != "PAPER":
        raise SystemExit("Live mode is not implemented and needs Omar's 'go live'.")
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--compare", action="store_true")
    args = ap.parse_args()

    if args.status:
        print(status(*load()))
        return

    end = last_complete_boundary(datetime.now(timezone.utc))
    data, usable_end = fetch_all(end)

    if STATE.exists():
        book, meta = load()
    else:
        # Start fresh at the newest completed bar: no replay of history.
        book, meta = make_book(), {"started": None}
        latest = usable_end - pd.Timedelta(hours=4)
        meta["started"] = latest.isoformat()
        book.last_bar = (latest - pd.Timedelta(hours=4)).isoformat()

    if args.compare:
        start = pd.Timestamp(meta["started"])
        bt = to_result_from(data, start, usable_end)
        compare(book, bt)
        return

    n_before = len(book.events)
    new = 0
    for t, bars in bar_rows(data, start=pd.Timestamp(book.last_bar) + pd.Timedelta(hours=4), end=usable_end):
        book.step(t, bars)
        new += 1
    save(book, meta)
    print(f"processed {new} new bar(s)")
    for e in book.events[n_before:]:
        print("  " + e)
    print(status(book, meta))


def to_result_from(data, start, end):
    book = make_book()
    for t, bars in bar_rows(data, start=start, end=end):
        book.step(t, bars)
    return book


def compare(paper, bt):
    """A paper trade 'matches' when the backtest has the same coin, entry bar and exit bar,
    with entry and exit prices within 0.5%."""
    def key(t):
        return (t["coin"], t["entry_time"], t["exit_time"])
    b = {key(t): t for t in bt.trades}
    matched = 0
    for t in paper.trades:
        o = b.get(key(t))
        ok = o is not None and abs(o["entry"] / t["entry"] - 1) < 0.005 and abs(o["exit"] / t["exit"] - 1) < 0.005
        matched += ok
        print(f"{'MATCH' if ok else 'MISMATCH'} {t['coin']} {t['entry_time']} -> {t['exit_time']} R={t['R']:+.2f}")
    extra = set(b) - {key(t) for t in paper.trades}
    for k in sorted(extra):
        print(f"BACKTEST ONLY {k}")
    print(f"\n{matched}/{len(paper.trades)} paper trades match the backtest; {len(extra)} backtest-only trades. "
          f"Golden rule 3 needs 30+ matching.")


if __name__ == "__main__":
    main()
