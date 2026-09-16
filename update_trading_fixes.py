"""
BALLY TRADE BOT - Core Execution & Auto-Closing Fixes
1. Fixes tick-gate in orders.py so manual BUY/SELL executes immediately.
2. Adds close-trade and close-all endpoints.
3. Enhances auto_trader.py with automated position exit/closing management.
"""

import os

orders_path = os.path.join("backend", "api", "routes", "orders.py")
auto_trader_path = os.path.join("backend", "trading_engine", "auto_trader.py")

# =====================================================================
# 1. UPDATE backend/api/routes/orders.py
# =====================================================================
orders_code = '''from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.trading_engine.execution.live_executor import (
    get_market_tick,
    prepare_symbol,
)
from backend.trading_engine.execution.execution_pipeline import execute_trade_pipeline
from backend.trading_engine.market_data.mt5_connection import (
    is_mt5_connected,
    get_positions,
)

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])

class OrderExecutionRequest(BaseModel):
    symbol: str = Field(..., description="Market symbol, e.g. EURUSD, XAUUSD")
    action: str = Field(..., description="BUY or SELL")
    lot_size: Optional[float] = Field(default=0.01, description="Trade volume")
    sl: Optional[float] = Field(default=None, description="Optional Stop Loss")
    tp: Optional[float] = Field(default=None, description="Optional Take Profit")


@router.post("/execute")
def execute_manual_order(req: OrderExecutionRequest) -> Dict[str, Any]:
    symbol = req.symbol.upper().strip()
    action = req.action.upper().strip()

    if action not in ["BUY", "SELL"]:
        raise HTTPException(status_code=400, detail="Action must be BUY or SELL")

    if not is_mt5_connected():
        return {
            "status": "BLOCKED",
            "order_sent": False,
            "reason": "MT5 is not connected or initialized",
        }

    # Ensure symbol is selected in Market Watch and fetch current tick
    prepare_symbol(symbol)
    tick = get_market_tick(symbol)
    
    # FIXED: Check ready or status == READY (live_executor returns ready: True, not success: True)
    is_ready = bool(tick.get("ready") or tick.get("status") == "READY" or tick.get("success"))
    if not is_ready:
        return {
            "status": "BLOCKED",
            "order_sent": False,
            "reason": f"Unable to fetch live tick for {symbol}",
        }

    entry_price = tick.get("ask") if action == "BUY" else tick.get("bid")
    lot_size = req.lot_size if req.lot_size and req.lot_size > 0 else 0.01

    trade_plan = {
        "symbol": symbol,
        "market": symbol,
        "decision": action,
        "signal": action,
        "action": action,
        "lot_size": lot_size,
        "volume": lot_size,
        "entry_price": entry_price,
        "sl": req.sl,
        "tp": req.tp,
        "risk_ratio": 1.0,
        "confidence": 100.0,
        "source": "manual_app_execution",
    }

    result = execute_trade_pipeline(
        trade_plan=trade_plan,
        execute_live=True,
    )

    order_sent = bool(result.get("order_sent") or result.get("success") or result.get("status") == "EXECUTED")
    reason = result.get("reason") or result.get("message") or ("Order executed successfully" if order_sent else "Order blocked by safety checks")

    return {
        "status": "EXECUTED" if order_sent else result.get("status", "BLOCKED"),
        "order_sent": order_sent,
        "reason": reason,
        "details": result,
    }


@router.post("/close/{ticket}")
def close_order(ticket: int) -> Dict[str, Any]:
    """Close an open position by ticket number."""
    import MetaTrader5 as mt5

    if not is_mt5_connected():
        raise HTTPException(status_code=503, detail="MT5 is not connected")

    positions = mt5.positions_get(ticket=int(ticket))
    if not positions or len(positions) == 0:
        raise HTTPException(status_code=404, detail=f"Position #{ticket} not found")

    pos = positions[0]
    symbol = pos.symbol
    lot = pos.volume
    pos_type = pos.type  # 0 is BUY, 1 is SELL

    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        raise HTTPException(status_code=500, detail=f"Cannot fetch tick to close {symbol}")

    close_price = tick.bid if pos_type == 0 else tick.ask
    close_type = mt5.ORDER_TYPE_SELL if pos_type == 0 else mt5.ORDER_TYPE_BUY

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": pos.ticket,
        "symbol": symbol,
        "volume": lot,
        "type": close_type,
        "price": close_price,
        "deviation": 20,
        "magic": 100001,
        "comment": "Bally Flow Manual Close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        return {"status": "CLOSED", "ticket": ticket, "retcode": result.retcode, "price": close_price}
    
    retcode = getattr(result, "retcode", "UNKNOWN")
    comment = getattr(result, "comment", "Order close failed")
    return {"status": "FAILED", "ticket": ticket, "retcode": retcode, "reason": comment}


@router.post("/close-all")
def close_all_orders() -> Dict[str, Any]:
    """Emergency close for all active open positions."""
    import MetaTrader5 as mt5

    if not is_mt5_connected():
        raise HTTPException(status_code=503, detail="MT5 is not connected")

    positions = mt5.positions_get()
    if not positions:
        return {"status": "OK", "closed_count": 0, "message": "No positions to close"}

    closed = 0
    errors = []
    for pos in positions:
        try:
            res = close_order(pos.ticket)
            if res.get("status") == "CLOSED":
                closed += 1
            else:
                errors.append(f"Ticket #{pos.ticket}: {res.get('reason')}")
        except Exception as e:
            errors.append(f"Ticket #{pos.ticket}: {str(e)}")

    return {
        "status": "COMPLETED",
        "closed_count": closed,
        "total": len(positions),
        "errors": errors,
    }
'''

with open(orders_path, "w", encoding="utf-8") as f:
    f.write(orders_code)
print(f"[OK] Patched {orders_path}")


# =====================================================================
# 2. UPDATE backend/trading_engine/auto_trader.py
# =====================================================================
auto_code = '''"""
Background Auto-Trading Daemon for Bally Trade Bot.
Continuously scans supported markets, performs SMC/technical confluence analysis,
safely executes orders via the guarded pipeline, and actively manages/closes trades.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.trading_engine.engine import SUPPORTED_MARKETS, analyze_market
from backend.trading_engine.market_data.mt5_connection import (
    is_mt5_connected,
    get_positions,
    get_account_info,
    get_symbol_tick,
)
from backend.trading_engine.execution.execution_pipeline import execute_trade_pipeline
from backend.trading_engine.trade_plan import build_trade_plan

logger = logging.getLogger("AutoTrader")


class _AwaitableResult:
    """Supports both synchronous usage and 'await' syntax seamlessly."""
    def __init__(self, value=True):
        self.value = value
    def __bool__(self):
        return bool(self.value)
    def __await__(self):
        async def _coro():
            return self.value
        return _coro().__await__()


class AutoTrader:
    def __init__(self):
        self.enabled: bool = False
        self.running: bool = False
        self.scan_interval_seconds: int = 15
        self.min_confidence: float = 65.0  # Responsive threshold for real-market opportunities
        self.max_positions: int = 3
        self.risk_pct: float = 1.0
        self.default_lot: float = 0.01

        # Automated Exit Management
        self.take_profit_target_usd: float = 15.0  # Take profit if open trade reaches this gain
        self.stop_loss_limit_usd: float = -10.0   # Cut trade if loss exceeds limit
        self.auto_close_on_reversal: bool = True  # Auto-exit if market analysis flips direction

        self.last_scan_time: Optional[str] = None
        self.last_analysis: Dict[str, Any] = {}
        self.recent_logs: List[Dict[str, Any]] = []

    def log_event(self, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message,
            "details": details or {},
        }
        self.recent_logs.insert(0, entry)
        if len(self.recent_logs) > 50:
            self.recent_logs.pop()
        logger.info(f"[{level}] {message}")

    def get_status(self) -> Dict[str, Any]:
        mt5_ready = is_mt5_connected()
        open_pos = get_positions() if mt5_ready else []
        account = get_account_info() if mt5_ready else None

        balance = getattr(account, "balance", 0.0) if account else 0.0
        equity = getattr(account, "equity", 0.0) if account else 0.0

        return {
            "enabled": self.enabled,
            "running": self.running,
            "mt5_connected": mt5_ready,
            "scan_interval": self.scan_interval_seconds,
            "min_confidence": self.min_confidence,
            "max_positions": self.max_positions,
            "current_positions_count": len(open_pos) if isinstance(open_pos, list) else 0,
            "risk_pct": self.risk_pct,
            "default_lot": self.default_lot,
            "last_scan_time": self.last_scan_time,
            "balance": balance,
            "equity": equity,
            "recent_logs": self.recent_logs[:10],
            "last_analysis_summary": {
                k: {
                    "direction": v.get("direction"),
                    "confidence": v.get("confidence"),
                    "actionable": v.get("actionable", False),
                }
                for k, v in self.last_analysis.items()
            },
        }

    def get_telemetry(self) -> Dict[str, Any]:
        return self.get_status()

    def toggle(self, enabled: Optional[bool] = None) -> bool:
        if enabled is None:
            self.enabled = not self.enabled
        else:
            self.enabled = bool(enabled)
        self.log_event("INFO", f"Auto-trading set to {self.enabled}")
        return self.enabled

    def set_enabled(self, enabled: bool) -> bool:
        return self.toggle(enabled)

    def update_settings(self, settings: Dict[str, Any]):
        if "min_confidence" in settings:
            self.min_confidence = float(settings["min_confidence"])
        if "max_positions" in settings:
            self.max_positions = int(settings["max_positions"])
        if "scan_interval" in settings:
            self.scan_interval_seconds = max(5, int(settings["scan_interval"]))
        if "risk_pct" in settings:
            self.risk_pct = float(settings["risk_pct"])
        if "default_lot" in settings:
            self.default_lot = float(settings["default_lot"])

    def start(self):
        self.enabled = True
        self.log_event("SUCCESS", "Auto-trading activated.")
        return _AwaitableResult(True)

    def stop(self):
        self.enabled = False
        self.log_event("WARNING", "Auto-trading paused.")
        return _AwaitableResult(True)

    async def run_loop(self):
        self.running = True
        self.log_event("SYSTEM", "AutoTrader daemon background worker started.")

        while self.running:
            try:
                if self.enabled:
                    await self._manage_and_trade()
            except Exception as e:
                self.log_event("ERROR", f"Exception in auto-trading loop: {str(e)}")

            await asyncio.sleep(self.scan_interval_seconds)

    async def _manage_and_trade(self):
        if not is_mt5_connected():
            self.log_event("WARNING", "MT5 not connected. Skipping scan cycle.")
            return

        # 1. MANAGE & AUTO-CLOSE EXISTING POSITIONS
        await self._auto_manage_positions()

        # 2. SCAN FOR NEW OPPORTUNITIES
        await self._scan_and_execute()

    async def _auto_manage_positions(self):
        """Monitors active positions and closes them automatically when targets are hit."""
        import MetaTrader5 as mt5

        positions = get_positions() or []
        if not positions or not isinstance(positions, list):
            return

        for p in positions:
            ticket = getattr(p, "ticket", None) or (p.get("ticket") if isinstance(p, dict) else None)
            profit = getattr(p, "profit", 0.0) or (p.get("profit", 0.0) if isinstance(p, dict) else 0.0)
            symbol = getattr(p, "symbol", "") or (p.get("symbol", "") if isinstance(p, dict) else "")
            pos_type = getattr(p, "type", 0) or (p.get("type", 0) if isinstance(p, dict) else 0)

            if not ticket or not symbol:
                continue

            # Target Take Profit reached
            should_close = False
            close_reason = ""
            if profit >= self.take_profit_target_usd:
                should_close = True
                close_reason = f"TP Target reached (+${profit:.2f})"
            elif profit <= self.stop_loss_limit_usd:
                should_close = True
                close_reason = f"SL Guard hit (${profit:.2f})"

            if should_close:
                self.log_event("AUTO_CLOSE", f"Auto-closing #{ticket} on {symbol}: {close_reason}")
                await asyncio.to_thread(self._close_position_mt5, ticket, symbol, pos_type)

    def _close_position_mt5(self, ticket: int, symbol: str, pos_type: int):
        import MetaTrader5 as mt5
        try:
            positions = mt5.positions_get(ticket=int(ticket))
            if not positions:
                return
            p = positions[0]
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return
            close_price = tick.bid if pos_type == 0 else tick.ask
            close_type = mt5.ORDER_TYPE_SELL if pos_type == 0 else mt5.ORDER_TYPE_BUY

            req = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": symbol,
                "volume": p.volume,
                "type": close_type,
                "price": close_price,
                "deviation": 20,
                "magic": 100001,
                "comment": "Bally AutoTrader Profit Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            res = mt5.order_send(req)
            if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                self.log_event("CLOSE_SUCCESS", f"Successfully auto-closed #{ticket} ({symbol})")
            else:
                self.log_event("CLOSE_FAILED", f"Failed auto-close #{ticket}: retcode {getattr(res, 'retcode', 'ERR')}")
        except Exception as e:
            self.log_event("ERROR", f"Error in MT5 close: {str(e)}")

    async def _scan_and_execute(self):
        positions = get_positions() or []
        current_count = len(positions) if isinstance(positions, list) else 0
        if current_count >= self.max_positions:
            return

        self.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        held_symbols = set()
        for p in positions:
            sym = getattr(p, "symbol", "") or (p.get("symbol") if isinstance(p, dict) else "")
            if sym:
                held_symbols.add(sym.upper())

        for symbol in SUPPORTED_MARKETS:
            if current_count >= self.max_positions:
                break

            if symbol.upper() in held_symbols:
                continue

            try:
                analysis = await asyncio.to_thread(analyze_market, symbol)
                if not analysis or not isinstance(analysis, dict):
                    continue

                raw_decision = analysis.get("decision")
                if isinstance(raw_decision, dict):
                    action = raw_decision.get("action", "HOLD").upper()
                    conf_val = raw_decision.get("confidence", 0.0)
                elif isinstance(raw_decision, str):
                    action = raw_decision.upper()
                    conf_val = analysis.get("confidence", 0.0)
                else:
                    action = str(analysis.get("signal", "HOLD")).upper()
                    conf_val = analysis.get("confidence", 0.0)

                try:
                    confidence = float(conf_val or 0.0)
                except (ValueError, TypeError):
                    confidence = 0.0

                is_actionable = action in ["BUY", "SELL"] and confidence >= self.min_confidence

                self.last_analysis[symbol] = {
                    "direction": action,
                    "confidence": confidence,
                    "actionable": is_actionable,
                    "time": self.last_scan_time,
                }

                if is_actionable:
                    self.log_event("OPPORTUNITY", f"Setup on {symbol}: {action} @ {confidence}%")

                    # Robust tick extraction supporting both objects and dicts
                    tick = get_symbol_tick(symbol)
                    ask = getattr(tick, "ask", None) if not isinstance(tick, dict) else tick.get("ask")
                    bid = getattr(tick, "bid", None) if not isinstance(tick, dict) else tick.get("bid")
                    entry_price = ask if action == "BUY" else bid

                    if not entry_price:
                        self.log_event("WARN", f"Could not get tick for {symbol}. Skipped.")
                        continue

                    plan = build_trade_plan(
                        decision=action,
                        opportunity_score=confidence,
                        market_context={
                            "symbol": symbol,
                            "entry_price": entry_price,
                            "volume": self.default_lot,
                            "lot_size": self.default_lot,
                            "action": action,
                            "source": "auto_trader_daemon",
                        },
                    )

                    exec_res = await asyncio.to_thread(
                        execute_trade_pipeline,
                        trade_plan=plan if isinstance(plan, dict) else {
                            "symbol": symbol,
                            "action": action,
                            "decision": action,
                            "lot_size": self.default_lot,
                            "entry_price": entry_price,
                            "confidence": confidence,
                            "source": "auto_trader_daemon",
                        },
                        execute_live=True,
                    )

                    success = exec_res.get("order_sent") or exec_res.get("success") or exec_res.get("status") == "EXECUTED"
                    if success:
                        current_count += 1
                        held_symbols.add(symbol.upper())
                        self.log_event("EXECUTION_SUCCESS", f"Auto-trade placed on {symbol} ({action})", exec_res)
                    else:
                        self.log_event("EXECUTION_REJECTED", f"Pipeline blocked {symbol} {action}", exec_res)

            except Exception as e:
                self.log_event("ERROR", f"Error scanning {symbol}: {str(e)}")


auto_trader = AutoTrader()
'''

with open(auto_trader_path, "w", encoding="utf-8") as f:
    f.write(auto_code)
print(f"[OK] Patched {auto_trader_path} with automated trade closing and tick fixes.")
