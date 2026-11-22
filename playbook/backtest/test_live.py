"""Dry-run live mode builds valid Coinbase orders from a paper book (no network, no keys)."""
import json

import pytest

import live
from engine import Book, Position
from paper import make_book


def fake_get(path):
    c = path.split("/")[2].split("-")[0]
    if path.endswith("/ticker"):
        return {"BTC": {"price": "60000", "bid": "59999", "ask": "60001"},
                "SHIB": {"price": "0.00002", "bid": "0.0000199", "ask": "0.0000201"},
                "ETH": {"price": "2000", "bid": "1999.9", "ask": "2000.1"}}[c]
    return {"BTC": dict(base_increment="0.00000001", quote_increment="0.01", min_market_funds="1"),
            "SHIB": dict(base_increment="1", quote_increment="0.00000001", min_market_funds="1"),
            "ETH": dict(base_increment="0.00000001", quote_increment="0.01", min_market_funds="1")}[c] | {
        "status": "online", "trading_disabled": False, "cancel_only": False}


def test_dry_run_orders(tmp_path, monkeypatch):
    book = make_book()
    book.cash, book.last_bar = 90.0, "2026-11-23T00:00:00+00:00"
    book.equity = [[book.last_bar, 100.0]]
    book.pos["BTC"] = Position("BTC", "trend", 0.000123456789, 58000.0, 52345.678, 0.04, 0.5, "2026-11-20T08:00:00+00:00")
    book.working = [["SHIB", "trend", 0.0000170, 0.0000199, 1]]
    book.pending_entries = [["ETH", "trend", 1800.0]]
    monkeypatch.setattr(live, "load", lambda: (book, {"started": "x"}))
    monkeypatch.setattr(live, "get", fake_get)
    monkeypatch.setattr(live, "DIR", tmp_path)
    live.main()
    out = json.loads((tmp_path / "dry_run.json").read_text())
    assert out["rule1_every_position_has_stop"] and not out["problems"]
    stop, buy, mbuy = [o["body"] for o in out["orders"]]

    s = stop["order_configuration"]["stop_limit_stop_limit_gtc"]
    assert stop["side"] == "SELL" and s["base_size"] == "0.00012345"       # floored to base_increment
    assert s["stop_price"] == "52345.67" and s["limit_price"] == "50775.30"  # floored; 3% buffer
    assert s["stop_direction"] == "STOP_DIRECTION_STOP_DOWN"

    b = buy["order_configuration"]["limit_limit_gtc"]
    assert buy["side"] == "BUY" and b["post_only"] is True
    assert b["limit_price"] == "0.00001990" and float(b["base_size"]).is_integer()
    assert 1 <= float(b["base_size"]) * 0.0000199 <= 90                    # above minimum, within cash

    m = mbuy["order_configuration"]["market_market_ioc"]
    assert 1 <= float(m["quote_size"]) <= 90


def test_flags_problems(tmp_path, monkeypatch):
    book = make_book()
    book.equity = [["t", 100.0]]
    book.last_bar = "2026-11-23T00:00:00+00:00"
    book.pos["BTC"] = Position("BTC", "trend", 1e-9, 58000.0, 61000.0, 0.0, 0.5, "t")  # dust, price below stop
    monkeypatch.setattr(live, "load", lambda: (book, {}))
    monkeypatch.setattr(live, "get", fake_get)
    monkeypatch.setattr(live, "DIR", tmp_path)
    live.main()
    out = json.loads((tmp_path / "dry_run.json").read_text())
    assert len(out["problems"]) == 2


def test_send_always_refuses():
    with pytest.raises(SystemExit):
        live.send({})
