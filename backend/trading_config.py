"""
BALLY FLOW - Trading Engine Configuration
"""

# Live Execution Switch
AUTO_TRADING_ENABLED: bool = False

# Risk & Position Limits
MAX_OPEN_POSITIONS: int = 3
MAX_RISK_PER_TRADE_PERCENT: float = 1.0
DEFAULT_LOT_SIZE: float = 0.01

DEFAULT_SL_POINTS: int = 250
DEFAULT_TP_POINTS: int = 500
MAX_DEVIATION_POINTS: int = 20
