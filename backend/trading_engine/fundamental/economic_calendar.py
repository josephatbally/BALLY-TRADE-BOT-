"""
BALLY FLOW - Economic Calendar Layer

Fundamental calendar adapter.

This module does not invent economic events.
A provider may be injected by the application.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


HIGH_IMPACT_LEVELS = {"HIGH", "CRITICAL"}
MEDIUM_IMPACT_LEVELS = {"MEDIUM", "MODERATE"}


def _normalize_impact(value: Any) -> str:
    text = str(value or "UNKNOWN").strip().upper()

    if text in {"3", "HIGH", "HIGH_IMPACT", "CRITICAL"}:
        return "HIGH"

    if text in {"2", "MEDIUM", "MODERATE"}:
        return "MEDIUM"

    if text in {"1", "LOW"}:
        return "LOW"

    return "UNKNOWN"


def _normalize_event(event: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(event, dict):
        return None

    name = (
        event.get("name")
        or event.get("event")
        or event.get("title")
        or ""
    )

    if not str(name).strip():
        return None

    impact = _normalize_impact(
        event.get("impact")
        or event.get("importance")
        or event.get("priority")
    )

    currency = str(
        event.get("currency")
        or event.get("country_currency")
        or ""
    ).upper().strip()

    timestamp = (
        event.get("timestamp")
        or event.get("time")
        or event.get("datetime")
    )

    return {
        "name": str(name).strip(),
        "impact": impact,
        "currency": currency,
        "timestamp": timestamp,
        "actual": event.get("actual"),
        "forecast": event.get("forecast"),
        "previous": event.get("previous"),
        "source": event.get("source"),
    }


def get_events(
    symbol: str,
    provider: Any = None,
) -> Dict[str, Any]:
    """
    Obtain economic-calendar events from an injected provider.

    Supported provider styles:

        provider.get_events(symbol)
        provider.events(symbol)

    No network calls are performed here.
    """

    symbol = str(symbol or "").strip().upper()

    if not symbol:
        return {
            "status": "INVALID",
            "symbol": symbol,
            "events": [],
            "provider_available": False,
        }

    if provider is None:
        try:
            from backend.trading_engine.fundamental.live_news_provider import get_default_fundamental_provider
            provider = get_default_fundamental_provider()
        except Exception:
            return {
                "status": "NO_PROVIDER",
                "symbol": symbol,
                "events": [],
                "provider_available": False,
            }

    try:
        if hasattr(provider, "get_events"):
            raw_events = provider.get_events(symbol)
        elif hasattr(provider, "events"):
            raw_events = provider.events(symbol)
        elif callable(provider):
            raw_events = provider(symbol)
        else:
            return {
                "status": "INVALID_PROVIDER",
                "symbol": symbol,
                "events": [],
                "provider_available": False,
            }

        if raw_events is None:
            raw_events = []

        if isinstance(raw_events, dict):
            raw_events = raw_events.get("events", [])

        events: List[Dict[str, Any]] = []

        for item in raw_events:
            normalized = _normalize_event(item)
            if normalized is not None:
                events.append(normalized)

        high_impact = [
            event for event in events
            if event["impact"] in HIGH_IMPACT_LEVELS
        ]

        return {
            "status": "READY",
            "symbol": symbol,
            "events": events,
            "event_count": len(events),
            "high_impact_events": high_impact,
            "high_impact_count": len(high_impact),
            "provider_available": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        return {
            "status": "ERROR",
            "symbol": symbol,
            "events": [],
            "event_count": 0,
            "high_impact_events": [],
            "high_impact_count": 0,
            "provider_available": True,
            "error": str(exc),
        }


def analyze_calendar(
    symbol: str,
    provider: Any = None,
) -> Dict[str, Any]:
    """Compatibility alias."""

    return get_events(
        symbol=symbol,
        provider=provider,
    )
