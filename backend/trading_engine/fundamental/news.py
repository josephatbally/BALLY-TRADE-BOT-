"""
BALLY FLOW - Fundamental News Source Layer

News adapter.

No fake news is generated.
News must come from an injected provider.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _normalize_article(article: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(article, dict):
        return None

    title = (
        article.get("title")
        or article.get("headline")
        or article.get("name")
        or ""
    )

    if not str(title).strip():
        return None

    description = (
        article.get("description")
        or article.get("summary")
        or ""
    )

    return {
        "title": str(title).strip(),
        "description": str(description).strip(),
        "source": article.get("source"),
        "url": article.get("url"),
        "timestamp": (
            article.get("timestamp")
            or article.get("time")
            or article.get("datetime")
        ),
        "currency": str(
            article.get("currency")
            or ""
        ).upper().strip(),
        "importance": str(
            article.get("importance")
            or article.get("impact")
            or "UNKNOWN"
        ).upper(),
    }


def get_news(
    symbol: str,
    provider: Any = None,
) -> Dict[str, Any]:

    symbol = str(symbol or "").strip().upper()

    if not symbol:
        return {
            "status": "INVALID",
            "symbol": symbol,
            "articles": [],
        }

    if provider is None:
        try:
            from backend.trading_engine.fundamental.live_news_provider import get_default_fundamental_provider
            provider = get_default_fundamental_provider()
        except Exception:
            return {
                "status": "NO_PROVIDER",
                "symbol": symbol,
                "articles": [],
                "provider_available": False,
            }

    try:
        if hasattr(provider, "get_news"):
            raw = provider.get_news(symbol)
        elif hasattr(provider, "news"):
            raw = provider.news(symbol)
        elif callable(provider):
            raw = provider(symbol)
        else:
            return {
                "status": "INVALID_PROVIDER",
                "symbol": symbol,
                "articles": [],
                "provider_available": False,
            }

        if raw is None:
            raw = []

        if isinstance(raw, dict):
            raw = raw.get("articles", raw.get("news", []))

        articles: List[Dict[str, Any]] = []

        for item in raw:
            normalized = _normalize_article(item)

            if normalized is not None:
                articles.append(normalized)

        return {
            "status": "READY",
            "symbol": symbol,
            "articles": articles,
            "article_count": len(articles),
            "provider_available": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        return {
            "status": "ERROR",
            "symbol": symbol,
            "articles": [],
            "article_count": 0,
            "provider_available": True,
            "error": str(exc),
        }


def fetch_news(
    symbol: str,
    provider: Any = None,
) -> Dict[str, Any]:
    """Compatibility alias."""

    return get_news(
        symbol=symbol,
        provider=provider,
    )
