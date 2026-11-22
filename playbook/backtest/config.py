"""Playbook parameters. Edit here, not in the engine."""
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# DRAFT universe: large, liquid Coinbase USD spot pairs (fixed list -> survivorship bias, see README).
UNIVERSE = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA", "LINK", "AVAX"]


@dataclass
class Costs:
    fee: float = 0.005        # 0.50% per side (Omar's Coinbase tier)
    slippage: float = 0.0005  # 0.05% per side, assumed for market/stop fills
    min_notional: float = 1.0  # Coinbase min_market_funds for USD pairs


@dataclass
class Risk:
    capital: float = 100.0
    risk_per_trade: float = 0.01   # 1% of equity, fees included in the risk
    daily_loss_limit: float = 0.03  # vs equity at UTC day start -> no new entries until next UTC day
    kill_switch: float = 0.15       # drawdown from equity high -> stop all, keep stops


@dataclass
class TrendParams:
    regime_ema: int = 200     # only long above the 200-bar EMA (~33 days)
    breakout: int = 20        # close above prior 20-bar high (~3.3 days)
    atr: int = 14
    init_stop_atr: float = 3.0
    trail_atr: float = 3.0    # chandelier: highest high since entry - 3 ATR


@dataclass
class MeanRevParams:
    regime_ema: int = 200     # only buy dips in an uptrend
    rsi: int = 3
    rsi_entry: float = 15.0   # RSI(3) < 15
    exit_sma: int = 20        # exit at next open after close > SMA(20)
    atr: int = 14
    stop_atr: float = 3.0
    max_bars: int = 18        # time stop: 3 days
