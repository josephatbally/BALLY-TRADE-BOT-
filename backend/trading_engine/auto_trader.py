"""
BALLY FLOW - High-Speed Intelligent Auto-Trading Engine
Parallel Async Market Scanner, Conviction-Weighted Dynamic Sizing,
and Microstructure Trade Management.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set

from backend.trading_engine.engine import SUPPORTED_MARKETS, analyze_market
from backend.trading_engine.market_data.mt5_connection import (
    is_mt5_connected,
    get_positions,
    get_account_info,
    get_symbol_tick,
    get_symbol_info,
)
from backend.trading_engine.execution.execution_pipeline import execute_trade_pipeline
from backend.trading_engine.execution.live_executor import close_position, execute_live_trade

logger = logging.getLogger("AutoTrader")


class _AwaitableResult:
    def __init__(self, value=True):
        self.value = value

    def __bool__(self):
        return bool(self.value)

    def __await__(self):
        async def _coro():
            return self.value
        return _coro().__await__()


def calculate_dynamic_lot(
    symbol: str,
    confidence: float,
    equity: float,
    stop_dist: float,
    sym_info: Any,
    base_risk_pct: float = 1.0,
    max_risk_pct: float = 2.5,
) -> float:
    """
    Intelligent Dynamic Lot Calculation based on Setup Conviction Tier:
    - A+ Institutional Setup (Confidence >= 80%): Scales risk up to 2.5%
    - Standard High-Probability Setup (Confidence 70-79%): 1.5% risk
    - Baseline Setup (Confidence 65-69%): 1.0% risk
    Calculates exact lot size from monetary risk, tick value, and stop-loss distance.
    """
    if confidence >= 80.0:
        target_risk_pct = max_risk_pct
    elif confidence >= 72.0:
        target_risk_pct = min(base_risk_pct * 1.5, max_risk_pct)
    else:
        target_risk_pct = base_risk_pct

    monetary_risk = max((equity * target_risk_pct) / 100.0, 1.0)

    min_vol = getattr(sym_info, "volume_min", 0.01) or 0.01
    max_vol = getattr(sym_info, "volume_max", 5.0) or 5.0
    vol_step = getattr(sym_info, "volume_step", 0.01) or 0.01
    tick_value = getattr(sym_info, "trade_tick_value", None) or 1.0
    tick_size = getattr(sym_info, "trade_tick_size", None) or getattr(sym_info, "point", 0.0001) or 0.0001

    ticks_at_risk = max(stop_dist / tick_size, 1.0)
    per_lot_risk = ticks_at_risk * tick_value

    if per_lot_risk > 0:
        raw_volume = monetary_risk / per_lot_risk
    else:
        raw_volume = min_vol

    steps = round(raw_volume / vol_step)
    calc_volume = steps * vol_step
    calc_volume = max(min_vol, min(calc_volume, max_vol))
    return round(calc_volume, 2)


class AutoTrader:
    def __init__(self):
        self.enabled: bool = True
        self.running: bool = False
        self._task: Optional[asyncio.Task] = None
        self.scan_interval: int = 5  # High-speed 5-second parallel scanning interval
        self.min_confidence: float = 65.0
        self.max_positions: int = 3
        self.risk_pct: float = 1.0
        self.max_risk_pct: float = 2.5
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
                self._add_log("SUCCESS", "High-speed auto-trading daemon started")
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
            "max_risk_pct": self.max_risk_pct,
            "default_lot": self.default_lot,
            "last_scan_time": self.last_scan_time,
            "balance": (getattr(account, "balance", 0.0) if not isinstance(account, dict) else account.get("balance", 0.0)) if account else 0.0,
            "equity": (getattr(account, "equity", 0.0) if not isinstance(account, dict) else account.get("equity", 0.0)) if account else 0.0,
            "recent_logs": self.logs[:10],
            "last_analysis_summary": self.last_analysis_summary,
        }

    async def _manage_positions(self):
        """Active risk and profit manager: closes at targets and cuts losses early."""
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
                self._add_log("SUCCESS", f"Profit Target Hit: {symbol} (#{ticket}) +${profit:.2f}")
                close_position(ticket)
            elif profit <= self.stop_loss_dollars:
                self._add_log("WARNING", f"Risk Stop Hit: {symbol} (#{ticket}) -${abs(profit):.2f}")
                close_position(ticket)

    async def _evaluate_and_execute_symbol(
        self,
        symbol: str,
        open_symbols: Set[str],
        account: Any,
        current_count: int,
    ) -> bool:
        """Evaluates a single market asynchronously and submits trade if high-probability criteria are met."""
        if symbol in open_symbols:
            return False

        try:
            # Run market analysis in background thread so scanner loop never blocks
            analysis = await asyncio.to_thread(analyze_market, symbol)
            decision_val = analysis.get("decision", "NO_TRADE") if isinstance(analysis, dict) else "NO_TRADE"
            action = decision_val.get("action", "NO_TRADE") if isinstance(decision_val, dict) else str(decision_val).upper()
            confidence_val = analysis.get("confidence", 0.0) if isinstance(analysis, dict) else 0.0
            confidence = confidence_val.get("score", 0.0) if isinstance(confidence_val, dict) else float(confidence_val or 0.0)
            self.last_analysis_summary[symbol] = {"action": action, "confidence": confidence}

            if action not in ["BUY", "SELL"] or confidence < self.min_confidence:
                return False

            self._add_log("INFO", f"High-conviction signal: {action} {symbol} ({confidence:.1f}%)")
            tick = get_symbol_tick(symbol)
            if not tick:
                return False

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

            bal = float(getattr(account, "balance", 100.0) if not isinstance(account, dict) else account.get("balance", 100.0) or 100.0)
            eq = float(getattr(account, "equity", bal) if not isinstance(account, dict) else account.get("equity", bal) or bal)

            # Calculate intelligent conviction-based volume
            calculated_lot = calculate_dynamic_lot(
                symbol=symbol,
                confidence=confidence,
                equity=eq,
                stop_dist=stop_dist,
                sym_info=sym_info,
                base_risk_pct=self.risk_pct,
                max_risk_pct=self.max_risk_pct,
            )

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

            trade_plan = {
                "symbol": symbol,
                "action": action,
                "decision": action,
                "signal": action,
                "lot_size": calculated_lot,
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
                "preferred_lot": calculated_lot,
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
                    self._add_log("SUCCESS", f"Auto-trade placed: {action} {calculated_lot}L {symbol} (#{ticket}) [Conf: {confidence:.0f}%]")
                    return True
                else:
                    self._add_log("WARNING", f"Auto-trade broker rejected: {live_res.get('reason')}")
            else:
                reason = res.get("reason") or "Safety pipeline blocked trade"
                self._add_log("WARNING", f"Auto-trade safety blocked for {symbol}: {reason}")
        except Exception as scan_err:
            self._add_log("WARNING", f"Scan error on {symbol}: {scan_err}")
        return False

    async def _run_loop(self):
        self.running = True
        self._add_log("SUCCESS", "High-speed parallel auto-scan active (5s intervals)")
        while self.running and self.enabled:
            try:
                self.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if is_mt5_connected():
                    await self._manage_positions()
                    positions = get_positions() or []
                    open_count = len(positions)
                    if open_count < self.max_positions:
                        open_symbols = {
                            p.get("symbol") if isinstance(p, dict) else getattr(p, "symbol", "")
                            for p in positions
                        }
                        account = get_account_info() or {}

                        # Parallel evaluation across all supported markets concurrently
                        tasks = [
                            self._evaluate_and_execute_symbol(sym, open_symbols, account, open_count)
                            for sym in SUPPORTED_MARKETS
                        ]
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        for res in results:
                            if isinstance(res, Exception):
                                logger.error(f"Market evaluation task error: {res}")
            except Exception as loop_err:
                self._add_log("ERROR", f"Loop exception: {loop_err}")
            await asyncio.sleep(self.scan_interval)
        self.running = False


auto_trader = AutoTrader()
