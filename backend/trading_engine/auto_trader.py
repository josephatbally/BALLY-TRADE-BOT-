"""
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
from backend.trading_engine.execution.live_executor import close_position, execute_live_trade
from backend.trading_engine.trade_plan import build_trade_plan

logger = logging.getLogger("AutoTrader")

class _AwaitableResult:
    """Supports both sync usage and 'await' syntax seamlessly."""
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
        return _AwaitableResult(True)

    def stop(self):
        self.enabled = False
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self._add_log("WARNING", "Auto-trading daemon stopped")
        return _AwaitableResult(False)

    def toggle(self):
        return self.set_enabled(not self.enabled)

    def set_enabled(self, val: bool):
        self.enabled = bool(val)
        if self.enabled:
            return bool(self.start())
        else:
            return bool(self.stop())

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
            "balance": (getattr(account, "balance", 0.0) if not isinstance(account, dict) else account.get("balance", 0.0)) if account else 0.0,
            "equity": (getattr(account, "equity", 0.0) if not isinstance(account, dict) else account.get("equity", 0.0)) if account else 0.0,
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
                                    bal = float(getattr(acc, "balance", 100.0) if not isinstance(acc, dict) else acc.get("balance", 100.0) or 100.0)
                                    eq = float(getattr(acc, "equity", bal) if not isinstance(acc, dict) else acc.get("equity", bal) or bal)

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
                                    if res.get('execution_allowed') or res.get('status') == 'READY':
                                        final_gate = res.get('final_gate', {})
                                        gate_result = final_gate.get('gate_result', final_gate) if isinstance(final_gate, dict) else {}
                                        builder_res = res.get('order_builder', {})
                                        order_payload = builder_res.get('order') or builder_res.get('built_order') or trade_plan
                                        while isinstance(order_payload, dict) and 'order' in order_payload and isinstance(order_payload['order'], dict):
                                            order_payload = order_payload['order']
                                        live_res = execute_live_trade(order=order_payload, gate=gate_result)
                                        if live_res.get('status') in ('EXECUTED', 'SUCCESS') or live_res.get('order_sent'):
                                            ticket = live_res.get('ticket') or live_res.get('order')
                                            self._add_log('SUCCESS', f'Auto-trade executed on MT5: {action} {symbol} (#{ticket})')
                                            break
                                        else:
                                            self._add_log('WARNING', f'Auto-trade MT5 rejected: {live_res.get("reason")}')
                            except Exception as scan_err:
                                self._add_log("WARNING", f"Scan error on {symbol}: {scan_err}")
            except Exception as loop_err:
                self._add_log("ERROR", f"Loop exception: {loop_err}")
            await asyncio.sleep(self.scan_interval)
        self.running = False

auto_trader = AutoTrader()

