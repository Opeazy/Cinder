"""Download Coinbase spot candles (public, no key) and build 4-hour bars.

Coinbase Exchange has no 4h granularity, so 1h candles are fetched and
resampled to 4h bars aligned to UTC 00/04/08/12/16/20.

Usage: python fetch.py [--start 2022-01-01] [--coins BTC,ETH,...]
"""
import argparse
import json
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from config import DATA_DIR, UNIVERSE

API = "https://api.exchange.coinbase.com"
HOUR = 3600
MAX_CANDLES = 300  # Coinbase limit per request


def _get(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "backtest-client"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:  # rate limit / transient
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))


def product_info(product):
    return _get(f"{API}/products/{product}")


def fetch_hourly(product, start, end):
    rows = []
    t = start
    while t < end:
        t2 = min(t + timedelta(seconds=HOUR * MAX_CANDLES), end)
        url = (f"{API}/products/{product}/candles?granularity={HOUR}"
               f"&start={t.isoformat()}&end={t2.isoformat()}")
        data = _get(url)
        rows.extend(data)
        t = t2
        time.sleep(0.15)
    df = pd.DataFrame(rows, columns=["time", "low", "high", "open", "close", "volume"])
    df = df.drop_duplicates("time").sort_values("time")
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.set_index("time")
    # Drop hours whose candle starts at or after `end` (incomplete)
    return df[df.index < end]


def to_4h(h):
    agg = h.resample("4h", origin="epoch", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    return agg.dropna(subset=["open"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2022-01-01")
    ap.add_argument("--coins", default=",".join(UNIVERSE))
    args = ap.parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    end = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=now.hour % 4)  # last complete 4h boundary
    pj = DATA_DIR / "products.json"
    meta = json.loads(pj.read_text()) if pj.exists() else {}
    for coin in args.coins.split(","):
        product = f"{coin}-USD"
        info = product_info(product)
        meta[coin] = {k: info[k] for k in ("base_increment", "quote_increment", "min_market_funds")}
        h = fetch_hourly(product, start, end)
        bars = to_4h(h)
        bars.to_csv(DATA_DIR / f"{coin}-USD_4h.csv")
        print(f"{product}: {len(h)} 1h -> {len(bars)} 4h bars, {bars.index[0]} .. {bars.index[-1]}", flush=True)
    pj.write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
