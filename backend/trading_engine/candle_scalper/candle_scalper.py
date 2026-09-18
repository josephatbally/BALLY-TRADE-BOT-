"""
BALLY FLOW - Candle Momentum Scalper Engine
"""
import logging, MetaTrader5 as mt5
logger = logging.getLogger("CandleScalper")

def get_tiered_lot_size(balance: float) -> float:
    b = max(0.0, float(balance))
    if b < 500: return 0.01
    elif b < 1000: return 0.05
    elif b < 2000: return 0.10
    elif b < 5000: return 0.50
    elif b < 10000: return 1.00
    elif b < 20000: return 2.00
    elif b < 50000: return 5.00
    else: return 10.00

def analyze_candle_momentum(symbol: str):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 5)
    if rates is None or len(rates) < 2:
        return {"signal": "HOLD", "confidence": 0}
    current = rates[-1]
    delta = float(current["close"]) - float(current["open"])
    body = abs(delta)
    total_range = max(float(current["high"]) - float(current["low"]), 1e-6)
    if delta > 0 and (body / total_range) > 0.55:
        return {"signal": "BUY", "confidence": 80, "burst_count": 3, "profit_target_usd": 2.50}
    elif delta < 0 and (body / total_range) > 0.55:
        return {"signal": "SELL", "confidence": 80, "burst_count": 3, "profit_target_usd": 2.50}
    return {"signal": "HOLD", "confidence": 40}
