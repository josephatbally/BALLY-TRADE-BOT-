"""
Complete replacement for orders.py and auto_trader.py
Ensures live risk context and active background scanning loop.
"""

ORDERS_CONTENT = '''from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.trading_engine.execution.live_executor import (
    get_market_tick,
    prepare_symbol,
    close_position,
    close_all_positions,
)
from backend.trading_engine.execution.execution_pipeline import execute_trade_pipeline
from backend.trading_engine.market_data.mt5_connection import (
    is_mt5_connected,
    get_account_info,
    get_positions,
    get_symbol_tick,
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

    prepare_symbol(symbol)
    tick = get_symbol_tick(symbol)
    if not tick:
        tick_res = get_market_tick(symbol)
        if isinstance(tick_res, dict) and tick_res.get("tick"):
            tick = tick_res["tick"]

    if not tick:
        return {
            "status": "BLOCKED",
            "order_sent": False,
            "reason": f"Unable to fetch live tick for {symbol}",
        }

    entry_price = getattr(tick, "ask", None) if action == "BUY" else getattr(tick, "bid", None)
    if entry_price is None:
        if isinstance(tick, dict):
            entry_price = tick.get("ask") if action == "BUY" else tick.get("bid")
        else:
            entry_price = getattr(tick, "last", 0.0)

    account = get_account_info() or {}
    balance = float(account.get("balance", 100.0) or 100.0)
    equity = float(account.get("equity", balance) or balance)

    trade_plan = {
        "symbol": symbol,
        "decision": action,
        "signal": action,
        "entry": float(entry_price),
        "entry_price": float(entry_price),
        "stop_loss": req.sl,
        "take_profit": req.tp,
        "opportunity_score": 85.0,
    }

    risk_context = {
        "account_balance": balance,
        "account_equity": equity,
        "starting_balance": balance,
        "starting_day_balance": balance,
        "base_risk_percent": 1.0,
        "preferred_lot": req.lot_size or 0.01,
    }

    pipeline_result = execute_trade_pipeline(
        trade_plan,
        risk_context=risk_context,
        execute_live=True,
        reject_existing_position=False,
    )

    is_allowed = bool(pipeline_result.get("execution_allowed", False))
    return {
        "status": "SUCCESS" if is_allowed else "BLOCKED",
        "order_sent": is_allowed,
        "reason": "Order executed successfully" if is_allowed else pipeline_result.get("reason", "Order blocked by safety checks"),
        "details": pipeline_result,
    }

@router.post("/close/{ticket}")
def close_order(ticket: int) -> Dict[str, Any]:
    if not is_mt5_connected():
        return {"status": "ERROR", "message": "MT5 is not connected"}
    result = close_position(ticket)
    return result if isinstance(result, dict) else {"status": "OK", "ticket": ticket, "result": str(result)}

@router.post("/close-all")
def close_all() -> Dict[str, Any]:
    if not is_mt5_connected():
        return {"status": "ERROR", "message": "MT5 is not connected"}
    result = close_all_positions()
    return result if isinstance(result, dict) else {"status": "OK", "result": str(result)}
'''

AUTO_TRADER_CONTENT = '''"""
Background Auto-Trading Daemon for Bally Trade Bot.
Scans supported markets, performs SMC/technical confluence analysis,
manages open positions, and safely executes orders via the guarded pipeline.
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
from backend.trading_engine.execution.live_executor import close_position
from backend.trading_engine.trade_plan import build_trade_plan

logger = logging.getLogger("AutoTrader")

class AutoTrader:
    def __init__(self):
        self.enabled: bool = True
        self.running: bool = False
        self._task: Optional[asyncio.Task] = None
        self.scan_interval: int = 15
        self.min_confidence: float = 65.0
        self.max_positions: int = 3
        self.risk_pct: float = 1.0
        self.default_lot: float = 0.01
        self.take_profit_dollars: float = 15.0
        self.stop_loss_dollars: float = -10.0
        self.auto_manage_exits: bool = True
        self.last_scan_time: Optional[str] = None
        self.last_analysis_summary: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []

    def _add_log(self, level: str, message: str, details: Any = None):
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level,
            "message": message,
            "details": details or "",
        }
        self.logs.insert(0, entry)
        if len(self.logs) > 30:
            self.logs.pop()

    def start(self):
        self.enabled = True
        if not self.running or self._task is None or self._task.done():
            self.running = True
            try:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(self._run_loop())
                self._add_log("SUCCESS", "Auto-trading daemon background worker started")
            except RuntimeError:
                pass
        return True

    def stop(self):
        self.enabled = False
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self._add_log("WARNING", "Auto-trading daemon stopped")
        return False

    def toggle(self):
        return self.set_enabled(not self.enabled)

    def set_enabled(self, val: bool):
        self.enabled = bool(val)
        if self.enabled:
            return self.start()
        else:
            return self.stop()

    def get_telemetry(self) -> Dict[str, Any]:
        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        account = get_account_info() if is_mt5_connected() else {}
        positions = get_positions() if is_mt5_connected() else []
        return {
            "enabled": self.enabled,
            "running": self.running,
            "mt5_connected": is_mt5_connected(),
            "scan_interval": self.scan_interval,
            "min_confidence": self.min_confidence,
            "max_positions": self.max_positions,
            "current_positions_count": len(positions) if positions else 0,
            "risk_pct": self.risk_pct,
            "default_lot": self.default_lot,
            "last_scan_time": self.last_scan_time,
            "balance": account.get("balance", 0.0) if account else 0.0,
            "equity": account.get("equity", 0.0) if account else 0.0,
            "recent_logs": self.logs[:10],
            "last_analysis_summary": self.last_analysis_summary,
        }

    async def _manage_positions(self):
        if not self.auto_manage_exits or not is_mt5_connected():
            return
        positions = get_positions() or []
        for pos in positions:
            ticket = pos.get("ticket") if isinstance(pos, dict) else getattr(pos, "ticket", None)
            profit = pos.get("profit") if isinstance(pos, dict) else getattr(pos, "profit", 0.0)
            symbol = pos.get("symbol") if isinstance(pos, dict) else getattr(pos, "symbol", "")
            if ticket is None:
                continue
            if profit >= self.take_profit_dollars:
                self._add_log("SUCCESS", f"Auto-take-profit triggered for {symbol} (#{ticket}) at ${profit:.2f}")
                close_position(ticket)
            elif profit <= self.stop_loss_dollars:
                self._add_log("WARNING", f"Auto-stop-loss triggered for {symbol} (#{ticket}) at ${profit:.2f}")
                close_position(ticket)

    async def _run_loop(self):
        self.running = True
        self._add_log("SUCCESS", "Background scan loop is active")
        while self.running and self.enabled:
            try:
                self.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if is_mt5_connected():
                    await self._manage_positions()
                    positions = get_positions() or []
                    if len(positions) < self.max_positions:
                        open_symbols = {
                            p.get("symbol") if isinstance(p, dict) else getattr(p, "symbol", "")
                            for p in positions
                        }
                        for symbol in SUPPORTED_MARKETS:
                            if not self.running or not self.enabled:
                                break
                            if symbol in open_symbols:
                                continue
                            try:
                                analysis = analyze_market(symbol)
                                decision_val = analysis.get("decision", "NO_TRADE") if isinstance(analysis, dict) else "NO_TRADE"
                                action = decision_val.get("action", "NO_TRADE") if isinstance(decision_val, dict) else str(decision_val).upper()
                                confidence_val = analysis.get("confidence", 0.0) if isinstance(analysis, dict) else 0.0
                                confidence = confidence_val.get("score", 0.0) if isinstance(confidence_val, dict) else float(confidence_val or 0.0)
                                self.last_analysis_summary[symbol] = {"action": action, "confidence": confidence}

                                if action in ["BUY", "SELL"] and confidence >= self.min_confidence:
                                    self._add_log("INFO", f"Signal found: {action} {symbol} ({confidence:.1f}%)")
                                    tick = get_symbol_tick(symbol)
                                    price = (tick.get("ask") if isinstance(tick, dict) else getattr(tick, "ask", 0.0)) if action == "BUY" else (tick.get("bid") if isinstance(tick, dict) else getattr(tick, "bid", 0.0))
                                    acc = get_account_info() or {}
                                    bal = float(acc.get("balance", 100.0) or 100.0)
                                    eq = float(acc.get("equity", bal) or bal)

                                    trade_plan = {
                                        "symbol": symbol,
                                        "decision": action,
                                        "signal": action,
                                        "entry": float(price),
                                        "entry_price": float(price),
                                        "opportunity_score": float(confidence),
                                    }
                                    risk_ctx = {
                                        "account_balance": bal,
                                        "account_equity": eq,
                                        "starting_balance": bal,
                                        "starting_day_balance": bal,
                                        "base_risk_percent": self.risk_pct,
                                        "preferred_lot": self.default_lot,
                                    }
                                    res = execute_trade_pipeline(
                                        trade_plan,
                                        risk_context=risk_ctx,
                                        execute_live=True,
                                        reject_existing_position=True,
                                    )
                                    if res.get("execution_allowed"):
                                        self._add_log("SUCCESS", f"Auto-trade placed: {action} {symbol}")
                                        break
                            except Exception as scan_err:
                                self._add_log("WARNING", f"Scan error on {symbol}: {scan_err}")
            except Exception as loop_err:
                self._add_log("ERROR", f"Loop exception: {loop_err}")
            await asyncio.sleep(self.scan_interval)
        self.running = False
'''

with open("backend/api/routes/orders.py", "w", encoding="utf-8") as f:
    f.write(ORDERS_CONTENT)
print("[OK] backend/api/routes/orders.py written successfully.")

with open("backend/trading_engine/auto_trader.py", "w", encoding="utf-8") as f:
    f.write(AUTO_TRADER_CONTENT)
print("[OK] backend/trading_engine/auto_trader.py written successfully.")
