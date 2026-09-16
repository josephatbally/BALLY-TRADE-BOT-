"""Patch executor.py to accept both flat orders and order_builder container dicts."""
from pathlib import Path

target = Path("backend/trading_engine/execution/executor.py")
if not target.exists():
    print("[ERR] File not found:", target)
    exit(1)

content = target.read_text(encoding="utf-8")

# Unwrap point 1: inside _validate_order
needle_1 = 'return "order must be a dictionary"'
unwrap_1 = (
    'return "order must be a dictionary"\n'
    '\n'
    '        # Unwrap if order_builder returned an order container\n'
    '        if "order" in order and isinstance(order["order"], dict) and "order_type" in order["order"]:\n'
    '            order = order["order"]'
)

if 'order_type" in order["order"]' not in content:
    if needle_1 not in content:
        print("[WARN] Could not find _validate_order insertion point.")
        exit(1)
    content = content.replace(needle_1, unwrap_1, 1)
    print("[OK] _validate_order patched.")

# Unwrap point 2: inside execute(), before validation runs
needle_2 = "error = self._validate_order(order)"
unwrap_2 = (
    '# Unwrap container dictionary if present\n'
    '        if isinstance(order, dict) and "order" in order and isinstance(order["order"], dict) and "order_type" in order["order"]:\n'
    '            order = order["order"]\n'
    '\n'
    '        error = self._validate_order(order)'
)

if "isinstance(order, dict) and \"order\" in order" not in content:
    if needle_2 not in content:
        print("[WARN] Could not find execute() insertion point.")
        exit(1)
    content = content.replace(needle_2, unwrap_2, 1)
    print("[OK] execute() patched.")

target.write_text(content, encoding="utf-8")
print("[OK] executor.py saved with order container unwrapping.")
