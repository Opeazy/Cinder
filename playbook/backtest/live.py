"""Live mode, DRY RUN ONLY. Translates the paper book into the exact Coinbase Advanced
Trade orders a live bot WOULD send, checks them against Coinbase's real product rules
and current prices, and writes them to ../paper/dry_run.json. It sends NOTHING and reads
no API keys.

    python live.py            # after paper.py: build + check the orders for the current book

Golden rules enforced here:
  1. No stop on the exchange, no trade: every open position must get a resting stop order,
     and a BUY is only listed together with the stop that follows it.
  3/4. Sending is not implemented. `send()` always refuses. Going live needs 30+ matching
     paper trades AND Omar's "go live", then a separate build + test.

Order formats follow the Advanced Trade API (POST /api/v3/brokerage/orders). Two details are
not confirmed from the official docs yet and MUST be checked with POST /orders/preview
before any live use: the placement of "post_only" and the exact "stop_direction" value.
Spot has stop-LIMIT orders only (no plain stop-market), so the stop's limit is set
STOP_LIMIT_BUFFER below the trigger; a crash through both inside a few seconds could
leave the stop unfilled. In the backtest no stop exit opened more than 0.05% below its stop.
"""
import json
import math
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from config import CHOSEN, CHOSEN_ENTRY, Costs, Risk
from paper import DIR, STATE, load

MODE = "DRY_RUN"
API = "https://api.exchange.coinbase.com"  # public product + ticker data (no key)
ORDERS_ENDPOINT = "POST https://api.coinbase.com/api/v3/brokerage/orders"
STOP_LIMIT_BUFFER = 0.03  # stop-limit sell: limit 3% below the stop trigger, so it fills in a fast drop


def send(order):
    raise SystemExit("Live sending is not implemented. Needs 30+ matching paper trades and Omar's 'go live'.")


def get(path):
    req = urllib.request.Request(API + path, headers={"User-Agent": "backtest-client"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception:
            if i == 3:
                raise
            time.sleep(2 * (i + 1))


def floor_to(x, inc):
    inc = float(inc)
    return math.floor(x / inc + 1e-9) * inc


def fmt(x, inc):
    decimals = max(0, -int(math.floor(math.log10(float(inc)))))
    return f"{x:.{decimals}f}"


def coid(*parts):
    return "playbook-" + "-".join(str(p) for p in parts)


def main():
    if MODE != "DRY_RUN":
        raise SystemExit("Only DRY_RUN exists.")
    book, meta = load()
    costs, risk = Costs(), Risk()
    coins = set(book.pos) | {o[0] for o in book.working} | {o[0] for o in book.pending_entries}
    info = {c: get(f"/products/{c}-USD") for c in coins}
    tick = {c: get(f"/products/{c}-USD/ticker") for c in coins}
    equity = book.equity[-1][1] if book.equity else book.cash
    orders, problems = [], []

    def check_product(c):
        p = info[c]
        if p.get("status") != "online" or p.get("trading_disabled") or p.get("cancel_only"):
            problems.append(f"{c}-USD not tradable now: status={p.get('status')}, cancel_only={p.get('cancel_only')}")
        return p

    # 1. A resting stop for every open position (golden rule 1)
    for c, pos in book.pos.items():
        p = check_product(c)
        size = floor_to(pos.qty, p["base_increment"])
        stop = floor_to(pos.stop, p["quote_increment"])
        limit = floor_to(pos.stop * (1 - STOP_LIMIT_BUFFER), p["quote_increment"])
        price = float(tick[c]["price"])
        if size <= 0:
            problems.append(f"{c}: position too small to place a stop at base_increment {p['base_increment']}")
        if price <= stop:
            problems.append(f"{c}: price {price} is already at/below the stop {stop}: a live bot would sell now")
        orders.append({"why": f"resting stop for open {c} position (entered {pos.entry_time})",
                       "endpoint": ORDERS_ENDPOINT,
                       "body": {"client_order_id": coid(c, "stop", pos.entry_time[:13]), "product_id": f"{c}-USD",
                                "side": "SELL",
                                "order_configuration": {"stop_limit_stop_limit_gtc": {
                                    "base_size": fmt(size, p["base_increment"]),
                                    "limit_price": fmt(limit, p["quote_increment"]),
                                    "stop_price": fmt(stop, p["quote_increment"]),
                                    "stop_direction": "STOP_DIRECTION_STOP_DOWN"}}}})

    # 2. Resting limit buys (maker), each followed by its stop once filled
    for c, strat, stop, limit_px, left in book.working:
        p = check_product(c)
        limit = floor_to(limit_px, p["quote_increment"])
        lpu = (limit - stop * (1 - costs.slippage)) + costs.maker_fee * limit + costs.fee * stop
        size = floor_to(min(risk.risk_per_trade * equity / lpu, book.cash / (limit * (1 + costs.maker_fee))),
                        p["base_increment"])
        notional = size * limit
        ask = float(tick[c]["ask"])
        if notional < float(p["min_market_funds"]):
            problems.append(f"{c}: limit buy ${notional:.2f} is below Coinbase minimum ${p['min_market_funds']}")
        if limit >= ask:
            problems.append(f"{c}: post-only limit {limit} >= ask {ask} would be rejected; "
                            f"{'market fallback next bar' if CHOSEN_ENTRY.fallback_market else 'skip'}")
        orders.append({"why": f"{strat} entry, maker limit buy good for {left} more bar(s); "
                              f"after fill place a stop-limit sell at {stop:.6g}",
                       "endpoint": ORDERS_ENDPOINT,
                       "body": {"client_order_id": coid(c, "buy", book.last_bar[:13]), "product_id": f"{c}-USD",
                                "side": "BUY",
                                "order_configuration": {"limit_limit_gtc": {
                                    "base_size": fmt(size, p["base_increment"]),
                                    "limit_price": fmt(limit, p["quote_increment"]),
                                    "post_only": True}}},  # VERIFY placement with /orders/preview
                       "est_notional_usd": round(notional, 2)})

    # 3. Market buys queued for the next open (fallbacks)
    for c, strat, stop in book.pending_entries:
        p = check_product(c)
        ask = float(tick[c]["ask"])
        lpu = (ask * (1 + costs.slippage) - stop) + costs.fee * ask + costs.fee * stop
        quote = min(risk.risk_per_trade * equity / lpu * ask, book.cash / (1 + costs.fee))
        quote = math.floor(quote * 100) / 100
        if quote < float(p["min_market_funds"]):
            problems.append(f"{c}: market buy ${quote:.2f} is below Coinbase minimum ${p['min_market_funds']}")
        orders.append({"why": f"{strat} entry, market buy at the open (taker); then stop-limit sell at {stop:.6g}",
                       "endpoint": ORDERS_ENDPOINT,
                       "body": {"client_order_id": coid(c, "mbuy", book.last_bar[:13]), "product_id": f"{c}-USD",
                                "side": "BUY",
                                "order_configuration": {"market_market_ioc": {"quote_size": f"{quote:.2f}"}}}})

    stops = sum(1 for o in orders if o["body"]["side"] == "SELL")
    rule1 = stops == len(book.pos)
    out = {"mode": MODE, "made_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "paper_last_bar": book.last_bar, "equity": round(equity, 2), "open_positions": len(book.pos),
           "rule1_every_position_has_stop": rule1, "problems": problems, "orders": orders}
    DIR.mkdir(exist_ok=True)
    (DIR / "dry_run.json").write_text(json.dumps(out, indent=1))
    line = (f"{out['made_at']} DRY RUN bar={book.last_bar} equity=${equity:.2f} positions={len(book.pos)} "
            f"orders={len(orders)} rule1={'OK' if rule1 else 'FAIL'} problems={len(problems)}")
    with open(DIR / "dry_run.log", "a") as f:
        f.write(line + "\n" + "".join(f"  PROBLEM {p}\n" for p in problems))
    print(line)
    for p in problems:
        print("  PROBLEM", p)
    for o in orders:
        print(f"  WOULD SEND: {o['why']}\n    {json.dumps(o['body'])}")
    if not orders:
        print("  Nothing to send: no open positions and no orders pending.")


if __name__ == "__main__":
    main()
