"""Chosen strategy (trend only, 180-bar breakout) on 20 coins with Omar's limits.
Writes RESULTS_CHOSEN.md. Usage: python run_chosen.py

The 12 added coins were never used to pick the rules, so their results are an
out-of-sample check on unseen coins (same period, though).
"""
import json
from dataclasses import replace
from pathlib import Path

from config import ADDED, CHOSEN, ORIGINAL, Costs, Risk
from engine import run, stats
from run import HDR, MIN_PF, MIN_TRADES, SPLIT, fmt, load, md_table

OUT = Path(__file__).parent
H1, H2 = HDR.split("\n")


def main():
    data = load()
    sub = lambda coins: {c: data[c] for c in coins if c in data}
    on = Risk()
    off = replace(on, kill_switch=1.0, daily_loss_limit=1.0)
    L = []
    w = L.append
    c0 = Costs()
    w("# Chosen strategy: trend only, 180-bar breakout (4h bars)\n")
    w(f"Rules: close > 200-bar EMA and close > prior 180-bar high; stop {CHOSEN.init_stop_atr:g} x ATR({CHOSEN.atr}) "
      f"below the signal close, trailing at highest high - {CHOSEN.trail_atr:g} x ATR; exit only via the resting stop.\n")
    w(f"Limits: risk {on.risk_per_trade:.1%}/trade incl. costs, daily loss limit {on.daily_loss_limit:.0%}, "
      f"kill switch -{on.kill_switch:.0%} from high, 1x, long only. Costs: fee {c0.fee:.2%}/side, "
      f"slippage {c0.slippage:.2%}/side, min order ${c0.min_notional:.0f}. Data 2022-01-01 to now.\n")
    w(f"Original 8 coins: {', '.join(ORIGINAL)}. Added 12 (unseen when the rules were picked): {', '.join(ADDED)}.\n")

    w("## 1. Playbook as written: limits ON\n")
    w("| Coins | " + H1[2:]); w("|---" + H2)
    runs = {}
    for label, coins in [("All 20", ORIGINAL + ADDED), ("Original 8", ORIGINAL), ("Added 12", ADDED)]:
        r = run(sub(coins), tp=CHOSEN, strategies=("trend",), risk=on)
        runs[label] = r
        w(f"| {label} " + fmt(stats(r)))
    w("")
    for label, r in runs.items():
        w(f"- {label}: kill switch {'hit ' + f'{r.kill_time:%Y-%m-%d}' if r.kill_time is not None else 'never hit'}, "
          f"daily limit hit on {r.blocked_days} days, skipped entries {r.skipped}")
    w("")
    runs["All 20"].trades.to_csv(OUT / "trades_chosen.csv", index=False)
    runs["All 20"].equity.to_csv(OUT / "equity_chosen.csv", header=["equity"])

    w("## 2. Limits OFF (whole period)\n")
    w("| Coins | " + H1[2:]); w("|---" + H2)
    full = {}
    for label, coins in [("All 20", ORIGINAL + ADDED), ("Original 8", ORIGINAL), ("Added 12", ADDED)]:
        full[label] = run(sub(coins), tp=CHOSEN, strategies=("trend",), risk=off)
        w(f"| {label} " + fmt(stats(full[label])))
    w("")

    w(f"## 3. Stability: before vs after {SPLIT:%Y-%m-%d} (limits off)\n")
    w("| Coins | Period | " + H1[2:]); w("|---|---" + H2)
    halves = {}
    for label, coins in [("All 20", ORIGINAL + ADDED), ("Added 12", ADDED)]:
        for p, s, e in [("early", None, SPLIT), ("late", SPLIT, None)]:
            halves[(label, p)] = stats(run(sub(coins), tp=CHOSEN, strategies=("trend",), risk=off, start=s, end=e))
            w(f"| {label} | {p} " + fmt(halves[(label, p)]))
    w("")

    w("## 4. Fee sensitivity, all 20 (limits off)\n")
    w("| Fee/side | " + H1[2:]); w("|---" + H2)
    fees = {}
    for f in (0.0, 0.0025, 0.005, 0.0075):
        fees[f] = stats(run(data, tp=CHOSEN, strategies=("trend",), risk=off, costs=replace(c0, fee=f)))
        w(f"| {f:.2%} " + fmt(fees[f]))
    w("")

    tr = full["All 20"].trades.assign(year=lambda t: t.exit_time.dt.year)
    piv = tr.pivot_table(index="coin", columns="year", values="R", aggfunc="sum").round(1)
    piv["trades"] = tr.groupby("coin").size()
    piv["total R"] = tr.groupby("coin").R.sum().round(1)
    w("## 5. R by coin and year, all 20 (limits off)\n")
    w(md_table(piv.sort_values("total R", ascending=False)) + "\n")

    w("## Verdict against golden rule 2\n")
    w(f">= {MIN_TRADES} trades, PF >= {MIN_PF} at 0.50% fees, positive in BOTH halves, positive at 0.75% fees, "
      "and the playbook as written (limits ON) must not end in the kill switch.\n")
    s = stats(full["All 20"])
    checks = {
        f"trades >= {MIN_TRADES}": s["trades"] >= MIN_TRADES,
        f"PF >= {MIN_PF}": s["profit_factor"] >= MIN_PF,
        "early half positive": halves[("All 20", "early")]["expectancy_usd"] > 0,
        "late half positive": halves[("All 20", "late")]["expectancy_usd"] > 0,
        "positive at 0.75% fees": fees[0.0075]["expectancy_usd"] > 0,
        "kill switch not hit (limits on)": runs["All 20"].kill_time is None,
        "added 12 coins positive (out of sample)": stats(full["Added 12"])["expectancy_usd"] > 0,
    }
    ok = all(checks.values())
    w(f"- **{'PASS' if ok else 'FAIL'}** — " + ", ".join(f"{k} {'✓' if v else '✗'}" for k, v in checks.items()))
    w("")
    (OUT / "RESULTS_CHOSEN.md").write_text("\n".join(L))
    json.dump({"pass": ok, **checks}, open(OUT / "verdict_chosen.json", "w"), indent=1)
    print("\n".join(L))


if __name__ == "__main__":
    main()
