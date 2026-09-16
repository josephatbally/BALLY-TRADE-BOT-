"""
Give AutoTrader the complete trade plan structure (SL, TP, market context, symbol info)
and log any pipeline blocks to telemetry.
"""

path = "backend/trading_engine/auto_trader.py"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Ensure get_symbol_info and execute_live_trade are imported
if "get_symbol_info" not in code:
    code = code.replace(
        "    get_symbol_tick,\n",
        "    get_symbol_tick,\n    get_symbol_info,\n",
    )

if "execute_live_trade" not in code:
    code = code.replace(
        "from backend.trading_engine.execution.live_executor import close_position",
        "from backend.trading_engine.execution.live_executor import close_position, execute_live_trade",
    )

# 2. Replace the signal evaluation block with complete trade plan construction
old_block_start = 'if action in ["BUY", "SELL"] and confidence >= self.min_confidence:'
start_idx = code.find(old_block_start)

if start_idx != -1:
    end_idx = code.find('except Exception as scan_err:', start_idx)
    
    new_block = '''if action in ["BUY", "SELL"] and confidence >= self.min_confidence:
                                self._add_log("INFO", f"Signal found: {action} {symbol} ({confidence:.1f}%)")
                                tick = get_symbol_tick(symbol)
                                if not tick:
                                    self._add_log("WARNING", f"No tick data for {symbol}")
                                    continue
                                
                                bid = getattr(tick, "bid", None) or (tick.get("bid") if isinstance(tick, dict) else None)
                                ask = getattr(tick, "ask", None) or (tick.get("ask") if isinstance(tick, dict) else None)
                                price = float(ask if action == "BUY" else bid)
                                
                                sym_info = get_symbol_info(symbol)
                                point = getattr(sym_info, "point", 0.0001) or 0.0001
                                digits = getattr(sym_info, "digits", 5) or 5
                                
                                sym_upper = symbol.upper()
                                if "XAU" in sym_upper or "GOLD" in sym_upper:
                                    stop_dist = 2.50
                                elif "XAG" in sym_upper or "SILVER" in sym_upper:
                                    stop_dist = 0.35
                                elif "JPY" in sym_upper:
                                    stop_dist = 0.35
                                elif "NAS" in sym_upper or "US100" in sym_upper or "100" in sym_upper:
                                    stop_dist = 25.0
                                else:
                                    stop_dist = max(250.0 * point, 0.0025)
                                
                                sl = round(price - stop_dist if action == "BUY" else price + stop_dist, digits)
                                tp = round(price + (stop_dist * 3.0) if action == "BUY" else price - (stop_dist * 3.0), digits)
                                
                                high_target = round(price + (stop_dist * 3.0), digits)
                                low_target = round(price - (stop_dist * 3.0), digits)
                                
                                market_ctx = {
                                    "symbol": symbol,
                                    "bid": bid,
                                    "ask": ask,
                                    "price": price,
                                    "structural_stop": sl,
                                    "swing_low": sl if action == "BUY" else low_target,
                                    "swing_high": high_target if action == "BUY" else sl,
                                    "target_high": high_target,
                                    "target_low": low_target,
                                    "liquidity_pool_high": high_target,
                                    "liquidity_pool_low": low_target,
                                }
                                
                                acc = get_account_info() or {}
                                bal = float(getattr(acc, "balance", 100.0) if not isinstance(acc, dict) else acc.get("balance", 100.0) or 100.0)
                                eq = float(getattr(acc, "equity", bal) if not isinstance(acc, dict) else acc.get("equity", bal) or bal)
                                
                                trade_plan = {
                                    "symbol": symbol,
                                    "action": action,
                                    "decision": action,
                                    "signal": action,
                                    "lot_size": self.default_lot,
                                    "entry": price,
                                    "entry_price": price,
                                    "stop_loss": sl,
                                    "take_profit": tp,
                                    "market_context": market_ctx,
                                    "structural_context": market_ctx,
                                    "account_balance": bal,
                                    "account_equity": eq,
                                    "opportunity_score": float(confidence) / 100.0 if float(confidence) > 1.0 else float(confidence),
                                }
                                
                                risk_ctx = {
                                    "account_balance": bal,
                                    "account_equity": eq,
                                    "starting_balance": bal,
                                    "starting_day_balance": bal,
                                    "symbol_info": sym_info,
                                    "base_risk_percent": self.risk_pct,
                                    "preferred_lot": self.default_lot,
                                }
                                
                                res = execute_trade_pipeline(
                                    trade_plan,
                                    symbol_info=sym_info,
                                    risk_context=risk_ctx,
                                    execute_live=True,
                                    reject_existing_position=True,
                                )
                                
                                if res.get("execution_allowed") or res.get("status") == "READY":
                                    final_gate = res.get("final_gate", {})
                                    gate_result = final_gate.get("gate_result", final_gate) if isinstance(final_gate, dict) else {}
                                    builder_res = res.get("order_builder", {})
                                    order_payload = builder_res.get("order") or builder_res.get("built_order") or trade_plan
                                    while isinstance(order_payload, dict) and "order" in order_payload and isinstance(order_payload["order"], dict):
                                        order_payload = order_payload["order"]
                                    
                                    live_res = execute_live_trade(order=order_payload, gate=gate_result)
                                    if live_res.get("status") in ("EXECUTED", "SUCCESS") or live_res.get("order_sent"):
                                        ticket = live_res.get("ticket") or live_res.get("deal") or live_res.get("order")
                                        self._add_log("SUCCESS", f"Auto-trade placed on MT5: {action} {symbol} (#{ticket})")
                                        break
                                    else:
                                        self._add_log("WARNING", f"Auto-trade MT5 rejected: {live_res.get('reason')}")
                                else:
                                    reason = res.get("reason") or "Safety pipeline blocked trade"
                                    self._add_log("WARNING", f"Auto-trade safety blocked for {symbol}: {reason}")
                            '''
    code = code[:start_idx] + new_block + code[end_idx:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print("SUCCESS: AutoTrader updated with complete trade plan and diagnostic logging.")
else:
    print("ERROR: Could not find signal block in auto_trader.py")
