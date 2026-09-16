from pathlib import Path

target = Path("backend/api/routes/account.py")
content = target.read_text(encoding="utf-8")

# 1. Add get_positions to imports
old_import = """from backend.trading_engine.market_data.mt5_connection import (
    get_account_info,
    is_mt5_connected,
)"""

new_import = """from backend.trading_engine.market_data.mt5_connection import (
    get_account_info,
    get_positions,
    is_mt5_connected,
)"""

if old_import in content:
    content = content.replace(old_import, new_import)

# 2. Compute open_trades dynamically
old_block = '''        trade_mode = "DEMO" if trade_mode_val == 0 else "REAL"
        return {'''

new_block = '''        trade_mode = "DEMO" if trade_mode_val == 0 else "REAL"
        open_positions = get_positions() or []
        open_trades_count = len(open_positions)
        return {'''

if old_block in content:
    content = content.replace(old_block, new_block)

# 3. Replace hardcoded open_trades: 0 with open_trades_count
old_trades = '"open_trades": 0,'
new_trades = '"open_trades": open_trades_count,'

# Replace only the second occurrence (inside the active account dict, not the offline dict)
parts = content.split(old_trades)
if len(parts) == 3:
    content = parts[0] + old_trades + parts[1] + new_trades + parts[2]
    target.write_text(content, encoding="utf-8")
    print("SUCCESS: backend/api/routes/account.py updated!")
else:
    print(f"Occurrence count unexpected ({len(parts)-1}). Content not written.")
