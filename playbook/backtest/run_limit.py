"""Limit-order entries vs market entries for the CHOSEN strategy. Writes RESULTS_LIMIT.md.

Variants fixed BEFORE any results were seen:
  market        buy at next open as taker (current)
  limit@close   post-only limit at the signal close, good for 1 bar, else skip
  limit+fallback  same, but if unfilled buy at the following open as taker
  limit-dip     limit 0.5 x ATR below the signal close, good for 6 bars (1 day), else skip
A limit fills only if a later bar trades strictly BELOW it (touching is not enough:
queue position), at the limit price, with the maker fee and no slippage.
Stops are always taker. Omar's full limits are ON.
"""
from dataclasses import replace
from pathlib import Path

from config import CHOSEN, Costs, EntryParams, Risk
from engine import run, stats
from run import SPLIT, load

OUT = Path(__file__).parent
VARIANTS = {
    "market": EntryParams(),
    "limit@close": EntryParams(mode="limit", offset_atr=0.0, valid_bars=1),
    "limit+fallback": EntryParams(mode="limit", offset_atr=0.0, valid_bars=1, fallback_market=True),
    "limit-dip": EntryParams(mode="limit", offset_atr=0.5, valid_bars=6),
}
MAKER = (0.005,)  # Omar's real maker fee (Intro tier)


def row(name, mk, r):
    s, o = stats(r), r.orders
    fill = f"{o['limit_filled'] / o['limit_placed']:.0%}" if o.get("limit_placed") else "n/a"
    kill = f"{r.kill_time:%Y-%m-%d}" if r.kill_time is not None else "never"
    return (f"| {name} | {mk} | {s['trades']} | {fill} | {s['win_rate']:.0%} | {s['profit_factor']:.2f} | "
            f"{s['return_pct']:+.1%} | {s['max_dd']:.1%} | ${s['fees']:.2f} | {kill} |")


def main():
    data = load()
    L = []
    w = L.append
    w("# Limit-order entries vs market entries (chosen strategy, 20 coins, all limits ON)\n")
    w("See `run_limit.py` for the variants and fill rules. Taker fee 0.90% for market buys and all stops, "
      "slippage 0.05% on taker fills. Real Intro-tier fees: taker 0.90%, maker 0.50%.\n")
    hdr = ("| Entry | Maker fee | Trades | Limit fill rate | Win % | Profit factor | Return | Max DD | Fees | Kill switch |\n"
           "|---|---|---|---|---|---|---|---|---|---|")
    w("## 1. Whole period, 2022 to now\n"); w(hdr)
    base = run(data, tp=CHOSEN, strategies=("trend",))
    w(row("market", "n/a (taker 0.90%)", base))
    for mk in MAKER:
        for name, ep in VARIANTS.items():
            if name == "market":
                continue
            r = run(data, tp=CHOSEN, strategies=("trend",), entry=ep, costs=replace(Costs(), maker_fee=mk))
            w(row(name, f"{mk:.2%}", r))
    w("")
    w(f"## 2. Stability at 0.50% maker: before vs after {SPLIT:%Y-%m-%d}\n")
    w("| Entry | Period | Trades | Limit fill rate | Win % | Profit factor | Return | Max DD | Fees | Kill switch |\n"
      "|---|---|---|---|---|---|---|---|---|---|")
    for name, ep in VARIANTS.items():
        for p, s, e in [("early", None, SPLIT), ("late", SPLIT, None)]:
            r = run(data, tp=CHOSEN, strategies=("trend",), entry=ep, costs=replace(Costs(), maker_fee=0.005),
                    start=s, end=e)
            w(row(name, p, r))
    w("")
    (OUT / "RESULTS_LIMIT.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
