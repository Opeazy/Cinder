"""Trading core for the playbook: 4h bars, long-only spot, 1x, full costs.

The SAME `Book.step()` is used by the backtest (`run()`) and by the paper bot
(`paper.py`), so paper trades can be compared one-for-one with the backtest.

Timing (no look-ahead):
  * Signals are computed on a bar's CLOSE and filled at the NEXT bar's OPEN.
  * The stop is set from the signal bar (close - k*ATR) and rests on the exchange
    from the moment of entry ("no stop on the exchange, no trade").
  * Stops fill at the stop price, or at the open if the bar gaps through it,
    both minus slippage, and pay the taker fee.
  * Trailing stops only ratchet up, and are updated at bar close for the next bar.

Risk controls:
  * Size so that a stop-out loses `risk_per_trade` of equity INCLUDING both fees and slippage.
  * 1x: a buy can never cost more than available cash (spot, no margin).
  * At most `max_positions` open trades; extra signals are skipped in universe order.
  * Daily loss limit: if close equity <= UTC-day-start equity * (1 - limit), no new
    entries until the next UTC day.
  * Kill switch: if close equity <= equity high * (1 - kill), no new entries ever
    and no more management; open positions exit only via their resting stops.
"""
from dataclasses import asdict, dataclass, field

import numpy as np
import pandas as pd

from config import Costs, EntryParams, MeanRevParams, Risk, TrendParams
from indicators import atr, ema, rsi, sma

FIELDS = ["open", "high", "low", "close", "ema_tf", "ema_mr", "dc_high", "atr_tf", "atr_mr", "rsi", "sma_exit"]


@dataclass
class Position:
    coin: str
    strategy: str
    qty: float
    entry: float
    stop: float
    entry_fee: float
    risk_usd: float
    entry_time: str
    bars: int = 0
    high: float = 0.0


@dataclass
class Result:
    trades: pd.DataFrame
    equity: pd.Series
    kill_time: pd.Timestamp | None
    blocked_days: int
    skipped: dict = field(default_factory=dict)
    orders: dict = field(default_factory=dict)


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


class Book:
    """All trading state. `step(t, bars)` processes one completed 4h bar for every coin."""

    def __init__(self, coins, costs=Costs(), risk=Risk(), tp=TrendParams(), mp=MeanRevParams(),
                 strategies=("trend", "meanrev"), entry=EntryParams()):
        self.coins, self.costs, self.risk, self.tp, self.mp = list(coins), costs, risk, tp, mp
        self.entry = entry
        self.working = []  # resting limit buys: [coin, strategy, stop, limit, bars_left]
        self.orders = {"limit_placed": 0, "limit_filled": 0, "limit_expired": 0, "fallback_market": 0}
        self.strategies = tuple(strategies)
        self.cash = risk.capital
        self.pos: dict[str, Position] = {}
        self.pending_entries = []  # [coin, strategy, stop]
        self.pending_exits = []
        self.trades, self.equity = [], []  # equity: [iso time, value]
        self.events = []  # human-readable log of orders (what the bot would send)
        self.eq_high = risk.capital
        self.killed_at = None
        self.day, self.day_start_eq, self.day_blocked = None, risk.capital, False
        self.blocked_days = 0
        self.last_close = {}
        self.last_bar = None
        self.skipped = {"gap_below_stop": 0, "below_min_notional": 0, "no_cash": 0, "max_positions": 0}

    # ---- state (de)serialisation for the paper bot ----
    def to_dict(self):
        d = {k: v for k, v in self.__dict__.items() if k not in ("costs", "risk", "tp", "mp", "pos", "entry")}
        d["pos"] = {c: asdict(p) for c, p in self.pos.items()}
        return d

    def load_dict(self, d):
        for k, v in d.items():
            if k == "pos":
                self.pos = {c: Position(**p) for c, p in v.items()}
            elif k != "coins":
                setattr(self, k, v)
        self.strategies = tuple(self.strategies)
        return self

    # ---- helpers ----
    def _log(self, t, msg):
        self.events.append(f"{t} {msg}")

    def _px(self, bars, c, f):
        b = bars.get(c)
        return b[f] if b is not None else self.last_close.get(c, self.pos[c].entry)

    def _mtm(self, bars, f):
        return self.cash + sum(p.qty * self._px(bars, c, f) for c, p in self.pos.items())

    def _close(self, c, price, t, reason):
        p = self.pos.pop(c)
        fee, slip = self.costs.fee, self.costs.slippage
        fill = price * (1 - slip)
        proceeds = p.qty * fill
        exit_fee = proceeds * fee
        self.cash += proceeds - exit_fee
        pnl = proceeds - exit_fee - (p.qty * p.entry + p.entry_fee)
        self.trades.append(dict(coin=c, strategy=p.strategy, entry_time=p.entry_time, exit_time=t,
                                entry=p.entry, exit=fill, stop=p.stop, qty=p.qty, notional=p.qty * p.entry,
                                fees=p.entry_fee + exit_fee, pnl=pnl, R=pnl / p.risk_usd,
                                bars=p.bars, reason=reason))
        self._log(t, f"SELL {c} qty={p.qty:.8g} @ {fill:.6g} ({reason}) pnl=${pnl:+.4f} R={pnl / p.risk_usd:+.2f}")

    def _buy(self, t, bars, c, strat, stop, fill, entry_fee_rate, kind):
        slip, fee = self.costs.slippage, self.costs.fee
        if fill <= stop:
            self.skipped["gap_below_stop"] += 1
            return False
        equity = self._mtm(bars, "open")
        risk_usd = self.risk.risk_per_trade * equity
        loss_per_unit = (fill - stop * (1 - slip)) + entry_fee_rate * fill + fee * stop * (1 - slip)
        qty = risk_usd / loss_per_unit
        if qty * fill * (1 + entry_fee_rate) > self.cash:  # 1x / spot
            qty = self.cash / (fill * (1 + entry_fee_rate))
            if qty * fill < self.costs.min_notional:
                self.skipped["no_cash"] += 1
                return False
        if qty * fill < self.costs.min_notional:
            self.skipped["below_min_notional"] += 1
            return False
        entry_fee = qty * fill * entry_fee_rate
        self.cash -= qty * fill + entry_fee
        self.pos[c] = Position(c, strat, qty, fill, stop, entry_fee, qty * loss_per_unit, t, high=bars[c]["high"])
        self._log(t, f"BUY {c} qty={qty:.8g} @ {fill:.6g} ({strat}, {kind}); STOP-SELL placed @ {stop:.6g}")
        return True

    # ---- one bar ----
    def step(self, t, bars):
        """t: bar open time (ISO string). bars: {coin: {field: value}} for coins with a bar at t."""
        fee, slip, risk, tp, mp = self.costs.fee, self.costs.slippage, self.risk, self.tp, self.mp
        day = t[:10]
        if day != self.day:
            self.day = day
            self.day_start_eq = self._mtm(bars, "open")
            self.day_blocked = False

        # at the open: queued market exits, then queued entries
        for c in self.pending_exits:
            if c in self.pos and c in bars:
                self._close(c, bars[c]["open"], t, "signal")
        self.pending_exits = []

        can_enter = self.killed_at is None and not self.day_blocked
        for c, strat, stop in self.pending_entries:
            if not can_enter or c in self.pos or c not in bars:
                continue
            if risk.max_positions and len(self.pos) >= risk.max_positions:
                self.skipped["max_positions"] += 1
                continue
            self._buy(t, bars, c, strat, stop, bars[c]["open"] * (1 + slip), fee, "market")
        self.pending_entries = []

        # resting limit buys: fill as maker at the limit if the bar trades below it
        still = []
        for c, strat, stop, limit, left in self.working:
            if not can_enter or c in self.pos:
                continue  # cancelled
            if c in bars and bars[c]["low"] < limit:
                if risk.max_positions and len(self.pos) >= risk.max_positions:
                    self.skipped["max_positions"] += 1
                    continue
                if self._buy(t, bars, c, strat, stop, limit, self.costs.maker_fee, "limit"):
                    self.orders["limit_filled"] += 1
                continue
            left -= 1
            if left > 0:
                still.append([c, strat, stop, limit, left])
                continue
            self.orders["limit_expired"] += 1
            self._log(t, f"CANCEL limit buy {c} @ {limit:.6g} (not filled)")
            if self.entry.fallback_market:
                self.orders["fallback_market"] += 1
                self.pending_entries.append([c, strat, stop])
        self.working = still

        # intrabar: resting stops
        for c in list(self.pos):
            if c not in bars:
                continue
            p, b = self.pos[c], bars[c]
            if b["open"] <= p.stop:
                self._close(c, b["open"], t, "stop_gap")
            elif b["low"] <= p.stop:
                self._close(c, p.stop, t, "stop")

        for c, b in bars.items():
            self.last_close[c] = b["close"]
        self.last_bar = t

        # at the close: risk checks
        equity = self._mtm(bars, "close")
        self.equity.append([t, equity])
        self.eq_high = max(self.eq_high, equity)
        if self.killed_at is None and equity <= self.eq_high * (1 - risk.kill_switch):
            self.killed_at = t
            self._log(t, f"KILL SWITCH: equity ${equity:.2f} <= high ${self.eq_high:.2f} - {risk.kill_switch:.0%}. "
                         "No new trades; resting stops stay.")
        if not self.day_blocked and equity <= self.day_start_eq * (1 - risk.daily_loss_limit):
            self.day_blocked = True
            self.blocked_days += 1
            self._log(t, f"DAILY LIMIT: equity ${equity:.2f} vs day start ${self.day_start_eq:.2f}. "
                         "No new entries until next UTC day.")
        if self.killed_at is not None:
            return

        # manage open positions
        for c, p in self.pos.items():
            if c not in bars:
                continue
            b = bars[c]
            p.bars += 1
            p.high = max(p.high, b["high"])
            if p.strategy == "trend":
                new = max(p.stop, p.high - tp.trail_atr * b["atr_tf"])
                if new > p.stop:
                    self._log(t, f"MOVE STOP {c} {p.stop:.6g} -> {new:.6g}")
                p.stop = new
            elif b["close"] > b["sma_exit"] or p.bars >= mp.max_bars:
                self.pending_exits.append(c)

        # signals for the next open
        if self.day_blocked:
            return
        resting = {o[0] for o in self.working} | {o[0] for o in self.pending_entries}
        for c in self.coins:
            if c in self.pos or c not in bars or c in resting:
                continue
            b = bars[c]
            cl = b["close"]
            sig = None
            if "trend" in self.strategies and cl > b["ema_tf"] and cl > b["dc_high"]:
                sig = ("trend", cl - tp.init_stop_atr * b["atr_tf"], b["atr_tf"])
            elif "meanrev" in self.strategies and cl > b["ema_mr"] and b["rsi"] < mp.rsi_entry:
                sig = ("meanrev", cl - mp.stop_atr * b["atr_mr"], b["atr_mr"])
            if sig is None:
                continue
            strat, stop, a = sig
            if self.entry.mode == "limit":
                limit = cl - self.entry.offset_atr * a
                self.working.append([c, strat, stop, limit, self.entry.valid_bars])
                self.orders["limit_placed"] += 1
                self._log(t, f"SIGNAL {c} {strat}: LIMIT BUY placed @ {limit:.6g} for {self.entry.valid_bars} bar(s), "
                             f"stop {stop:.6g}")
            else:
                self.pending_entries.append([c, strat, stop])
                self._log(t, f"SIGNAL {c} {strat}: buy at next open, stop {stop:.6g}")


def bar_rows(data, start=None, end=None):
    """Yield (iso time, {coin: {field: value}}) for each bar time, skipping coins with no bar/NaN."""
    index = sorted(set().union(*[d.index for d in data.values()]))
    index = [t for t in index if (start is None or t >= start) and (end is None or t < end)]
    cols = {c: d.reindex(index)[FIELDS].to_numpy() for c, d in data.items()}
    for i, t in enumerate(index):
        bars = {}
        for c, a in cols.items():
            row = a[i]
            if not np.isnan(row[0]):
                # NaN indicators (warm-up) make every comparison False -> no signal, like before
                bars[c] = dict(zip(FIELDS, row.tolist()))
        yield t.isoformat(), bars


def run(data: dict, costs=Costs(), risk=Risk(), tp=TrendParams(), mp=MeanRevParams(),
        strategies=("trend", "meanrev"), start=None, end=None, entry=EntryParams()):
    data = {c: add_indicators(d, tp, mp) for c, d in data.items()}
    book = Book(data, costs, risk, tp, mp, strategies, entry)
    for t, bars in bar_rows(data, start, end):
        book.step(t, bars)
    for c in list(book.pos):  # mark anything still open at the last close
        book._close(c, book.last_close[c], book.last_bar, "end_of_test")
    return to_result(book)


def to_result(book):
    tr = pd.DataFrame(book.trades)
    if not tr.empty:
        tr["entry_time"] = pd.to_datetime(tr.entry_time)
        tr["exit_time"] = pd.to_datetime(tr.exit_time)
    eq = pd.Series({pd.Timestamp(t): v for t, v in book.equity})
    kill = pd.Timestamp(book.killed_at) if book.killed_at else None
    return Result(tr, eq, kill, book.blocked_days, dict(book.skipped), dict(book.orders))


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
