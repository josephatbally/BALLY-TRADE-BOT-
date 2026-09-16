"""
Fix manual order risk context and auto-trader background loop triggering.
"""
import re

# 1. Patch backend/api/routes/orders.py
orders_path = "backend/api/routes/orders.py"
print(f"Patching {orders_path}...")

with open(orders_path, "r", encoding="utf-8") as f:
    orders_code = f.read()

# Make sure get_account_info is imported
if "get_account_info" not in orders_code:
    orders_code = orders_code.replace(
        "from backend.trading_engine.market_data.mt5_connection import is_mt5_connected",
        "from backend.trading_engine.market_data.mt5_connection import is_mt5_connected, get_account_info"
    )

# Inject live account balance & equity into risk_context
target_pipeline_call = """    account = get_account_info() or {}
    balance = float(account.get("balance", 100.0) or 100.0)
    equity = float(account.get("equity", balance) or balance)

    risk_context = {
        "account_balance": balance,
        "account_equity": equity,
        "starting_balance": balance,
        "starting_day_balance": balance,
        "base_risk_percent": 1.0,
        "preferred_lot": req.lot_size or 0.01,
    }

    pipeline_result = execute_trade_pipeline(
        trade_plan,
        risk_context=risk_context,
        execute_live=True,
        reject_existing_position=False,
    )"""

# Replace the pipeline execution in orders.py
orders_code = re.sub(
    r"pipeline_result = execute_trade_pipeline\([^)]+\)",
    target_pipeline_call.strip(),
    orders_code,
    flags=re.DOTALL
)

with open(orders_path, "w", encoding="utf-8") as f:
    f.write(orders_code)
print(f"[OK] Patched {orders_path}")


# 2. Patch backend/trading_engine/auto_trader.py
trader_path = "backend/trading_engine/auto_trader.py"
print(f"Patching {trader_path}...")

with open(trader_path, "r", encoding="utf-8") as f:
    trader_code = f.read()

# Ensure set_enabled actively starts the asyncio loop if event loop is running
new_toggle_logic = """    def set_enabled(self, val: bool):
        self.enabled = bool(val)
        level = "SUCCESS" if self.enabled else "WARNING"
        self._add_log(level, f"Auto-trading set to {self.enabled}")
        if self.enabled and (not self.running or self._task is None or self._task.done()):
            try:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(self._run_loop())
                self.running = True
                self._add_log("INFO", "Auto-trader background scanner loop launched.")
            except RuntimeError:
                pass
        return self.enabled

    def toggle(self):
        return self.set_enabled(not self.enabled)"""

trader_code = re.sub(
    r"def set_enabled\(self, val: bool\):.*?return self\.enabled\s+def toggle\(self\):.*?return self\.set_enabled\(not self\.enabled\)",
    new_toggle_logic,
    trader_code,
    flags=re.DOTALL
)

with open(trader_path, "w", encoding="utf-8") as f:
    f.write(trader_code)
print(f"[OK] Patched {trader_path}")
