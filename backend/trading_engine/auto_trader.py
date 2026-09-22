from backend.trading_engine.modes.mode_controller import get_mode_controller, TradingMode
from backend.trading_engine.hybrid.hybrid_engine import analyze_hybrid_market
from backend.trading_engine.ai.ai_engine import ai_engine
from backend.trading_engine.candle_scalper.candle_scalper import (
    DEFAULT_BURST_COUNT,
    DEFAULT_PROFIT_TARGET_USD,
    MIN_CONFIDENCE,
    analyze_candle_momentum,
    candle_position_comment,
    current_candle_movement,
    get_tiered_lot_size,
    parse_candle_position_comment,
)
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set

from backend.trading_engine.engine import SUPPORTED_MARKETS, analyze_market
from backend.trading_engine.market_data.mt5_connection import (
    ensure_mt5_connected,
    is_mt5_connected,
    get_positions,
    get_account_info,
    get_symbol_tick,
    get_symbol_info,
)
from backend.trading_engine.execution.execution_pipeline import execute_trade_pipeline
from backend.trading_engine.execution.live_executor import (
    close_position,
    execute_live_trade,
    set_live_execution_enabled,
)
from backend.trading_engine.tenant_router import tenant_router
from backend.trading_engine.trading_account_runtime import resolve_authenticated_trading_account

logger = logging.getLogger("AutoTrader")

SUPPORTED_STRATEGIES = ("SMC", "HYBRID", "CANDLE_SCALPER")
CANDLE_SCALPER_MAGIC = 20260817


def pos_field(position: Any, name: str, default: Any = None) -> Any:
    """Read a field from an MT5 position given as a dict or a namedtuple."""
    if isinstance(position, dict):
        value = position.get(name, default)
    else:
        value = getattr(position, name, default)
    return default if value is None else value


def acc_field(account: Any, name: str, default: Any = 0.0) -> Any:
    """Read a field from MT5 account info given as a dict or a namedtuple."""
    if isinstance(account, dict):
        value = account.get(name, default)
    else:
        value = getattr(account, name, default)
    return default if value is None else value


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
        self.enabled: bool = False
        self.running: bool = False
        self._task: Optional[asyncio.Task] = None
        self.scan_interval: int = 5
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
        self.owner_user_id: Optional[int] = None
        self.active_strategy: str = "SMC"
        self._closing_tickets: Set[Any] = set()
        self._manage_task: Optional[asyncio.Task] = None

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

    def set_strategy(self, strategy: str) -> str:
        """Set the live strategy and route the analysis pipeline to match."""
        requested = str(strategy or "").strip().upper()
        if requested not in SUPPORTED_STRATEGIES:
            raise ValueError(
                f"Unsupported strategy '{strategy}'. "
                f"Supported: {', '.join(SUPPORTED_STRATEGIES)}"
            )

        self.active_strategy = requested

        # Wire the strategy into the analysis pipeline so the running bot
        # actually changes behaviour instead of only changing a label.
        try:
            mode_ctrl = get_mode_controller()
            mode_ctrl.set_mode(
                TradingMode.HYBRID if requested == "HYBRID" else TradingMode.TECHNICAL
            )
        except Exception as exc:
            logger.error("Unable to align mode controller with strategy: %s", exc)

        self._add_log("INFO", f"Active strategy changed to {self.active_strategy}")
        return self.active_strategy

    def get_strategy(self) -> str:
        return str(getattr(self, "active_strategy", "SMC") or "SMC").upper()

    def _record_owner_tickets(
        self,
        live_res: Dict[str, Any],
        *,
        symbol: str,
        action: str,
        lot: float,
        magic_number: int = 100001,
    ) -> None:
        """Record broker tickets against the owning tenant (single source)."""
        if self.owner_user_id is None or not isinstance(live_res, dict):
            return

        broker_send = live_res.get("mt5_order_send", {})
        tickets = {
            live_res.get("ticket"),
            live_res.get("deal"),
            live_res.get("order"),
            broker_send.get("order") if isinstance(broker_send, dict) else None,
            broker_send.get("deal") if isinstance(broker_send, dict) else None,
        }
        for ticket in tickets:
            if not ticket:
                continue
            try:
                tenant_router.record_user_order(
                    user_id=self.owner_user_id,
                    ticket=int(ticket),
                    symbol=symbol,
                    action=action,
                    lot_size=float(lot),
                    status="SUBMITTED",
                    magic_number=magic_number,
                )
            except Exception as exc:
                logger.error("Unable to record order ownership: %s", exc)

    def start(self):
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
        try:
            set_live_execution_enabled(False)
        except Exception as exc:
            logger.error("Unable to disable live executor: %s", exc)
        if self._task and not self._task.done():
            self._task.cancel()
        self._add_log("WARNING", "Auto-trading daemon stopped")
        return _AwaitableResult(False)

    def toggle(self):
        return self.set_enabled(not self.enabled)

    def set_enabled(self, val: bool, user_id: Optional[int] = None):
        if val and user_id is None:
            raise ValueError("Authenticated user ownership is required to enable auto-trading.")
        self.owner_user_id = int(user_id) if val and user_id is not None else None
        self.enabled = bool(val)

        try:
            set_live_execution_enabled(self.enabled)
        except Exception as exc:
            self.enabled = False
            self.owner_user_id = None
            raise RuntimeError(
                f"Unable to synchronize live execution state: {exc}"
            ) from exc

        if self.enabled:
            return bool(self.start())
        return bool(self.stop())

    def update_settings(
        self,
        *,
        min_confidence: Optional[float] = None,
        risk_per_trade_pct: Optional[float] = None,
        max_positions: Optional[int] = None,
        scan_interval_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Update live bot settings; unspecified values are left unchanged."""
        if min_confidence is not None:
            self.min_confidence = max(0.0, min(99.0, float(min_confidence)))
        if risk_per_trade_pct is not None:
            self.risk_pct = max(0.1, min(float(risk_per_trade_pct), self.max_risk_pct))
        if max_positions is not None:
            self.max_positions = max(1, int(max_positions))
        if scan_interval_seconds is not None:
            self.scan_interval = max(1, int(scan_interval_seconds))

        settings = {
            "min_confidence": self.min_confidence,
            "risk_per_trade_pct": self.risk_pct,
            "max_positions": self.max_positions,
            "scan_interval_seconds": self.scan_interval,
        }
        self._add_log("INFO", f"Bot settings updated: {settings}")
        return settings

    def get_telemetry(self) -> Dict[str, Any]:
        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        account = get_account_info() if is_mt5_connected() else {}
        positions = tenant_router.filter_user_positions(self.owner_user_id, get_positions() or []) if is_mt5_connected() and self.owner_user_id is not None else []
        return {
            "enabled": self.enabled,
            "owner_user_id": self.owner_user_id,
            "running": self.running,
            "active_strategy": self.active_strategy,
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

    async def _manage_candle_scalper_bursts(self, positions):
        """Manage Candle Momentum positions independently per leg.
        
        Closes individual legs when their floating profit reaches >= $2.50.
        Does not close unaffected legs in the group.
        """
        closes = []
        for pos in positions:
            parsed = parse_candle_position_comment(pos_field(pos, "comment", ""))
            if not parsed:
                continue

            profit = float(pos_field(pos, "profit", 0.0))
            ticket = pos_field(pos, "ticket")
            symbol = pos_field(pos, "symbol", "")
            direction = parsed.get("direction", "")

            # Strict individual leg exit: each leg must hit >= $2.50
            if profit >= DEFAULT_PROFIT_TARGET_USD and ticket is not None:
                self._add_log(
                    "SUCCESS",
                    f"[CANDLE SCALPER] Leg profit hit: {symbol} (#{ticket}) {direction} "
                    f"+${profit:.2f} >= ${DEFAULT_PROFIT_TARGET_USD:.2f} -> Closing leg",
                )
                closes.append(self._close_position_async(ticket, symbol))

        if closes:
            await asyncio.gather(*closes, return_exceptions=True)

    async def _close_position_async(self, ticket: Any, symbol: str = "") -> None:
        """Close a position off the event loop so the scan loop never stalls."""
        if ticket is None or ticket in self._closing_tickets:
            return
        self._closing_tickets.add(ticket)
        try:
            result = await asyncio.to_thread(close_position, ticket)
            if isinstance(result, dict) and not result.get("closed", True):
                self._add_log(
                    "WARNING",
                    f"Close rejected on {symbol} (#{ticket}): "
                    f"{result.get('reason', 'unknown broker reason')}",
                )
        except Exception as exc:
            self._add_log("WARNING", f"Close failed on {symbol} (#{ticket}): {exc}")
        finally:
            self._closing_tickets.discard(ticket)

    async def _manage_positions(self):
        if not self.auto_manage_exits or not is_mt5_connected():
            return

        raw_positions = await asyncio.to_thread(get_positions)
        positions = tenant_router.filter_user_positions(
            self.owner_user_id,
            raw_positions or [],
        )

        await self._manage_candle_scalper_bursts(positions)

        closes = []
        for pos in positions:
            if parse_candle_position_comment(pos_field(pos, "comment", "")):
                continue

            ticket = pos_field(pos, "ticket")
            profit = float(pos_field(pos, "profit", 0.0))
            symbol = pos_field(pos, "symbol", "")
            if ticket is None:
                continue

            if profit >= self.take_profit_dollars:
                self._add_log(
                    "SUCCESS",
                    f"Profit Target Hit: {symbol} (#{ticket}) +${profit:.2f}",
                )
                ai_engine.record_trade_outcome(
                    symbol=symbol,
                    timeframe="M15",
                    signal="BUY",
                    outcome="WIN",
                    entry_price=0.0,
                    exit_price=0.0,
                    pnl=profit,
                    quality=85.0,
                )
                closes.append(self._close_position_async(ticket, symbol))
            elif profit <= self.stop_loss_dollars:
                self._add_log(
                    "WARNING",
                    f"Risk Stop Hit: {symbol} (#{ticket}) -${abs(profit):.2f}",
                )
                ai_engine.record_trade_outcome(
                    symbol=symbol,
                    timeframe="M15",
                    signal="BUY",
                    outcome="LOSS",
                    entry_price=0.0,
                    exit_price=0.0,
                    pnl=profit,
                    quality=40.0,
                )
                closes.append(self._close_position_async(ticket, symbol))

        if closes:
            await asyncio.gather(*closes, return_exceptions=True)

    async def _evaluate_and_execute_symbol(
        self,
        symbol: str,
        open_symbols: Set[str],
        account: Any,
        current_count: int,
    ) -> bool:
        active_strategy = self.get_strategy()
        if active_strategy != "CANDLE_SCALPER" and symbol in open_symbols:
            return False

        # --- 1. CANDLE MOMENTUM SCALPER BRANCH ---
        # Independent from SMC, Hybrid and AI.
        if active_strategy == "CANDLE_SCALPER":
            all_positions = await asyncio.to_thread(get_positions) or []
            active_cs_legs = [
                p for p in all_positions
                if pos_field(p, "symbol", "") == symbol
                and parse_candle_position_comment(pos_field(p, "comment", ""))
            ]
            current_cs_count = len(active_cs_legs)
            slots_needed = max(0, DEFAULT_BURST_COUNT - current_cs_count)

            if slots_needed <= 0:
                return False
            try:
                scalp_res = await asyncio.to_thread(analyze_candle_momentum, symbol)
                signal = str(scalp_res.get("signal", "HOLD")).upper()
                confidence = float(scalp_res.get("confidence", 0.0))

                self.last_analysis_summary[symbol] = {
                    "action": signal,
                    "confidence": confidence,
                    "strategy": "CANDLE_SCALPER",
                    "timeframe": scalp_res.get("timeframe", "M1"),
                    "body_ratio": scalp_res.get("body_ratio"),
                    "body_expansion": scalp_res.get("body_expansion"),
                    "range_expansion": scalp_res.get("range_expansion"),
                }

                if signal not in ("BUY", "SELL") or confidence < MIN_CONFIDENCE:
                    return False

                burst_count = slots_needed
                if current_count + burst_count > self.max_positions:
                    self._add_log(
                        "INFO",
                        f"[CANDLE SCALPER] Burst skipped on {symbol}: "
                        f"{burst_count} positions would exceed max_positions={self.max_positions}",
                    )
                    return False

                tick = get_symbol_tick(symbol)
                if not tick:
                    return False

                bid = float(
                    getattr(tick, "bid", 0.0)
                    or (tick.get("bid", 0.0) if isinstance(tick, dict) else 0.0)
                )
                ask = float(
                    getattr(tick, "ask", 0.0)
                    or (tick.get("ask", 0.0) if isinstance(tick, dict) else 0.0)
                )
                if bid <= 0 or ask <= 0:
                    return False

                entry = ask if signal == "BUY" else bid
                sym_info = get_symbol_info(symbol)
                point = float(getattr(sym_info, "point", 0.0001) or 0.0001)
                digits = int(getattr(sym_info, "digits", 5) or 5)

                signal_range = max(float(scalp_res.get("range", 0.0) or 0.0), point)
                stop_dist = max(signal_range * 0.75, point * 150.0)

                sl = round(
                    entry - stop_dist if signal == "BUY" else entry + stop_dist,
                    digits,
                )
                tp = round(
                    entry + (stop_dist * 3.0)
                    if signal == "BUY"
                    else entry - (stop_dist * 3.0),
                    digits,
                )

                balance = float(acc_field(account, "balance", 0.0))
                lot = get_tiered_lot_size(balance)

                candle_move_target = float(
                    scalp_res.get(
                        "candle_move_target",
                        scalp_res.get("body", signal_range),
                    )
                    or signal_range
                )
                comment = candle_position_comment(signal, candle_move_target)
                profit_target = float(scalp_res.get("profit_target_usd", 2.50))

                self._add_log(
                    "INFO",
                    f"[CANDLE SCALPER] {signal} burst: "
                    f"{burst_count}x {lot}L {symbol}; "
                    f"max profit ${profit_target:.2f}; "
                    f"M1 move target {candle_move_target:.6f}",
                )

                opened = 0
                for index in range(burst_count):
                    order_payload = {
                        "symbol": symbol,
                        "action": signal,
                        "decision": signal,
                        "signal": signal,
                        "order_type": signal,
                        "volume": lot,
                        "price": entry,
                        "entry": entry,
                        "stop_loss": sl,
                        "take_profit": tp,
                        "magic_number": CANDLE_SCALPER_MAGIC,
                        "comment": comment,
                        "strategy": "CANDLE_SCALPER",
                        "timeframe": "M1",
                        "burst_index": index + 1,
                        "burst_count": burst_count,
                        "profit_target_usd": profit_target,
                        "candle_move_target": candle_move_target,
                    }

                    live_res = await asyncio.to_thread(
                        execute_live_trade,
                        order=order_payload,
                        gate=None,
                    )

                    if live_res.get("status") in ("EXECUTED", "SUCCESS") or live_res.get("real_trade"):
                        opened += 1

                        self._record_owner_tickets(
                            live_res,
                            symbol=symbol,
                            action=signal,
                            lot=lot,
                            magic_number=CANDLE_SCALPER_MAGIC,
                        )
                    else:
                        reason = live_res.get("reason", "broker execution blocked")
                        self._add_log(
                            "WARNING",
                            f"[CANDLE SCALPER] Burst leg {index + 1}/{burst_count} "
                            f"not opened on {symbol}: {reason}",
                        )
                        break

                    await asyncio.sleep(0.15)

                if opened == burst_count:
                    return True

                if opened:
                    self._add_log(
                        "WARNING",
                        f"[CANDLE SCALPER] Partial burst on {symbol}: "
                        f"{opened}/{burst_count} legs opened",
                    )
                return opened > 0

            except Exception as exc:
                self._add_log("WARNING", f"Candle Scalper error on {symbol}: {exc}")
                return False

        # --- 2. SMC & HYBRID ENGINE BRANCH ---
        try:
            analysis = await asyncio.to_thread(analyze_market, symbol)
            decision_val = analysis.get("decision", "NO_TRADE") if isinstance(analysis, dict) else "NO_TRADE"
            action = decision_val.get("action", "NO_TRADE") if isinstance(decision_val, dict) else str(decision_val).upper()
            confidence_val = analysis.get("confidence", 0.0) if isinstance(analysis, dict) else 0.0
            confidence = confidence_val.get("score", 0.0) if isinstance(confidence_val, dict) else float(confidence_val or 0.0)
            
            mode_ctrl = get_mode_controller()
            active_mode = mode_ctrl.mode.value
            fundamental_info = {}

            use_hybrid = active_strategy == "HYBRID" or mode_ctrl.is_hybrid()
            if use_hybrid:
                hybrid_res = await asyncio.to_thread(analyze_hybrid_market, symbol=symbol, technical_result=analysis)
                alignment = hybrid_res.get("alignment", "UNKNOWN")
                hybrid_signal = hybrid_res.get("hybrid_signal", "NO_TRADE")
                hybrid_conf = float(hybrid_res.get("hybrid_confidence", 0.0) or 0.0)
                fundamental_info = hybrid_res.get("fundamental", {})

                if hybrid_signal in ["BUY", "SELL"] and alignment in ["BUY_ALIGNED", "SELL_ALIGNED"]:
                    action = hybrid_signal
                    confidence = hybrid_conf
                    self._add_log(
                        "INFO",
                        f"[HYBRID] {symbol} {alignment}: Tech & News ALIGNED -> "
                        f"{action} ({confidence:.1f}%)",
                    )
                else:
                    self._add_log(
                        "WARNING",
                        f"[HYBRID SAFETY] {symbol} blocked by news conflict: "
                        f"{alignment} (Tech: {action})",
                    )
                    self.last_analysis_summary[symbol] = {
                        "action": "NO_TRADE",
                        "confidence": hybrid_conf,
                        "mode": active_mode,
                        "strategy": active_strategy,
                        "alignment": alignment,
                    }
                    return False

            ai_study = ai_engine.study_market(symbol=symbol, timeframe="M15", candles=[], technical_analysis=analysis if isinstance(analysis, dict) else {})
            multiplier = ai_study.get("multiplier", 1.0)
            adjusted_confidence = min(99.0, confidence * multiplier)
            confidence = adjusted_confidence
            self.last_analysis_summary[symbol] = {
                "action": action,
                "confidence": confidence,
                "mode": active_mode,
                "strategy": active_strategy,
                "regime": ai_study.get("regime", "BALANCED_RANGE"),
                "ai_samples": ai_study.get("samples_learned", 0),
            }

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

            bal = float(acc_field(account, "balance", 100.0) or 100.0)
            eq = float(acc_field(account, "equity", bal) or bal)

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

                live_res = await asyncio.to_thread(
                    execute_live_trade, order=order_payload, gate=gate_result
                )
                if live_res.get("status") in ("EXECUTED", "SUCCESS") or live_res.get("order_sent"):
                    ticket = live_res.get("ticket") or live_res.get("deal") or live_res.get("order")
                    self._record_owner_tickets(
                        live_res, symbol=symbol, action=action, lot=calculated_lot
                    )
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

                # Attach to the MT5 terminal running on this machine.
                # No credentials are ever requested from the user.
                if not is_mt5_connected():
                    await asyncio.to_thread(ensure_mt5_connected)

                if is_mt5_connected():
                    # Exit management runs alongside the scan: closing a
                    # position must never hold up the next scan cycle.
                    if self._manage_task is None or self._manage_task.done():
                        self._manage_task = asyncio.create_task(self._manage_positions())

                    positions = await asyncio.to_thread(get_positions) or []
                    open_count = len(positions)
                    if open_count < self.max_positions:
                        open_symbols = {
                            pos_field(p, "symbol", "") for p in positions
                        }
                        account = await asyncio.to_thread(get_account_info) or {}

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

        if self._manage_task and not self._manage_task.done():
            self._manage_task.cancel()
        self.running = False


auto_trader = AutoTrader()
