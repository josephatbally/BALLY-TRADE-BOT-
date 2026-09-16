"""
Wire live MT5 execution directly into AutoTrader scan loop.
"""

path = "backend/trading_engine/auto_trader.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Ensure execute_live_trade is imported
if "execute_live_trade" not in code:
    code = code.replace(
        "from backend.trading_engine.execution.live_executor import close_position",
        "from backend.trading_engine.execution.live_executor import close_position, execute_live_trade",
    )

# 2. Locate the pipeline call and attach the live execution dispatch
target = 'res = execute_trade_pipeline('
idx = code.find(target)
if idx != -1:
    # Find start of line for indentation
    line_start = code.rfind("\n", 0, idx) + 1
    indent = code[line_start:idx]
    
    # Find the end of this block
    old_block_end = code.find('break', idx)
    next_line = code.find('\n', old_block_end) + 1
    
    new_block = (
        f"{indent}res = execute_trade_pipeline(\n"
        f"{indent}    trade_plan,\n"
        f"{indent}    risk_context=risk_ctx,\n"
        f"{indent}    execute_live=True,\n"
        f"{indent}    reject_existing_position=True,\n"
        f"{indent})\n"
        f"{indent}if res.get('execution_allowed') or res.get('status') == 'READY':\n"
        f"{indent}    final_gate = res.get('final_gate', {{}})\n"
        f"{indent}    gate_result = final_gate.get('gate_result', final_gate) if isinstance(final_gate, dict) else {{}}\n"
        f"{indent}    builder_res = res.get('order_builder', {{}})\n"
        f"{indent}    order_payload = builder_res.get('order') or builder_res.get('built_order') or trade_plan\n"
        f"{indent}    while isinstance(order_payload, dict) and 'order' in order_payload and isinstance(order_payload['order'], dict):\n"
        f"{indent}        order_payload = order_payload['order']\n"
        f"{indent}    live_res = execute_live_trade(order=order_payload, gate=gate_result)\n"
        f"{indent}    if live_res.get('status') in ('EXECUTED', 'SUCCESS') or live_res.get('order_sent'):\n"
        f"{indent}        ticket = live_res.get('ticket') or live_res.get('order')\n"
        f"{indent}        self._add_log('SUCCESS', f'Auto-trade executed on MT5: {{action}} {{symbol}} (#{{ticket}})')\n"
        f"{indent}        break\n"
        f"{indent}    else:\n"
        f"{indent}        self._add_log('WARNING', f'Auto-trade MT5 rejected: {{live_res.get(\"reason\")}}')\n"
    )
    
    code = code[:line_start] + new_block + code[next_line:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print("SUCCESS: AutoTrader is now fully connected to MT5 live execution.")
else:
    print("ERROR: Target execution block not found.")
