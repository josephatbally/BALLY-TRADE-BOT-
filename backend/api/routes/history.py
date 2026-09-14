from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from backend.trading_engine.market_data.mt5_connection import (
    get_history_deals,
    is_mt5_connected,
)

router = APIRouter()

def _read_value(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if hasattr(value, name):
        return getattr(value, name)
    if isinstance(value, dict):
        return value.get(name, default)
    return default

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _deal_datetime(deal: Any) -> Optional[str]:
    timestamp = _read_value(deal, "time", None)
    if timestamp is None:
        return None
    try:
        return datetime.fromtimestamp(
            float(timestamp),
            tz=timezone.utc,
        ).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None

def _normalize_deal(deal: Any) -> Dict[str, Any]:
    return {
        "ticket": _safe_int(_read_value(deal, "ticket", 0)),
        "order": _safe_int(_read_value(deal, "order", 0)),
        "position_id": _safe_int(_read_value(deal, "position_id", 0)),
        "symbol": str(_read_value(deal, "symbol", "") or ""),
        "type": _safe_int(_read_value(deal, "type", -1), -1),
        "entry": _safe_int(_read_value(deal, "entry", -1), -1),
        "volume": _safe_float(_read_value(deal, "volume", 0.0)),
        "price": _safe_float(_read_value(deal, "price", 0.0)),
        "profit": _safe_float(_read_value(deal, "profit", 0.0)),
        "swap": _safe_float(_read_value(deal, "swap", 0.0)),
        "commission": _safe_float(_read_value(deal, "commission", 0.0)),
        "fee": _safe_float(_read_value(deal, "fee", 0.0)),
        "magic": _safe_int(_read_value(deal, "magic", 0)),
        "reason": _safe_int(_read_value(deal, "reason", -1), -1),
        "comment": _read_value(deal, "comment", None),
        "time": _deal_datetime(deal),
        "time_msc": _safe_int(_read_value(deal, "time_msc", 0)),
    }

@router.get("/summary")
def get_history_summary(days: int = 7) -> Dict[str, Any]:
    """
    Return aggregated performance metrics for the given lookback period (default: 7 days / weekly).
    """
    if not is_mt5_connected():
        return {
            "status": "OFFLINE",
            "connected": False,
            "days": days,
            "win_rate": 0.0,
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "profit_factor": 0.0,
            "net_profit": 0.0,
        }

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    try:
        raw_deals = get_history_deals(date_from=start, date_to=end) or []
        closed_deals = [
            deal for deal in raw_deals
            if abs(_safe_float(_read_value(deal, "profit", 0.0))) > 0.0001
            or _safe_int(_read_value(deal, "entry", -1)) == 1 # DEAL_ENTRY_OUT
        ]

        wins = 0
        losses = 0
        gross_profit = 0.0
        gross_loss = 0.0
        net_profit = 0.0

        for deal in closed_deals:
            profit = _safe_float(_read_value(deal, "profit", 0.0))
            swap = _safe_float(_read_value(deal, "swap", 0.0))
            commission = _safe_float(_read_value(deal, "commission", 0.0))
            deal_net = profit + swap + commission
            net_profit += deal_net

            if profit > 0:
                wins += 1
                gross_profit += profit
            elif profit < 0:
                losses += 1
                gross_loss += abs(profit)

        total_trades = wins + losses
        win_rate = round((wins / total_trades * 100.0), 1) if total_trades > 0 else 0.0
        profit_factor = round((gross_profit / gross_loss), 2) if gross_loss > 0 else (round(gross_profit, 2) if gross_profit > 0 else 0.0)

        return {
            "status": "READY",
            "connected": True,
            "days": days,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "profit_factor": profit_factor,
            "net_profit": round(net_profit, 2),
        }
    except Exception as exc:
        return {
            "status": "ERROR",
            "connected": True,
            "days": days,
            "win_rate": 0.0,
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "profit_factor": 0.0,
            "net_profit": 0.0,
            "error": str(exc),
        }

@router.get("")
def get_history(
    days: int = 30,
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Return read-only MT5 historical deal data.
    """
    if days < 1 or days > 3650:
        raise HTTPException(
            status_code=400,
            detail="days must be between 1 and 3650",
        )
    if not is_mt5_connected():
        return {
            "status": "OFFLINE",
            "connected": False,
            "days": days,
            "symbol": symbol,
            "count": 0,
            "deals": [],
        }
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    try:
        raw_deals = get_history_deals(
            date_from=start,
            date_to=end,
        ) or []
        deals = [
            _normalize_deal(deal)
            for deal in raw_deals
        ]
        return {
            "status": "READY",
            "connected": True,
            "days": days,
            "symbol": symbol,
            "from": start.isoformat(),
            "to": end.isoformat(),
            "count": len(deals),
            "deals": deals,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Unable to retrieve MT5 historical deals.",
                "error": str(exc),
            },
        ) from exc