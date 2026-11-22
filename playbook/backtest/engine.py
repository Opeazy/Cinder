"""Portfolio backtest for the playbook: 4h bars, long-only spot, 1x, full costs.

Timing (no look-ahead):
  * Signals are computed on a bar's CLOSE and filled at the NEXT bar's OPEN.
  * The stop is set from the signal bar (close - k*ATR) and is assumed to rest
    on the exchange from the moment of entry ("no stop on the exchange, no trade").
  * Stops fill at the stop price, or at the open if the bar gaps through it,
    both minus slippage, and pay the taker fee.
  * Trailing stops only ratchet up, and are updated at bar close for the next bar.

Risk controls:
  * Size so that a stop-out loses ~1% of equity INCLUDING both fees and slippage.
  * 1x: a buy can never cost more than available cash (spot, no margin).
  * Daily loss limit: if close equity <= UTC-day-start equity * (1 - 3%), no new
    entries until the next UTC day.
  * Kill switch: if close equity <= equity high * (1 - 15%), no new entries ever
    and no more management; open positions exit only via their resting stops.
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from config import Costs, MeanRevParams, Risk, TrendParams
from indicators import atr, ema, rsi, sma


@dataclass
class Position:
    coin: str
    strategy: str
    qty: float
    entry: float
    stop: float
    entry_fee: float
    risk_usd: float
    entry_time: pd.Timestamp
    bars: int = 0
    high: float = 0.0


@dataclass
class Result:
    trades: pd.DataFrame
    equity: pd.Series
    kill_time: pd.Timestamp | None
    blocked_days: int
    skipped: dict = field(default_factory=dict)


def add_indicators(df, tp: TrendParams, mp: MeanRevParams):
    df = df.copy()
    df["ema_tf"] = ema(df["close"], tp.regime_ema)
    df["ema_mr"] = ema(df["close"], mp.regime_ema)
    df["dc_high"] = df["high"].rolling(tp.breakout).max().shift(1)
    df["atr_tf"] = atr(df, tp.atr)
    df["atr_mr"] = atr(df, mp.atr)
    df["rsi"] = rsi(df["close"], mp.rsi)
    df["sma_exit"] = sma(df["close"], mp.exit_sma)
    return df


def run(data: dict, costs=Costs(), risk=Risk(), tp=TrendParams(), mp=MeanRevParams(),
        strategies=("trend", "meanrev"), start=None, end=None):
    data = {c: add_indicators(d, tp, mp) for c, d in data.items()}
    index = sorted(set().union(*[d.index for d in data.values()]))
    index = [t for t in index if (start is None or t >= start) and (end is None or t < end)]
    coins = list(data)
    rows = {c: data[c].reindex(index) for c in coins}
    arr = {c: {k: rows[c][k].to_numpy() for k in rows[c].columns} for c in coins}

    fee, slip = costs.fee, costs.slippage
    cash = risk.capital
    pos: dict[str, Position] = {}
    pending_entries = []  # (coin, strategy, stop)
    pending_exits = set()
    trades, eq_curve = [], []
    eq_high = risk.capital
    killed_at = None
    day, day_start_eq, day_blocked = None, risk.capital, False
    blocked_days = 0
    skipped = {"gap_below_stop": 0, "below_min_notional": 0, "no_cash": 0}

    def close_pos(p, price, t, reason):
        nonlocal cash
        fill = price * (1 - slip)
        proceeds = p.qty * fill
        exit_fee = proceeds * fee
        cash += proceeds - exit_fee
        pnl = proceeds - exit_fee - (p.qty * p.entry + p.entry_fee)
        trades.append(dict(coin=p.coin, strategy=p.strategy, entry_time=p.entry_time, exit_time=t,
                           entry=p.entry, exit=fill, qty=p.qty, notional=p.qty * p.entry,
                           fees=p.entry_fee + exit_fee, pnl=pnl, R=pnl / p.risk_usd,
                           bars=p.bars, reason=reason))

    def mtm(i, field_="close"):
        v = cash
        for c, p in pos.items():
            px = arr[c][field_][i]
            v += p.qty * (px if not np.isnan(px) else p.entry)
        return v

    for i, t in enumerate(index):
        # ---- new UTC day ----
        if t.date() != day:
            day = t.date()
            day_start_eq = mtm(i, "open") if i else risk.capital
            day_blocked = False

        # ---- at the open: queued market exits, then queued entries ----
        for c in list(pending_exits):
            o = arr[c]["open"][i]
            if c in pos and not np.isnan(o):
                close_pos(pos.pop(c), o, t, "signal")
        pending_exits.clear()

        can_enter = killed_at is None and not day_blocked
        for c, strat, stop in pending_entries:
            o = arr[c]["open"][i]
            if not can_enter or c in pos or np.isnan(o):
                continue
            fill = o * (1 + slip)
            if fill <= stop:
                skipped["gap_below_stop"] += 1
                continue
            equity = mtm(i, "open")
            risk_usd = risk.risk_per_trade * equity
            loss_per_unit = (fill - stop * (1 - slip)) + fee * fill + fee * stop * (1 - slip)
            qty = risk_usd / loss_per_unit
            if qty * fill * (1 + fee) > cash:  # 1x / spot: cannot spend more than cash
                qty = cash / (fill * (1 + fee))
                if qty * fill < costs.min_notional:
                    skipped["no_cash"] += 1
                    continue
            if qty * fill < costs.min_notional:
                skipped["below_min_notional"] += 1
                continue
            entry_fee = qty * fill * fee
            cash -= qty * fill + entry_fee
            pos[c] = Position(c, strat, qty, fill, stop, entry_fee,
                              qty * loss_per_unit, t, high=arr[c]["high"][i])
        pending_entries = []

        # ---- intrabar: resting stops ----
        for c in list(pos):
            p = pos[c]
            o, lo = arr[c]["open"][i], arr[c]["low"][i]
            if np.isnan(o):
                continue
            if o <= p.stop:
                close_pos(pos.pop(c), o, t, "stop_gap")
            elif lo <= p.stop:
                close_pos(pos.pop(c), p.stop, t, "stop")

        # ---- at the close: risk checks ----
        equity = mtm(i)
        eq_curve.append((t, equity))
        eq_high = max(eq_high, equity)
        if killed_at is None and equity <= eq_high * (1 - risk.kill_switch):
            killed_at = t
        if not day_blocked and equity <= day_start_eq * (1 - risk.daily_loss_limit):
            day_blocked = True
            blocked_days += 1
        if killed_at is not None:
            continue  # stop all, keep stops

        # ---- manage open positions ----
        for c, p in pos.items():
            a = arr[c]
            if np.isnan(a["close"][i]):
                continue
            p.bars += 1
            p.high = max(p.high, a["high"][i])
            if p.strategy == "trend":
                p.stop = max(p.stop, p.high - tp.trail_atr * a["atr_tf"][i])
            else:
                if a["close"][i] > a["sma_exit"][i] or p.bars >= mp.max_bars:
                    pending_exits.add(c)

        # ---- signals for next open ----
        if day_blocked:
            continue
        for c in coins:
            if c in pos:
                continue
            a = arr[c]
            cl = a["close"][i]
            if np.isnan(cl):
                continue
            if "trend" in strategies and cl > a["ema_tf"][i] and cl > a["dc_high"][i]:
                pending_entries.append((c, "trend", cl - tp.init_stop_atr * a["atr_tf"][i]))
            elif ("meanrev" in strategies and cl > a["ema_mr"][i] and a["rsi"][i] < mp.rsi_entry):
                pending_entries.append((c, "meanrev", cl - mp.stop_atr * a["atr_mr"][i]))

    # mark anything still open at the last close
    last = len(index) - 1
    for c in list(pos):
        close_pos(pos.pop(c), arr[c]["close"][last], index[last], "end_of_test")

    eq = pd.Series(dict(eq_curve))
    return Result(pd.DataFrame(trades), eq, killed_at, blocked_days, skipped)


def stats(res: Result, capital=100.0):
    tr, eq = res.trades, res.equity
    if tr.empty:
        return dict(trades=0)
    gross_win = tr.loc[tr.pnl > 0, "pnl"].sum()
    gross_loss = -tr.loc[tr.pnl <= 0, "pnl"].sum()
    dd = (eq / eq.cummax() - 1).min()
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    final = eq.iloc[-1]
    return dict(
        trades=len(tr),
        win_rate=(tr.pnl > 0).mean(),
        avg_R=tr.R.mean(),
        expectancy_usd=tr.pnl.mean(),
        profit_factor=gross_win / gross_loss if gross_loss else np.inf,
        net_pnl=final - capital,
        return_pct=final / capital - 1,
        cagr=(final / capital) ** (1 / years) - 1 if years > 0 and final > 0 else np.nan,
        max_dd=dd,
        fees=tr.fees.sum(),
        pnl_before_fees=tr.pnl.sum() + tr.fees.sum(),
    )
