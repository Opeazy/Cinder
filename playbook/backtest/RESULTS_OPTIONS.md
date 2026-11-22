# Fix options considered for the kill switch (before choosing max 8 open trades)

With 20 coins, many correlated positions are open at once, so drawdowns are deeper (-30% with limits off).
Two standard fixes, tested once each (more data mining on the same history, so treat with care):

| Risk/trade | Max open positions | Trades | Return | Max DD | Kill switch (-25%) |
|---|---|---|---|---|---|
| 0.5% | no cap | 302 | +4.7% | -27.8% | hit 2024-09-30 |
| 0.5% | 10 (5% max open risk) | 408 | +33.1% | -22.4% | never |
| 0.5% | 8 (4% max open risk) | 356 | +23.6% | -19.0% | never |
| 0.5% | 6 (3% max open risk) | 300 | +3.1% | -16.4% | never |
| 0.4% | no cap | 313 | +1.4% | -25.8% | hit 2024-11-06 |
| 0.3% | no cap | 516 | +19.6% | -19.9% | never |

Results jump around between neighboring settings (e.g. 6 vs 8 positions), so the exact numbers are
noisy. When the cap is full, new signals are skipped in list order (original 8 coins first).
