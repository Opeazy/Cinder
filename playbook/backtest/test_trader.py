"""Live trader against a fake Coinbase: golden rule 1 and real-fill accounting."""
import pytest

from config import CHOSEN, CHOSEN_ENTRY, Costs, MeanRevParams, Risk
from engine import Book, Position
from trader import LiveTrader

PROD = {"base_increment": "0.00000001", "quote_increment": "0.01", "min_market_funds": "1"}


class FakeX:
    def __init__(self, price=100.0):
        self.price, self.orders, self.n = price, {}, 0
        self.reject_stops = False
        self.fee = {"limit": 0.005, "market": 0.009, "stop": 0.009}

    def best_bid_ask(self, pid):
        return self.price - 0.01, self.price + 0.01

    def create(self, coid, pid, side, cfg):
        kind = next(iter(cfg))
        if kind.startswith("stop") and self.reject_stops:
            raise RuntimeError("stop rejected")
        self.n += 1
        oid = f"o{self.n}"
        body = cfg[kind]
        o = {"pid": pid, "side": side, "kind": kind, "cfg": body, "status": "OPEN",
             "filled_size": 0.0, "avg_price": 0.0, "fees": 0.0, "filled_value": 0.0}
        self.orders[oid] = o
        if kind == "market_market_ioc":
            size = float(body["base_size"]) if "base_size" in body else float(body["quote_size"]) / self.price
            self._fill(oid, size, self.price, "market")
        return oid

    def _fill(self, oid, size, px, kind):
        o = self.orders[oid]
        o.update(status="FILLED", filled_size=size, avg_price=px, filled_value=size * px,
                 fees=size * px * self.fee[kind])

    def fill_limit(self, pid):
        for oid, o in self.orders.items():
            if o["pid"] == pid and o["kind"] == "limit_limit_gtc" and o["status"] == "OPEN":
                self._fill(oid, float(o["cfg"]["base_size"]), float(o["cfg"]["limit_price"]), "limit")

    def trigger_stop(self, pid):
        for oid, o in self.orders.items():
            if o["pid"] == pid and o["kind"].startswith("stop") and o["status"] == "OPEN":
                self._fill(oid, float(o["cfg"]["base_size"]), float(o["cfg"]["stop_price"]), "stop")

    def cancel(self, oid):
        if self.orders[oid]["status"] == "OPEN":
            self.orders[oid]["status"] = "CANCELLED"

    def order(self, oid):
        return dict(self.orders[oid])

    def open_stops(self, pid):
        return [o for o in self.orders.values() if o["pid"] == pid and o["kind"].startswith("stop") and o["status"] == "OPEN"]


def setup(x):
    book = Book(["BTC"], Costs(), Risk(), CHOSEN, MeanRevParams(), ("trend",), CHOSEN_ENTRY)
    book.equity = [["t0", 100.0]]
    book.last_bar = "t0"
    logs = []
    tr = LiveTrader(book, {}, x, {"BTC": PROD}, logs.append)
    return book, tr, logs


def act(tr):
    r = Risk()
    tr.act("t1", {}, True, 0.005, 0.009, r.risk_per_trade, r.max_positions)


def test_buy_fill_gets_stop_then_stop_exit_uses_real_fill():
    x = FakeX(100.0)
    book, tr, logs = setup(x)
    book.working = [["BTC", "trend", 80.0, 100.0, 1]]     # signal: limit at 100, stop 80
    act(tr)
    assert "BTC" in tr.orders["buy"] and not book.pos
    x.fill_limit("BTC-USD")
    tr.sync("t1")
    assert "BTC" in book.pos and len(x.open_stops("BTC-USD")) == 1   # rule 1
    stop_cfg = x.open_stops("BTC-USD")[0]["cfg"]
    assert stop_cfg["stop_price"] == "80.00" and stop_cfg["limit_price"] == "77.60"
    assert tr.check_rule1()
    pos = book.pos["BTC"]
    cash_before = book.cash
    x.trigger_stop("BTC-USD")
    tr.sync("t2")
    assert not book.pos and len(book.trades) == 1
    t = book.trades[0]
    assert t["R"] == pytest.approx(-1.0, abs=0.05)                  # real fills, about -1R
    assert book.cash == pytest.approx(cash_before + pos.qty * 80 * (1 - 0.009))


def test_stop_rejected_means_emergency_sell():
    x = FakeX(100.0)
    book, tr, logs = setup(x)
    book.working = [["BTC", "trend", 80.0, 100.0, 1]]
    act(tr)
    x.reject_stops = True
    x.fill_limit("BTC-USD")
    tr.sync("t1")
    assert not book.pos                                          # sold: no stop, no trade
    assert any("EMERGENCY SELL" in l for l in logs)
    assert book.trades[0]["reason"] == "emergency"


def test_trailing_stop_is_moved_and_never_left_missing():
    x = FakeX(100.0)
    book, tr, logs = setup(x)
    book.pos["BTC"] = Position("BTC", "trend", 0.05, 100.0, 80.0, 0.025, 1.0, "t0", high=100.0)
    book.cash = 95.0
    tr.sync("t1")                                                # no stop known -> placed
    assert len(x.open_stops("BTC-USD")) == 1
    book.pos["BTC"].stop = 90.0                                  # engine ratcheted the trail up
    act(tr)
    stops = x.open_stops("BTC-USD")
    assert len(stops) == 1 and stops[0]["cfg"]["stop_price"] == "90.00"
    assert tr.check_rule1()


def test_expired_limit_falls_back_to_market_with_stop():
    x = FakeX(100.0)
    book, tr, logs = setup(x)
    book.working = [["BTC", "trend", 80.0, 100.0, 1]]
    act(tr)                       # placed, 1 bar left
    act(tr)                       # not filled -> cancelled -> market fallback -> filled -> stop
    assert "BTC" in book.pos and len(x.open_stops("BTC-USD")) == 1
    assert book.cash >= 0


def test_kill_switch_cancels_resting_buys_but_keeps_stops():
    x = FakeX(100.0)
    book, tr, logs = setup(x)
    book.pos["BTC"] = Position("BTC", "trend", 0.05, 100.0, 80.0, 0.025, 1.0, "t0", high=100.0)
    tr.sync("t1")
    book.coins = ["BTC", "ETH"]
    tr.products["ETH"] = PROD
    book.working = [["ETH", "trend", 80.0, 100.0, 3]]
    act(tr)
    assert "ETH" in tr.orders["buy"]
    book.killed_at = "t2"
    act(tr)
    assert not tr.orders["buy"] and len(x.open_stops("BTC-USD")) == 1


def test_never_spends_more_than_cash_or_cap():
    x = FakeX(100.0)
    book, tr, logs = setup(x)
    book.cash = 10.0
    book.working = [["BTC", "trend", 99.0, 100.0, 1]]            # tight stop -> big size wanted
    act(tr)
    oid, *_ = tr.orders["buy"]["BTC"]
    o = x.orders[oid]
    assert float(o["cfg"]["base_size"]) * float(o["cfg"]["limit_price"]) * 1.005 <= 10.0 + 1e-6
