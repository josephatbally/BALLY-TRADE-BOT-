"""Patch final_gate.py to recognize risk_authorized from risk_manager."""
import re
from pathlib import Path

target = Path("backend/trading_engine/execution/final_gate.py")
if not target.exists():
    print(f"[ERR] File not found: {target}")
    exit(1)

content = target.read_text(encoding="utf-8")

old_code = """        # Accept common authorization field names.
        approved = risk.get("approved")

        if approved is None:
            approved = risk.get("risk_approved")

        if approved is None:
            approved = risk.get("trade_allowed")

        if approved is None:
            approved = risk.get("allowed")"""

new_code = """        # Accept common authorization field names.
        approved = risk.get("risk_authorized")

        if approved is None:
            approved = risk.get("approved")

        if approved is None:
            approved = risk.get("risk_approved")

        if approved is None:
            approved = risk.get("trade_allowed")

        if approved is None:
            approved = risk.get("allowed")"""

if old_code in content:
    content = content.replace(old_code, new_code)
    target.write_text(content, encoding="utf-8")
    print("[OK] final_gate.py successfully patched to accept 'risk_authorized'.")
else:
    # Fallback regex if formatting differs slightly
    pattern = r'approved\s*=\s*risk\.get\("approved"\)'
    replacement = 'approved = risk.get("risk_authorized")\n        if approved is None:\n            approved = risk.get("approved")'
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content, count=1)
        target.write_text(content, encoding="utf-8")
        print("[OK] final_gate.py patched via regex.")
    else:
        print("[WARN] Could not find insertion point. Please inspect _check_risk in final_gate.py.")
