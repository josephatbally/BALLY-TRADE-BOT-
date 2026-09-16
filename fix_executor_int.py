from pathlib import Path
import re

target = Path("backend/trading_engine/execution/live_executor.py")
content = target.read_text(encoding="utf-8")

# Replace direct int(order.get(...)) with safe defaults
old_deviation_pattern = r'"deviation":\s*int\(\s*order\.get\(\s*["\']deviation["\'],?\s*([^\)]*)\s*\)\s*\)'
new_deviation = '"deviation": int(order.get("deviation") or 20)'

old_magic_pattern = r'"magic":\s*int\(\s*order\.get\(\s*["\']magic_number["\'],?\s*([^\)]*)\s*\)\s*\)'
new_magic = '"magic": int(order.get("magic_number") or 100001)'

c1, n1 = re.subn(old_deviation_pattern, new_deviation, content)
c2, n2 = re.subn(old_magic_pattern, new_magic, c1)

if n1 > 0 or n2 > 0:
    target.write_text(c2, encoding="utf-8")
    print(f"SUCCESS: live_executor.py patched! (deviation fixes: {n1}, magic fixes: {n2})")
else:
    print("Regex did not match directly. Showing lines around deviation in live_executor.py:")
    lines = content.splitlines()
    for idx, l in enumerate(lines):
        if "deviation" in l or "magic" in l:
            if idx > 400 and idx < 550:
                print(f"{idx+1}: {l}")
