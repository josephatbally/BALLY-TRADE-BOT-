"""
Background Auto-Trading Daemon for Bally Trade Bot.
Continuously scans supported markets, performs SMC/technical confluence analysis,
checks confidence thresholds, and safely executes orders via the guarded pipeline.
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
        self.min_confidence: float = 75.0
        self.max_positions: int = 3
        self.risk_pct: float = 1.0
        self.default_lot: float = 0.01

        self.last_scan_time: Optional[str] = None
        self.last_analysis: Dict[str, Any] = {}
        self.recent_logs: List[Dict[str, Any]] = []
        self._task: Optional[asyncio.Task] = None

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
        self.log_event("INFO", "Settings updated", settings)

    def start(self):
        self.enabled = True
        self.log_event("INFO", "Auto-trading activated.")
        if not self.running:
            try:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(self.run_loop())
            except RuntimeError:
                pass
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
                    await self._evaluate_and_trade()
            except Exception as e:
                self.log_event("ERROR", f"Exception in auto-trading loop: {str(e)}")

            await asyncio.sleep(self.scan_interval_seconds)

    async def _evaluate_and_trade(self):
        if not is_mt5_connected():
            self.log_event("WARNING", "MT5 not connected. Skipping scan cycle.")
            return

        positions = get_positions() or []
        current_count = len(positions) if isinstance(positions, list) else 0
        if current_count >= self.max_positions:
            self.log_event("INFO", f"Max position cap reached ({current_count}/{self.max_positions}).")
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

                # Support both string decisions and dictionary decisions
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

                    tick = get_symbol_tick(symbol)
                    ask = tick.get("ask") if tick else None
                    bid = tick.get("bid") if tick else None
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
