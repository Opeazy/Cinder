"""Sanity tests for the engine on synthetic bars: python -m pytest -q"""
import numpy as np
import pandas as pd
import pytest

from config import Costs, Risk, TrendParams
from engine import run


def bars(closes, lows=None, opens=None):
    idx = pd.date_range("2024-01-01", periods=len(closes), freq="4h", tz="UTC")
    c = np.asarray(closes, float)
    o = np.r_[c[0], c[:-1]] if opens is None else np.asarray(opens, float)
    lo = np.minimum(o, c) * 0.999 if lows is None else np.asarray(lows, float)
    hi = np.maximum(o, c) * 1.001
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": c, "volume": 1.0}, index=idx)


def uptrend_then_breakout(n=260):
    # gentle zig-zag uptrend so ATR > 0 and close > EMA200, then a clear breakout
    base = 100 + np.arange(n) * 0.05 + np.where(np.arange(n) % 2, 0.5, -0.5)
    return list(base) + [base[-1] + 5]


def test_stop_out_loses_about_1R_including_costs():
    closes = uptrend_then_breakout() + [120, 80]  # entry bar, then a bar that trades through the stop
    df = bars(closes)  # crash bar opens at 120 (prior close), low ~80
    res = run({"X": df}, strategies=("trend",), tp=TrendParams(trail_atr=1e6))  # keep the initial stop
    tr = res.trades
    t = tr.iloc[0]
    assert t.reason == "stop"
    assert t.entry_time == df.index[-2]  # filled at the open AFTER the signal bar
    assert t.R == pytest.approx(-1.0, abs=1e-6)
    assert t.fees > 0


def test_gap_through_stop_fills_at_open_and_loses_more_than_1R():
    closes = uptrend_then_breakout() + [120, 60]
    df = bars(closes)
    opens = df["open"].to_numpy().copy()
    opens[-1] = 60  # gaps well below stop
    df["open"] = opens
    res = run({"X": df}, strategies=("trend",))
    t = res.trades.iloc[0]
    assert t.reason == "stop_gap"
    assert t.exit == pytest.approx(60 * (1 - Costs().slippage))
    assert t.R < -1.0


def test_never_spends_more_than_cash():
    closes = uptrend_then_breakout() + [120, 121]
    res = run({"X": bars(closes)}, strategies=("trend",), risk=Risk(risk_per_trade=0.5))
    t = res.trades.iloc[0]
    assert t.notional * (1 + Costs().fee) <= 100.0 + 1e-9


def test_kill_switch_blocks_new_entries():
    closes = uptrend_then_breakout() + [120, 60, 70, 140, 150]
    df = bars(closes)
    opens = df["open"].to_numpy().copy()
    opens[-4] = 60  # gap far through the stop -> ~-50% on a full-size position
    df["open"] = opens
    res = run({"X": df}, strategies=("trend",), risk=Risk(risk_per_trade=0.5))  # big loss -> kill
    assert res.kill_time is not None
    assert len(res.trades) == 1


def test_book_state_roundtrip_matches_backtest():
    """Paper bot path (step + JSON save/load every bar) must equal the backtest path."""
    import json
    from config import MeanRevParams, TrendParams
    CHOSEN = TrendParams(breakout=180, atr=42, init_stop_atr=5.0, trail_atr=7.0)
    from engine import Book, add_indicators, bar_rows, to_result

    rng = np.random.default_rng(0)
    data = {}
    for c in ("A", "B", "C"):
        closes = 100 * np.exp(np.cumsum(rng.normal(0.002, 0.03, 1500)))
        data[c] = add_indicators(bars(closes), CHOSEN, MeanRevParams())
    rows = list(bar_rows(data))

    ref = Book(data, tp=CHOSEN, strategies=("trend",))
    for t, b in rows:
        ref.step(t, b)

    book = Book(data, tp=CHOSEN, strategies=("trend",))
    for t, b in rows:
        state = json.loads(json.dumps(book.to_dict()))
        book = Book(data, tp=CHOSEN, strategies=("trend",)).load_dict(state)
        book.step(t, b)

    assert len(ref.trades) > 5
    assert book.trades == ref.trades
    assert book.cash == pytest.approx(ref.cash)


def _breakout_then(next_bar_low_factor, maker=0.0025, fallback=False):
    from config import EntryParams
    closes = uptrend_then_breakout() + [120, 121, 122]
    df = bars(closes)
    sig_close = df["close"].iloc[-4]
    lows = df["low"].to_numpy().copy()
    lows[-3] = sig_close * next_bar_low_factor  # bar after the signal
    lows[-2:] = df["close"].iloc[-3] * 1.5       # later bars never come back down
    df["low"] = lows
    entry = EntryParams(mode="limit", valid_bars=1, fallback_market=fallback)
    return run({"X": df}, strategies=("trend",), entry=entry, costs=Costs(maker_fee=maker)), sig_close


def test_limit_fills_as_maker_when_price_trades_below():
    res, sig_close = _breakout_then(0.99)
    t = res.trades.iloc[0]
    assert t.entry == pytest.approx(sig_close)  # filled at the limit, no slippage
    assert res.orders["limit_filled"] == 1
    assert t.fees == pytest.approx(t.qty * t.entry * 0.0025 + t.qty * t.exit * Costs().fee)


def test_limit_not_filled_is_skipped_or_falls_back():
    res, _ = _breakout_then(1.01)
    # every later bar is also a breakout, so a new limit is placed each bar and none fill
    assert res.trades.empty and res.orders["limit_filled"] == 0 and res.orders["limit_expired"] >= 1
    res, _ = _breakout_then(1.01, fallback=True)
    assert len(res.trades) == 1 and res.orders["fallback_market"] >= 1
    assert res.trades.iloc[0].entry > 120  # fallback bought at a later open, as taker
