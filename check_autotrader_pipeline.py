"""
Diagnostic: Initialize MT5 and check why AutoTrader's trade plan blocked.
"""
from backend.trading_engine.market_data.mt5_connection import (
    initialize,
    ensure_connected,
    get_account_info,
    get_symbol_tick,
    get_symbol_info,
)
from backend.trading_engine.execution.execution_pipeline import execute_trade_pipeline
import json

# 1. Initialize MT5
connected = initialize() or ensure_connected()
print("MT5 Connected:", connected)

sym = "USDJPY"
action = "BUY"
tick = get_symbol_tick(sym)
price = getattr(tick, "ask", None) if tick else None
print(f"Live {sym} Ask Price:", price)

acc = get_account_info()
bal = getattr(acc, "balance", 100.0) if acc else 100.0
eq = getattr(acc, "equity", bal) if acc else bal
info = get_symbol_info(sym)

# What AutoTrader currently sends:
trade_plan = {
    "symbol": sym,
    "decision": action,
    "signal": action,
    "entry": float(price or 150.0),
    "entry_price": float(price or 150.0),
    "opportunity_score": 75.2,
}

risk_ctx = {
    "account_balance": bal,
    "account_equity": eq,
    "starting_balance": bal,
    "starting_day_balance": bal,
    "base_risk_percent": 1.0,
    "preferred_lot": 0.01,
    "symbol_info": info,
}

res = execute_trade_pipeline(
    trade_plan,
    symbol_info=info,
    risk_context=risk_ctx,
    execute_live=True,
    reject_existing_position=False,
)

print("\n--- Pipeline Result ---")
print("Status:", res.get("status"))
print("Reason:", res.get("reason"))
print("Stage where it failed:", res.get("stage"))

for stage_name in ("risk", "bridge", "position", "final_gate", "order_builder", "executor"):
    if stage_name in res:
        stage_data = res[stage_name]
        status = stage_data.get("status") if isinstance(stage_data, dict) else stage_data
        reason = stage_data.get("reason") if isinstance(stage_data, dict) else ""
        print(f" - {stage_name}: {status} ({reason})")
