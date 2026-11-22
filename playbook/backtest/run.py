"""Run the playbook backtest and write RESULTS.md. Usage: python run.py"""
import json
from dataclasses import replace
from pathlib import Path

import pandas as pd

from config import DATA_DIR, UNIVERSE, Costs, Risk
from engine import run, stats

OUT = Path(__file__).parent
SPLIT = pd.Timestamp("2024-06-01", tz="UTC")
WARMUP_NOTE = "First ~200 bars per coin are indicator warm-up (no trades)."

# Draft go/no-go for golden rule 2 ("no backtest with full costs, no bot")
MIN_TRADES = 100
MIN_PF = 1.2


def load():
    data = {}
    for c in UNIVERSE:
        f = DATA_DIR / f"{c}-USD_4h.csv"
        if f.exists():
            data[c] = pd.read_csv(f, index_col=0, parse_dates=True)
    return data


def md_table(df):
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join([df.index.name or ""] + cols) + " |", "|" + "---|" * (len(cols) + 1)]
    for idx, row in df.iterrows():
        out.append("| " + " | ".join([str(idx)] + ["" if pd.isna(v) else f"{v:g}" for v in row]) + " |")
    return "\n".join(out)


def fmt(s):
    if not s.get("trades"):
        return "| 0 | | | | | | | | |"
    return (f"| {s['trades']} | {s['win_rate']:.0%} | {s['avg_R']:+.3f} | ${s['expectancy_usd']:+.3f} | "
            f"{s['profit_factor']:.2f} | ${s['net_pnl']:+.2f} ({s['return_pct']:+.1%}) | {s['max_dd']:.1%} | "
            f"${s['fees']:.2f} | ${s['pnl_before_fees']:+.2f} |")


HDR = ("| Trades | Win % | Avg R | Expectancy/trade | Profit factor | Net P&L | Max DD | Fees paid | P&L before fees |\n"
       "|---|---|---|---|---|---|---|---|---|")


def main():
    data = load()
    first = min(d.index[0] for d in data.values())
    last = max(d.index[-1] for d in data.values())
    no_kill = replace(Risk(), kill_switch=1.0, daily_loss_limit=1.0)
    L = []
    w = L.append
    w("# Backtest results (DRAFT rules)\n")
    w(f"Data: Coinbase spot, {', '.join(f'{c}-USD' for c in data)}; 4h bars built from 1h candles; "
      f"{first:%Y-%m-%d} to {last:%Y-%m-%d} UTC. {WARMUP_NOTE}\n")
    c0 = Costs()
    w(f"Costs: fee {c0.fee:.2%} per side (every fill, incl. stops), slippage {c0.slippage:.2%} per side, "
      f"min order ${c0.min_notional:.0f}. Capital $100, 1% risk/trade incl. costs, 1x, long only.\n")

    # 1. Playbook exactly as written
    base = run(data)
    w("## 1. Playbook as written (both strategies, all risk limits)\n")
    w(HDR); w(fmt(stats(base)) + "\n")
    w(f"- Kill switch (-15% from high): **{'hit on ' + f'{base.kill_time:%Y-%m-%d}' if base.kill_time is not None else 'never hit'}**")
    w(f"- Days with daily loss limit hit: {base.blocked_days}")
    w(f"- Entries skipped: {base.skipped}\n")
    base.trades.to_csv(OUT / "trades.csv", index=False)
    base.equity.to_csv(OUT / "equity.csv", header=["equity"])

    # 2. Edge diagnostics: limits off so the full history is used
    w("## 2. Edge by strategy (kill switch and daily limit OFF, to see the whole period)\n")
    w("| Strategy | " + HDR.split("\n")[0][2:]); w("|---" + HDR.split("\n")[1])
    diag = {}
    for name, strats in [("Trend", ("trend",)), ("Mean reversion", ("meanrev",)), ("Both", ("trend", "meanrev"))]:
        r = run(data, risk=no_kill, strategies=strats)
        diag[name] = r
        w(f"| {name} " + fmt(stats(r)))
    w("")

    # 3. Out-of-sample style split (parameters were NOT fitted, this checks stability)
    w(f"## 3. Stability: before vs after {SPLIT:%Y-%m-%d} (limits off)\n")
    w("| Strategy | Period | " + HDR.split("\n")[0][2:]); w("|---|---" + HDR.split("\n")[1])
    halves = {}
    for name, strats in [("Trend", ("trend",)), ("Mean reversion", ("meanrev",))]:
        for label, s, e in [("early", None, SPLIT), ("late", SPLIT, None)]:
            r = run(data, risk=no_kill, strategies=strats, start=s, end=e)
            halves[(name, label)] = stats(r)
            w(f"| {name} | {label} " + fmt(halves[(name, label)]))
    w("")

    # 4. Fee sensitivity
    w("## 4. Fee sensitivity (limits off)\n")
    w("| Strategy | Fee/side | " + HDR.split("\n")[0][2:]); w("|---|---" + HDR.split("\n")[1])
    fee_stats = {}
    for name, strats in [("Trend", ("trend",)), ("Mean reversion", ("meanrev",))]:
        for f in (0.0, 0.0025, 0.005, 0.0075):
            r = run(data, risk=no_kill, strategies=strats, costs=replace(Costs(), fee=f))
            fee_stats[(name, f)] = stats(r)
            w(f"| {name} | {f:.2%} " + fmt(fee_stats[(name, f)]))
    w("")

    # 5. Per coin / per year for trend (limits off)
    for name in ("Trend", "Mean reversion"):
        tr = diag[name].trades
        if tr.empty:
            continue
        w(f"## 5. {name}: R by coin and year (limits off)\n")
        tr = tr.assign(year=tr.exit_time.dt.year)
        piv = tr.pivot_table(index="coin", columns="year", values="R", aggfunc="sum").round(1)
        piv["trades"] = tr.groupby("coin").size()
        w(md_table(piv) + "\n")

    # Verdict
    w("## Verdict against golden rule 2 (draft criteria)\n")
    w(f"Pass needs, per strategy: >= {MIN_TRADES} trades, profit factor >= {MIN_PF} at 0.50% fees, "
      "positive expectancy in BOTH halves, and still positive at 0.75% fees.\n")
    verdict = {}
    for name in ("Trend", "Mean reversion"):
        s = stats(diag[name])
        checks = {
            f"trades >= {MIN_TRADES}": s.get("trades", 0) >= MIN_TRADES,
            f"PF >= {MIN_PF}": s.get("profit_factor", 0) >= MIN_PF,
            "early half positive": halves[(name, "early")].get("expectancy_usd", -1) > 0,
            "late half positive": halves[(name, "late")].get("expectancy_usd", -1) > 0,
            "positive at 0.75% fees": fee_stats[(name, 0.0075)].get("expectancy_usd", -1) > 0,
        }
        ok = all(checks.values())
        verdict[name] = ok
        w(f"- **{name}: {'PASS' if ok else 'FAIL'}** — " + ", ".join(f"{k} {'✓' if v else '✗'}" for k, v in checks.items()))
    w("")
    (OUT / "RESULTS.md").write_text("\n".join(L))
    print("\n".join(L))
    json.dump(verdict, open(OUT / "verdict.json", "w"))


if __name__ == "__main__":
    main()
