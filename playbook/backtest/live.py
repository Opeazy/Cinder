"""Live mode.

    python live.py                    # DRY RUN from the paper book (no key, sends nothing)
    python live.py --preview          # with your key: Coinbase checks sample orders, places NOTHING
    python live.py --live             # REAL ORDERS. Needs PLAYBOOK_GO_LIVE=yes and the key file

Key: a Coinbase CDP API key file (JSON) on the machine running the bot, path in COINBASE_KEY_FILE.
Create it with only "View" and "Trade" permissions, NEVER "Transfer". Never commit it.
Live state lives OUTSIDE the repo in PLAYBOOK_LIVE_DIR (default ~/playbook-live).

Dry run details: Translates the paper book into the exact Coinbase Advanced
Trade orders a live bot WOULD send, checks them against Coinbase's real product rules
and current prices, and writes them to ../paper/dry_run.json. It sends NOTHING and reads
no API keys.

    python live.py            # after paper.py: build + check the orders for the current book

Golden rules enforced here:
  1. No stop on the exchange, no trade: every open position must get a resting stop order,
     and a BUY is only listed together with the stop that follows it.
  3/4. The dry run never sends. Omar skipped rule 3 and said "go live" on 2026-11-22;
     real orders only via --live with PLAYBOOK_GO_LIVE=yes.

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
    raise SystemExit("The dry run never sends. Real orders go through `python live.py --live` only.")


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


# ---------------------------------------------------------------- preview / live
import os  # noqa: E402
import argparse  # noqa: E402


def _key_file():
    k = os.environ.get("COINBASE_KEY_FILE")
    if not k or not Path(k).exists():
        raise SystemExit("Set COINBASE_KEY_FILE to the path of your Coinbase CDP API key JSON file.")
    return k


def _check_perms(x):
    p = x.permissions()
    print(f"API key permissions: can_view={p.get('can_view')} can_trade={p.get('can_trade')} "
          f"can_transfer={p.get('can_transfer')} portfolio={p.get('portfolio_type')}")
    if p.get("can_transfer"):
        raise SystemExit("This key can TRANSFER (withdraw) funds. Make a new key with View + Trade only.")
    if not p.get("can_trade"):
        raise SystemExit("This key cannot trade. Make a key with View + Trade.")


def run_preview():
    from trader import CoinbaseExchange, fmt, floor_to
    x = CoinbaseExchange(_key_file())
    _check_perms(x)
    print(f"USD available: ${x.balance('USD'):.2f}   USDC available: ${x.balance('USDC'):.2f}")
    p = get("/products/BTC-USD")
    bid, ask = x.best_bid_ask("BTC-USD")
    size = fmt(floor_to(2.0 / bid, p["base_increment"]), p["base_increment"])
    q = p["quote_increment"]
    tests = {
        "post-only limit buy (entry)": ("BUY", {"limit_limit_gtc": {
            "base_size": size, "limit_price": fmt(floor_to(bid * 0.9, q), q), "post_only": True}}),
        "market buy $2 (fallback)": ("BUY", {"market_market_ioc": {"quote_size": "2.00"}}),
        "stop-limit sell (stop)": ("SELL", {"stop_limit_stop_limit_gtc": {
            "base_size": size, "limit_price": fmt(floor_to(bid * 0.8 * 0.97, q), q),
            "stop_price": fmt(floor_to(bid * 0.8, q), q), "stop_direction": "STOP_DIRECTION_STOP_DOWN"}}),
    }
    print("Previews (NOTHING is placed). A stop-limit SELL preview may report insufficient BTC; "
          "that is fine as long as the order format itself is accepted.")
    for name, (side, cfg) in tests.items():
        r = x.preview("BTC-USD", side, cfg)
        errs = r.get("errs") or []
        print(f"- {name}: {'OK' if not errs else 'ERRORS ' + str(errs)} "
              f"commission={r.get('commission_total')} warnings={r.get('warning') or []}")


def run_live():
    from config import UNIVERSE
    from engine import bar_rows
    from paper import fetch_all, last_complete_boundary, make_book
    from trader import CoinbaseExchange, LiveTrader
    import pandas as pd

    if os.environ.get("PLAYBOOK_GO_LIVE") != "yes":
        raise SystemExit("Refusing: set PLAYBOOK_GO_LIVE=yes to place real orders.")
    x = CoinbaseExchange(_key_file())
    _check_perms(x)
    ldir = Path(os.environ.get("PLAYBOOK_LIVE_DIR", Path.home() / "playbook-live"))
    ldir.mkdir(parents=True, exist_ok=True)
    sfile, lfile = ldir / "state.json", ldir / "live.log"

    def log(msg):
        line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}"
        print(line)
        with open(lfile, "a") as f:
            f.write(line + "\n")

    if sfile.exists():
        st = json.loads(sfile.read_text())
        book = make_book().load_dict(st["book"])
        orders = st["orders"]
    else:
        usd = x.balance("USD")
        capital = min(usd, Risk().capital)
        if capital < 5:
            raise SystemExit(f"Only ${usd:.2f} USD available. Fund the account with USD first.")
        book, orders = make_book(), {}
        book.cash = book.eq_high = book.day_start_eq = capital
        book.equity = [[datetime.now(timezone.utc).isoformat(), capital]]
        log(f"START live book with ${capital:.2f} (USD available ${usd:.2f}, cap ${Risk().capital:.0f})")

    products = {c: get(f"/products/{c}-USD") for c in UNIVERSE}
    end = last_complete_boundary(datetime.now(timezone.utc))
    data, usable_end = fetch_all(end)
    t_latest = (usable_end - pd.Timedelta(hours=4)).isoformat()
    costs, risk = Costs(), Risk()
    tr = LiveTrader(book, orders, x, products, log, taker_fee=costs.fee)

    tr.sync(t_latest)
    if book.last_bar is None or t_latest > book.last_bar:
        rows = dict(bar_rows(data, start=pd.Timestamp(t_latest), end=usable_end))
        bars = rows[t_latest]
        if book.last_bar and pd.Timestamp(t_latest) - pd.Timestamp(book.last_bar) > pd.Timedelta(hours=4):
            log(f"WARNING missed bars since {book.last_bar}; acting on the latest only")
        n_ev = len(book.events)
        book.begin_bar(t_latest, bars)
        book.decide_phase(t_latest, bars)
        for e in book.events[n_ev:]:
            log(e)
        tr.act(t_latest, bars, CHOSEN_ENTRY.fallback_market, costs.maker_fee, costs.fee,
               risk.risk_per_trade, risk.max_positions)
    ok = tr.check_rule1()
    usd = x.balance("USD")
    if usd + 0.5 < book.cash:
        log(f"WARNING Coinbase USD ${usd:.2f} is below the bot's cash ${book.cash:.2f}")
    sfile.write_text(json.dumps({"book": book.to_dict(), "orders": orders}, indent=1))
    eq = book.equity[-1][1] if book.equity else book.cash
    log(f"RUN DONE bar={book.last_bar} equity=${eq:.2f} cash=${book.cash:.2f} positions={list(book.pos)} "
        f"resting_buys={list(orders.get('buy', {}))} rule1={'OK' if ok else 'FAIL'} "
        f"kill={'HIT' if book.killed_at else 'ok'} trades={len(book.trades)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    if a.preview:
        run_preview()
    elif a.live:
        run_live()
    else:
        main()
