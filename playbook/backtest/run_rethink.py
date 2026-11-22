"""Rethink at real fees (taker 0.90%, maker 0.50%): very slow trend systems. Writes RESULTS_RETHINK.md.

Why: fees are charged on notional, but sizing is by risk (stop distance). With a stop X% away,
a round trip costs about (maker + taker) / X of 1R. Wider stops -> fees shrink relative to risk.

Variants fixed BEFORE any results were seen (4h bars; 6 bars = 1 day):
  current 180   the strategy that failed at real fees (for reference)
  A 60-day      close > 200-day EMA (1200 bars) and > prior 60-day high (360 bars);
                stop 6 x ATR(42) below, trail 9 x ATR
  B 90-day      close > 200-day EMA and > prior 90-day high (540 bars); stop 8 x ATR, trail 12 x ATR
All: limit buy at the signal close with market fallback, 0.5% risk, max 8 open, daily limit, -25% kill switch.
Note: the 200-day EMA needs ~200 days of warm-up, so trading starts mid-2022.
"""
from dataclasses import replace
from pathlib import Path

from config import CHOSEN, ADDED, ORIGINAL, Costs, EntryParams, Risk, TrendParams
from engine import run, stats
from run import HDR, MIN_PF, MIN_TRADES, SPLIT, fmt, load, md_table

OUT = Path(__file__).parent
ENTRY = EntryParams(mode="limit", offset_atr=0.0, valid_bars=1, fallback_market=True)
VARIANTS = {
    "current 180": CHOSEN,
    "A 60-day": TrendParams(regime_ema=1200, breakout=360, atr=42, init_stop_atr=6.0, trail_atr=9.0),
    "B 90-day": TrendParams(regime_ema=1200, breakout=540, atr=42, init_stop_atr=8.0, trail_atr=12.0),
}
H1, H2 = HDR.split("\n")


def go(data, tp, **kw):
    return run(data, tp=tp, strategies=("trend",), entry=ENTRY, **kw)


def main():
    data = load()
    sub = lambda coins: {c: data[c] for c in coins if c in data}
    off = replace(Risk(), kill_switch=1.0, daily_loss_limit=1.0)
    c0 = Costs()
    L = []
    w = L.append
    w("# Rethink: very slow trend systems at real fees\n")
    w(f"Fees: taker {c0.fee:.2%} (stops, fallback buys), maker {c0.maker_fee:.2%} (limit buys), slippage "
      f"{c0.slippage:.2%} on taker fills. 20 coins, 0.5% risk, max 8 open. Variants fixed in advance: see run_rethink.py.\n")

    w("## 1. Playbook as written: limits ON\n")
    w("| Variant | " + H1[2:]); w("|---" + H2)
    on = {}
    for name, tp in VARIANTS.items():
        on[name] = go(data, tp)
        w(f"| {name} " + fmt(stats(on[name])))
    w("")
    for name, r in on.items():
        s = stats(r)
        w(f"- {name}: kill switch {'hit ' + f'{r.kill_time:%Y-%m-%d}' if r.kill_time is not None else 'never hit'}, "
          f"daily limit {r.blocked_days} days, avg position ${r.trades.notional.mean():.2f}, "
          f"avg hold {r.trades.bars.mean() / 6:.0f} days, orders {r.orders}")
    w("")

    w("## 2. Limits OFF: all coins, original 8, added 12\n")
    w("| Variant | Coins | " + H1[2:]); w("|---|---" + H2)
    full = {}
    for name, tp in VARIANTS.items():
        for label, coins in [("all 20", ORIGINAL + ADDED), ("original 8", ORIGINAL), ("added 12", ADDED)]:
            full[(name, label)] = stats(go(sub(coins), tp, risk=off))
            w(f"| {name} | {label} " + fmt(full[(name, label)]))
    w("")

    w(f"## 3. Stability: before vs after {SPLIT:%Y-%m-%d} (limits off, all 20)\n")
    w("| Variant | Period | " + H1[2:]); w("|---|---" + H2)
    halves = {}
    for name, tp in VARIANTS.items():
        for p, s, e in [("early", None, SPLIT), ("late", SPLIT, None)]:
            halves[(name, p)] = stats(go(data, tp, risk=off, start=s, end=e))
            w(f"| {name} | {p} " + fmt(halves[(name, p)]))
    w("")

    w("## 4. Fee stress: taker 1.20%, maker 0.60% (limits off, all 20)\n")
    w("| Variant | " + H1[2:]); w("|---" + H2)
    stress = {}
    for name, tp in VARIANTS.items():
        stress[name] = stats(go(data, tp, risk=off, costs=replace(c0, fee=0.012, maker_fee=0.006)))
        w(f"| {name} " + fmt(stress[name]))
    w("")

    for name, tp in VARIANTS.items():
        tr = go(data, tp, risk=off).trades
        if tr.empty:
            continue
        tr = tr.assign(year=tr.exit_time.dt.year)
        piv = tr.pivot_table(index="coin", columns="year", values="R", aggfunc="sum").round(1)
        piv["trades"] = tr.groupby("coin").size()
        piv["total R"] = tr.groupby("coin").R.sum().round(1)
        w(f"## 5. {name}: R by coin and year (limits off)\n")
        w(md_table(piv.sort_values("total R", ascending=False)) + "\n")

    w("## Verdict against golden rule 2 (real fees)\n")
    w(f">= {MIN_TRADES} trades, PF >= {MIN_PF}, positive in BOTH halves, positive under fee stress, "
      "kill switch not hit with limits on, added 12 coins positive.\n")
    for name in VARIANTS:
        s = full[(name, "all 20")]
        checks = {
            f"trades >= {MIN_TRADES}": s.get("trades", 0) >= MIN_TRADES,
            f"PF >= {MIN_PF}": s.get("profit_factor", 0) >= MIN_PF,
            "early positive": halves[(name, "early")].get("expectancy_usd", -1) > 0,
            "late positive": halves[(name, "late")].get("expectancy_usd", -1) > 0,
            "fee stress positive": stress[name].get("expectancy_usd", -1) > 0,
            "kill switch not hit": on[name].kill_time is None,
            "added 12 positive": full[(name, "added 12")].get("expectancy_usd", -1) > 0,
        }
        ok = all(checks.values())
        w(f"- **{name}: {'PASS' if ok else 'FAIL'}** — " + ", ".join(f"{k} {'✓' if v else '✗'}" for k, v in checks.items()))
    w("")
    (OUT / "RESULTS_RETHINK.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
