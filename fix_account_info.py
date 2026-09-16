"""
Fixes AccountInfo object handling (attribute vs dict access)
in both auto_trader.py and orders.py.
"""

def extract_metric(obj, attr_name, default=0.0):
    if obj is None:
        return default
    if isinstance(obj, dict):
        return float(obj.get(attr_name, default) or default)
    return float(getattr(obj, attr_name, default) or default)

# 1. Patch orders.py
orders_path = "backend/api/routes/orders.py"
with open(orders_path, "r", encoding="utf-8") as f:
    orders_code = f.read()

orders_old = """    account = get_account_info() or {}
    balance = float(account.get("balance", 100.0) or 100.0)
    equity = float(account.get("equity", balance) or balance)"""

orders_new = """    account = get_account_info()
    balance = float(getattr(account, "balance", 100.0) if not isinstance(account, dict) else account.get("balance", 100.0) or 100.0)
    equity = float(getattr(account, "equity", balance) if not isinstance(account, dict) else account.get("equity", balance) or balance)"""

if orders_old in orders_code:
    orders_code = orders_code.replace(orders_old, orders_new)
    with open(orders_path, "w", encoding="utf-8") as f:
        f.write(orders_code)
    print("[OK] orders.py patched for AccountInfo attributes.")
else:
    print("[SKIP] orders.py snippet not matched directly.")


# 2. Patch auto_trader.py
trader_path = "backend/trading_engine/auto_trader.py"
with open(trader_path, "r", encoding="utf-8") as f:
    trader_code = f.read()

# Replace dict .get() calls on account
trader_code = trader_code.replace(
    '"balance": account.get("balance", 0.0) if account else 0.0,',
    '"balance": (getattr(account, "balance", 0.0) if not isinstance(account, dict) else account.get("balance", 0.0)) if account else 0.0,'
)
trader_code = trader_code.replace(
    '"equity": account.get("equity", 0.0) if account else 0.0,',
    '"equity": (getattr(account, "equity", 0.0) if not isinstance(account, dict) else account.get("equity", 0.0)) if account else 0.0,'
)

# Also protect inside the scan loop
trader_code = trader_code.replace(
    'bal = float(acc.get("balance", 100.0) or 100.0)',
    'bal = float(getattr(acc, "balance", 100.0) if not isinstance(acc, dict) else acc.get("balance", 100.0) or 100.0)'
)
trader_code = trader_code.replace(
    'eq = float(acc.get("equity", bal) or bal)',
    'eq = float(getattr(acc, "equity", bal) if not isinstance(acc, dict) else acc.get("equity", bal) or bal)'
)

with open(trader_path, "w", encoding="utf-8") as f:
    f.write(trader_code)
print("[OK] auto_trader.py patched for AccountInfo attributes.")
