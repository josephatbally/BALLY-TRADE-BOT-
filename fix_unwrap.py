from pathlib import Path

target = Path("backend/api/routes/orders.py")
content = target.read_text(encoding="utf-8")

old_code = """    builder_result = pipeline_result.get("order_builder", {})
    order_dict = (
        builder_result.get("order")
        or builder_result.get("built_order")
        or trade_plan
    )"""

new_code = """    builder_result = pipeline_result.get("order_builder", {})
    order_dict = (
        builder_result.get("order")
        or builder_result.get("built_order")
        or trade_plan
    )

    # Unwrap nested order dictionaries until top-level holds the actual order attributes
    while isinstance(order_dict, dict) and "order" in order_dict and isinstance(order_dict["order"], dict):
        order_dict = order_dict["order"]"""

if old_code in content:
    content = content.replace(old_code, new_code)
    target.write_text(content, encoding="utf-8")
    print("SUCCESS: backend/api/routes/orders.py updated cleanly!")
else:
    print("MATCH FAILED: Checking lines around order_dict...")
    for idx, line in enumerate(content.splitlines()):
        if "builder_result" in line or "order_dict" in line:
            print(f"{idx+1}: {line}")
