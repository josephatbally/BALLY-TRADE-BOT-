from pathlib import Path

orders_path = Path("backend/api/routes/orders.py")
if not orders_path.exists():
    print("[ERROR] backend/api/routes/orders.py not found")
    exit(1)

content = orders_path.read_text(encoding="utf-8")

# Ensure trade_plan and live_order have 'volume' explicitly populated
if '"volume":' not in content:
    content = content.replace(
        '"lot_size": lot_size,',
        '"lot_size": lot_size,\n        "volume": lot_size,'
    )

# When calling execute_live_trade, extract the full authorized order from pipeline or fallback to order with volume
patch_search = 'live_result = execute_live_trade('
if patch_search in content:
    # Make sure whatever dictionary is passed into execute_live_trade has volume = lot_size
    replacement = """# Extract authorized order from pipeline if available, ensuring volume is set
        live_order = None
        if isinstance(pipeline_result, dict):
            live_order = (
                pipeline_result.get("executor", {}).get("executor_result", {}).get("order")
                or pipeline_result.get("order", {}).get("order")
                or pipeline_result.get("order")
            )
        if not live_order or not isinstance(live_order, dict) or not live_order.get("volume"):
            live_order = {
                "symbol": symbol,
                "decision": action,
                "order_type": action,
                "volume": lot_size,
                "entry": entry_price,
                "stop_loss": structural_stop,
                "take_profit": structural_tp,
            }
        else:
            live_order["volume"] = float(live_order.get("volume") or lot_size)

        live_result = execute_live_trade(
            order=live_order,
            gate=pipeline_result.get("final_gate", {}).get("gate_result", pipeline_result.get("final_gate"))
        )"""
    
    # Replace standard call block
    import re
    content = re.sub(
        r'live_result\s*=\s*execute_live_trade\([^)]+\)',
        replacement,
        content
    )

orders_path.write_text(content, encoding="utf-8")
print("[OK] backend/api/routes/orders.py patched with volume forwarding.")
