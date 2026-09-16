from pathlib import Path

target = Path("backend/api/routes/account.py")
content = target.read_text(encoding="utf-8")

# Make sure get_positions is imported
if "get_positions" not in content:
    content = content.replace(
        "    get_account_info,\n    is_mt5_connected,",
        "    get_account_info,\n    get_positions,\n    is_mt5_connected,"
    )

# Insert open_trades_count calculation before company = getattr(...)
old_block = """        account = get_account_info()
        if account is None:
            raise RuntimeError("MT5 account information is unavailable.")"""

new_block = """        account = get_account_info()
        if account is None:
            raise RuntimeError("MT5 account information is unavailable.")

        try:
            positions = get_positions() or []
            open_trades_count = len(positions)
        except Exception:
            open_trades_count = 0"""

if old_block in content:
    content = content.replace(old_block, new_block)
    target.write_text(content, encoding="utf-8")
    print("SUCCESS: account.py patched with open_trades_count calculation!")
else:
    print("Could not locate target block in account.py")
