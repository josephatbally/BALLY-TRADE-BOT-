from pathlib import Path

target = Path("backend/api/routes/orders.py")
content = target.read_text(encoding="utf-8")

old_code = '    gate_result = pipeline_result.get("gate", {})'
new_code = '''    # Extract and unwrap final gate result
    final_gate_spec = pipeline_result.get("final_gate", {})
    gate_result = final_gate_spec.get("gate_result", final_gate_spec) if isinstance(final_gate_spec, dict) else {}'''

if old_code in content:
    content = content.replace(old_code, new_code)
    target.write_text(content, encoding="utf-8")
    print("SUCCESS: backend/api/routes/orders.py updated cleanly!")
else:
    print("Pattern not matched directly. Current gate assignment:")
    for line in content.splitlines():
        if "gate_result =" in line:
            print("  ", line)
