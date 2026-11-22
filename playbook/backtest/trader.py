"""Live trader for the playbook: real Coinbase Advanced orders, same decisions as backtest/paper.

Each run (once per 4h bar, a few minutes after the close):
  1. SYNC with Coinbase: read the status of every resting buy and every stop.
       - buy filled   -> open the position with the REAL size/price/fees, place its stop at once
       - stop filled  -> close the position with the REAL fill
       - stop missing -> re-place it; if that fails, sell at market (golden rule 1)
  2. DECIDE with the shared engine (Book.decide_phase): daily limit, kill switch, trailing
     stops, new signals. Identical code to the backtest and paper bot.
  3. ACT: move stops (cancel + replace), cancel expired buys (market fallback), place new
     post-only limit buys. Never more than the account holds; nothing new after the kill
     switch or daily limit.
  4. CHECK golden rule 1: every open position has a resting stop order, else sell it.

The exchange is passed in, so tests use a fake one. Only the bot's own positions are ever
sold: it never touches coins it did not buy.
"""
import math
import time

from engine import Position

STOP_LIMIT_BUFFER = 0.03   # stop-limit sell: limit 3% below the trigger
MAX_ORDER_USD = 60.0       # sanity cap per order
DONE = {"FILLED"}
DEAD = {"CANCELLED", "EXPIRED", "FAILED"}


def floor_to(x, inc):
    inc = float(inc)
    return math.floor(x / inc + 1e-9) * inc


def fmt(x, inc):
    decimals = max(0, -int(math.floor(math.log10(float(inc)))))
    return f"{x:.{decimals}f}"


class CoinbaseExchange:
    """Thin wrapper over the official SDK. Needs a CDP API key file (JSON) on THIS machine."""

    def __init__(self, key_file):
        from coinbase.rest import RESTClient  # pip install coinbase-advanced-py
        self.c = RESTClient(key_file=key_file)

    def _d(self, r):
        return r.to_dict() if hasattr(r, "to_dict") else r

    def product(self, pid):
        return self._d(self.c.get_product(pid))

    def best_bid_ask(self, pid):
        b = self._d(self.c.get_best_bid_ask(product_ids=[pid]))["pricebooks"][0]
        return float(b["bids"][0]["price"]), float(b["asks"][0]["price"])

    def balance(self, currency):
        total, cursor = 0.0, None
        while True:
            r = self._d(self.c.get_accounts(limit=250, cursor=cursor))
            for a in r["accounts"]:
                if a["currency"] == currency:
                    total += float(a["available_balance"]["value"])
            if not r.get("has_next"):
                return total
            cursor = r["cursor"]

    def create(self, client_order_id, pid, side, config):
        r = self._d(self.c.create_order(client_order_id=client_order_id, product_id=pid, side=side,
                                        order_configuration=config))
        if not r.get("success"):
            raise RuntimeError(f"order rejected: {r.get('error_response') or r}")
        return r["success_response"]["order_id"]

    def preview(self, pid, side, config):
        return self._d(self.c.preview_order(product_id=pid, side=side, order_configuration=config))

    def cancel(self, order_id):
        r = self._d(self.c.cancel_orders(order_ids=[order_id]))
        res = r["results"][0]
        if not res.get("success") and res.get("failure_reason") not in ("UNKNOWN_CANCEL_ORDER", "DUPLICATE_CANCEL_REQUEST"):
            raise RuntimeError(f"cancel failed: {res}")

    def order(self, order_id):
        o = self._d(self.c.get_order(order_id))["order"]
        return {"status": o["status"], "filled_size": float(o.get("filled_size") or 0),
                "avg_price": float(o.get("average_filled_price") or 0), "fees": float(o.get("total_fees") or 0),
                "filled_value": float(o.get("filled_value") or 0)}

    def permissions(self):
        return self._d(self.c.get_api_key_permissions())


class LiveTrader:
    def __init__(self, book, orders, exchange, products, log, taker_fee=0.009):
        self.taker_fee = taker_fee
        self.book = book            # engine.Book: cash/positions/stops as of the real account
        self.orders = orders        # {"stop": {coin: order_id}, "buy": {coin: [order_id, strat, stop, left]}}
        self.x = exchange
        self.products = products    # {coin: product info with base_increment, quote_increment, ...}
        self.log = log              # callable(str)
        self.orders.setdefault("stop", {})
        self.orders.setdefault("buy", {})
        self.orders.setdefault("n", 0)

    # ---------- helpers ----------
    def _coid(self, c, kind):
        self.orders["n"] += 1
        return f"pb-{c}-{kind}-{int(time.time())}-{self.orders['n']}"

    def _p(self, c):
        return self.products[c]

    def _place_stop(self, c):
        p, pos = self._p(c), self.book.pos[c]
        size = floor_to(pos.qty, p["base_increment"])
        cfg = {"stop_limit_stop_limit_gtc": {
            "base_size": fmt(size, p["base_increment"]),
            "limit_price": fmt(floor_to(pos.stop * (1 - STOP_LIMIT_BUFFER), p["quote_increment"]), p["quote_increment"]),
            "stop_price": fmt(floor_to(pos.stop, p["quote_increment"]), p["quote_increment"]),
            "stop_direction": "STOP_DIRECTION_STOP_DOWN"}}
        oid = self.x.create(self._coid(c, "stop"), f"{c}-USD", "SELL", cfg)
        self.orders["stop"][c] = oid
        self.orders.setdefault("stop_px", {})[c] = pos.stop
        self.log(f"STOP placed {c} size={cfg['stop_limit_stop_limit_gtc']['base_size']} "
                 f"stop={cfg['stop_limit_stop_limit_gtc']['stop_price']} id={oid}")

    def _emergency_sell(self, c, why):
        """Golden rule 1: a position without a stop is sold at market."""
        p, pos = self._p(c), self.book.pos[c]
        size = fmt(floor_to(pos.qty, p["base_increment"]), p["base_increment"])
        self.log(f"EMERGENCY SELL {c} ({why})")
        oid = self.x.create(self._coid(c, "esell"), f"{c}-USD", "SELL", {"market_market_ioc": {"base_size": size}})
        o = self.x.order(oid)
        if o["filled_size"] <= 0:
            self.log(f"!!! EMERGENCY SELL {c} DID NOT FILL (order {oid}, status {o['status']}). "
                     "Position has NO STOP. Check Coinbase now.")
            return
        self._record_exit(c, o, "emergency")

    def _ensure_stop(self, c):
        try:
            self._place_stop(c)
        except Exception as e:
            self._emergency_sell(c, f"stop could not be placed: {e}")

    def _record_entry(self, c, strat, stop, o, t):
        b = self.book
        cost = o["filled_value"] + o["fees"]
        b.cash -= cost
        risk_usd = max(o["filled_size"] * (o["avg_price"] - stop) + o["fees"] + self.taker_fee * o["filled_size"] * stop, 1e-9)
        b.pos[c] = Position(c, strat, o["filled_size"], o["avg_price"], stop, o["fees"], risk_usd, t,
                            high=o["avg_price"])
        b._log(t, f"BUY {c} qty={o['filled_size']:.8g} @ {o['avg_price']:.6g} fees=${o['fees']:.4f} (live); stop {stop:.6g}")

    def _record_exit(self, c, o, reason):
        b = self.book
        p = b.pos.pop(c)
        self.orders["stop"].pop(c, None)
        proceeds = o["filled_value"] - o["fees"]
        b.cash += proceeds
        pnl = proceeds - (p.qty * p.entry + p.entry_fee)
        b.trades.append(dict(coin=c, strategy=p.strategy, entry_time=p.entry_time, exit_time=b.last_bar,
                             entry=p.entry, exit=o["avg_price"], stop=p.stop, qty=p.qty, notional=p.qty * p.entry,
                             fees=p.entry_fee + o["fees"], pnl=pnl, R=pnl / p.risk_usd, bars=p.bars, reason=reason))
        b._log(b.last_bar, f"SELL {c} qty={o['filled_size']:.8g} @ {o['avg_price']:.6g} ({reason}, live) pnl=${pnl:+.4f}")

    # ---------- 1. sync ----------
    def sync(self, t):
        for c in list(self.book.pos):
            oid = self.orders["stop"].get(c)
            if oid is None:
                self._ensure_stop(c)
                continue
            o = self.x.order(oid)
            if o["status"] in DONE:
                self._record_exit(c, o, "stop")
            elif o["status"] in DEAD:
                self.log(f"WARNING stop for {c} is {o['status']}; re-placing")
                if o["filled_size"] > 0:
                    self.log(f"WARNING stop for {c} partly filled ({o['filled_size']}); position reduced")
                    self.book.pos[c].qty -= o["filled_size"]
                    self.book.cash += o["filled_value"] - o["fees"]
                self._ensure_stop(c)

        for c, (oid, strat, stop, left) in list(self.orders["buy"].items()):
            o = self.x.order(oid)
            if o["status"] in DONE:
                del self.orders["buy"][c]
                self._record_entry(c, strat, stop, o, t)
                self._ensure_stop(c)
            elif o["status"] in DEAD:
                del self.orders["buy"][c]
                if o["filled_size"] > 0:
                    self._record_entry(c, strat, stop, o, t)
                    self._ensure_stop(c)

    # ---------- 3. act ----------
    def act(self, t, bars, fallback_market, maker_fee, taker_fee, risk_per_trade, max_positions, min_funds_default=1.0):
        b = self.book
        blocked = b.killed_at is not None or b.day_blocked

        # move stops that the engine ratcheted up
        for c, pos in b.pos.items():
            oid = self.orders["stop"].get(c)
            if oid is None:
                continue
            placed = self.orders.setdefault("stop_px", {}).get(c)
            if placed is not None and pos.stop <= placed * (1 + 1e-9):
                continue
            self.x.cancel(oid)
            o = self.x.order(oid)
            if o["status"] in DONE:  # filled while we were moving it
                self._record_exit(c, o, "stop")
                continue
            self._ensure_stop(c)
            self.orders["stop_px"][c] = pos.stop
        for c in list(self.orders.get("stop_px", {})):
            if c not in b.pos:
                del self.orders["stop_px"][c]

        # resting buys: count down, cancel when expired or blocked
        for c, (oid, strat, stop, left) in list(self.orders["buy"].items()):
            left -= 1
            if blocked or left <= 0:
                self.x.cancel(oid)
                o = self.x.order(oid)
                del self.orders["buy"][c]
                if o["filled_size"] > 0:
                    self._record_entry(c, strat, stop, o, t)
                    self._ensure_stop(c)
                    continue
                self.log(f"CANCEL limit buy {c} ({'blocked' if blocked else 'not filled'})")
                if fallback_market and not blocked:
                    b.pending_entries.append([c, strat, stop])
            else:
                self.orders["buy"][c][3] = left

        equity = b.equity[-1][1] if b.equity else b.cash

        def size_ok(c, notional):
            p = self._p(c)
            return notional >= float(p.get("min_market_funds") or p.get("quote_min_size") or min_funds_default)

        def room():
            return not max_positions or len(b.pos) + len(self.orders["buy"]) < max_positions

        # market fallbacks (taker)
        for c, strat, stop in b.pending_entries:
            if blocked or c in b.pos or not room():
                continue
            bid, ask = self.x.best_bid_ask(f"{c}-USD")
            if ask <= stop:
                continue
            lpu = (ask - stop) + taker_fee * ask + taker_fee * stop
            quote = min(risk_per_trade * equity / lpu * ask, b.cash / (1 + taker_fee), MAX_ORDER_USD)
            quote = math.floor(quote * 100) / 100
            if not size_ok(c, quote):
                continue
            oid = self.x.create(self._coid(c, "mbuy"), f"{c}-USD", "BUY", {"market_market_ioc": {"quote_size": f"{quote:.2f}"}})
            o = self.x.order(oid)
            if o["filled_size"] > 0:
                self._record_entry(c, strat, stop, o, t)
                self._ensure_stop(c)
        b.pending_entries = []

        # new post-only limit buys from this bar's signals (maker)
        for c, strat, stop, limit, left in b.working:
            if blocked or c in b.pos or c in self.orders["buy"] or not room():
                continue
            p = self._p(c)
            bid, ask = self.x.best_bid_ask(f"{c}-USD")
            limit = floor_to(min(limit, bid), p["quote_increment"])  # post-only must not cross the ask
            if limit <= stop:
                continue
            lpu = (limit - stop) + maker_fee * limit + taker_fee * stop
            size = floor_to(min(risk_per_trade * equity / lpu, b.cash / (limit * (1 + maker_fee)),
                                MAX_ORDER_USD / limit), p["base_increment"])
            if not size_ok(c, size * limit):
                self.log(f"SKIP {c}: order ${size * limit:.2f} below Coinbase minimum")
                continue
            cfg = {"limit_limit_gtc": {"base_size": fmt(size, p["base_increment"]),
                                       "limit_price": fmt(limit, p["quote_increment"]), "post_only": True}}
            try:
                oid = self.x.create(self._coid(c, "buy"), f"{c}-USD", "BUY", cfg)
            except Exception as e:
                self.log(f"limit buy {c} rejected ({e})")
                if fallback_market:
                    b.pending_entries.append([c, strat, stop])
                continue
            self.orders["buy"][c] = [oid, strat, stop, left]
            self.log(f"LIMIT BUY placed {c} size={cfg['limit_limit_gtc']['base_size']} @ {cfg['limit_limit_gtc']['limit_price']} id={oid}")
        b.working = []

    # ---------- 4. golden rule 1 ----------
    def check_rule1(self):
        for c in list(self.book.pos):
            oid = self.orders["stop"].get(c)
            o = self.x.order(oid) if oid is not None else None
            if o is not None and o["status"] in DONE:
                self._record_exit(c, o, "stop")
            elif o is None or o["status"] in DEAD:
                self._emergency_sell(c, "no resting stop at end of run")
        return all(c in self.orders["stop"] for c in self.book.pos)
