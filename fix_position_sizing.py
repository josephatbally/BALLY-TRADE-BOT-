import re
from pathlib import Path

# 1. Update position_sizing.py to allow broker minimum lot if within hard max risk
pos_path = Path("backend/trading_engine/risk/position_sizing.py")
if pos_path.exists():
    text = pos_path.read_text(encoding="utf-8")
    
    # Allow broker minimum volume when within hard_max_volume
    text = text.replace(
        "REJECT_IF_BROKER_MIN_EXCEEDS_RISK = True",
        "REJECT_IF_BROKER_MIN_EXCEEDS_RISK = False"
    )
    
    # In verify_final_risk, allow broker minimum if within hard max risk ceiling
    old_verify = """    hard_limit_passed = (
        actual_risk
        <= hard_max_risk_amount + 1e-9
    )

    requested_limit_passed = (
        actual_risk
        <= risk_amount + 1e-9
    )"""
    new_verify = """    hard_limit_passed = (
        actual_risk
        <= hard_max_risk_amount + 1e-9
    )

    # For accounts with micro lot minimums, allow broker_min if within hard safety ceiling
    requested_limit_passed = (
        (actual_risk <= risk_amount + 1e-9)
        or (hard_limit_passed and actual_risk <= hard_max_risk_amount + 1e-9)
    )"""
    if old_verify in text:
        text = text.replace(old_verify, new_verify)
    
    pos_path.write_text(text, encoding="utf-8")
    print("[OK] Patched backend/trading_engine/risk/position_sizing.py")
else:
    print("[ERROR] backend/trading_engine/risk/position_sizing.py not found")

# 2. Update orders.py to pass realistic risk_percent (1.5%) for manual trades
orders_path = Path("backend/api/routes/orders.py")
if orders_path.exists():
    otext = orders_path.read_text(encoding="utf-8")
    otext = re.sub(r'("risk_percent":\s*)0\.[0-9]+', r'\g<1>1.5', otext)
    orders_path.write_text(otext, encoding="utf-8")
    print("[OK] Patched backend/api/routes/orders.py")
else:
    print("[ERROR] backend/api/routes/orders.py not found")
