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
