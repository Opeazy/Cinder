"""Slower trend-only variants, 4h bars. Writes RESULTS_SLOW.md. Usage: python run_slow.py

The three variants were fixed BEFORE looking at any results (no tuning):
  slow    breakout 55 bars (~9 days),  ATR 14, initial stop 3 ATR, trail 4 ATR
  slower  breakout 120 bars (~20 days), ATR 42, initial stop 4 ATR, trail 5 ATR
  slowest breakout 180 bars (~30 days), ATR 42, initial stop 5 ATR, trail 7 ATR
All keep: close > 200-bar EMA filter, exit only via the resting stop, full costs.
"""
import json
from dataclasses import replace
from pathlib import Path

from config import Costs, Risk, TrendParams
from engine import run, stats
from run import HDR, MIN_PF, MIN_TRADES, SPLIT, fmt, load, md_table

OUT = Path(__file__).parent
VARIANTS = {
    "draft (20)": TrendParams(),
    "slow (55)": TrendParams(breakout=55, atr=14, init_stop_atr=3.0, trail_atr=4.0),
    "slower (120)": TrendParams(breakout=120, atr=42, init_stop_atr=4.0, trail_atr=5.0),
    "slowest (180)": TrendParams(breakout=180, atr=42, init_stop_atr=5.0, trail_atr=7.0),
}
H1, H2 = HDR.split("\n")


def main():
    data = load()
    no_kill = replace(Risk(), kill_switch=1.0, daily_loss_limit=1.0)
    L = []
    w = L.append
    w("# Slower trend-only variants (4h bars, full costs)\n")
    w("Variants fixed before any results were seen; see `run_slow.py`. Same data, costs and sizing as RESULTS.md. "
      "The 'draft (20)' row repeats the original trend rules for comparison.\n")

    w("## 1. Playbook limits ON (daily limit, -15% kill switch)\n")
    w("| Variant | " + H1[2:]); w("|---" + H2)
    on = {}
    for name, tp in VARIANTS.items():
        r = run(data, tp=tp, strategies=("trend",))
        on[name] = r
        w(f"| {name} " + fmt(stats(r)))
    w("")
    for name, r in on.items():
        w(f"- {name}: kill switch {'hit ' + f'{r.kill_time:%Y-%m-%d}' if r.kill_time is not None else 'never hit'}, "
          f"daily limit hit on {r.blocked_days} days, skipped entries {r.skipped}")
    w("")

    w("## 2. Limits OFF (whole period)\n")
    w("| Variant | " + H1[2:]); w("|---" + H2)
    full = {}
    for name, tp in VARIANTS.items():
        full[name] = run(data, tp=tp, strategies=("trend",), risk=no_kill)
        w(f"| {name} " + fmt(stats(full[name])))
    w("")

    w(f"## 3. Stability: before vs after {SPLIT:%Y-%m-%d} (limits off)\n")
    w("| Variant | Period | " + H1[2:]); w("|---|---" + H2)
    halves = {}
    for name, tp in VARIANTS.items():
        for label, s, e in [("early", None, SPLIT), ("late", SPLIT, None)]:
            halves[(name, label)] = stats(run(data, tp=tp, strategies=("trend",), risk=no_kill, start=s, end=e))
            w(f"| {name} | {label} " + fmt(halves[(name, label)]))
    w("")

    w("## 4. Fee sensitivity (limits off)\n")
    w("| Variant | Fee/side | " + H1[2:]); w("|---|---" + H2)
    fees = {}
    for name, tp in VARIANTS.items():
        for f in (0.0, 0.0025, 0.005, 0.0075):
            fees[(name, f)] = stats(run(data, tp=tp, strategies=("trend",), risk=no_kill, costs=replace(Costs(), fee=f)))
            w(f"| {name} | {f:.2%} " + fmt(fees[(name, f)]))
    w("")

    for name in VARIANTS:
        tr = full[name].trades
        if tr.empty:
            continue
        tr = tr.assign(year=tr.exit_time.dt.year)
        piv = tr.pivot_table(index="coin", columns="year", values="R", aggfunc="sum").round(1)
        piv["trades"] = tr.groupby("coin").size()
        w(f"## 5. {name}: R by coin and year (limits off)\n")
        w(md_table(piv) + "\n")

    w("## Verdict against golden rule 2 (same draft criteria)\n")
    w(f">= {MIN_TRADES} trades, PF >= {MIN_PF} at 0.50% fees, positive in BOTH halves, positive at 0.75% fees.\n")
    verdict = {}
    for name in VARIANTS:
        s = stats(full[name])
        checks = {
            f"trades >= {MIN_TRADES}": s.get("trades", 0) >= MIN_TRADES,
            f"PF >= {MIN_PF}": s.get("profit_factor", 0) >= MIN_PF,
            "early half positive": halves[(name, "early")].get("expectancy_usd", -1) > 0,
            "late half positive": halves[(name, "late")].get("expectancy_usd", -1) > 0,
            "positive at 0.75% fees": fees[(name, 0.0075)].get("expectancy_usd", -1) > 0,
        }
        verdict[name] = all(checks.values())
        w(f"- **{name}: {'PASS' if verdict[name] else 'FAIL'}** — "
          + ", ".join(f"{k} {'✓' if v else '✗'}" for k, v in checks.items()))
    w("")
    (OUT / "RESULTS_SLOW.md").write_text("\n".join(L))
    json.dump(verdict, open(OUT / "verdict_slow.json", "w"))
    print("\n".join(L))


if __name__ == "__main__":
    main()
