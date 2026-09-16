"""Patch execution_pipeline.py to delegate authorized orders to live_executor."""
from pathlib import Path

target = Path("backend/trading_engine/execution/execution_pipeline.py")
if not target.exists():
    print("[ERR] File not found:", target)
    exit(1)

content = target.read_text(encoding="utf-8")

needle = "result = execute_order(\n            approved_order,\n        )"
replacement = (
    "result = execute_order(\n"
    "            approved_order,\n"
    "            gate=gate_result,\n"
    "            delegate=True,\n"
    "        )"
)

if "delegate=True" in content:
    print("[SKIP] delegate=True already present.")
elif needle in content:
    content = content.replace(needle, replacement, 1)
    target.write_text(content, encoding="utf-8")
    print("[OK] _run_executor now delegates authorized orders to live_executor.")
else:
    print("[WARN] Insertion point not found - paste the _run_executor body here.")

# Sanity check the module still compiles
import py_compile
py_compile.compile(str(target), doraise=True)
print("[OK] execution_pipeline.py compiles cleanly.")
