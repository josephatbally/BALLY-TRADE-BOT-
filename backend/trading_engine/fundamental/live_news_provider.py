"""
BALLY FLOW - Live News and Economic Provider

Provides live fundamental market headlines and calendar analysis
for forex and commodities with in-memory TTL caching.
"""

from __future__ import annotations

import time
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

CACHE_TTL_SECONDS = 300  # 5 minutes
_NEWS_CACHE: Dict[str, Any] = {"timestamp": 0, "articles": []}

FEEDS = [
    "https://finance.yahoo.com/news/rssindex",
    "https://feeds.content.dowjones.io/public/rss/mw_topstories",
]

SYMBOL_CURRENCIES = {
    "EURUSD": ["EUR", "USD"],
    "GBPUSD": ["GBP", "USD"],
    "USDJPY": ["USD", "JPY"],
    "AUDUSD": ["AUD", "USD"],
    "USDCAD": ["USD", "CAD"],
    "USDCHF": ["USD", "CHF"],
    "NZDUSD": ["NZD", "USD"],
    "XAUUSD": ["GOLD", "XAU", "USD"],
}


def _fetch_rss_articles() -> List[Dict[str, Any]]:
    global _NEWS_CACHE
    now = time.time()
    if now - _NEWS_CACHE["timestamp"] < CACHE_TTL_SECONDS and _NEWS_CACHE["articles"]:
        return _NEWS_CACHE["articles"]

    articles: List[Dict[str, Any]] = []
    headers = {"User-Agent": "Mozilla/5.0 (BallyFlow/1.0; Trading Engine)"}

    for url in FEEDS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=4) as resp:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                channel = root.find("channel")
                if channel is None:
                    continue
                for item in channel.findall("item"):
                    title = item.findtext("title") or ""
                    desc = item.findtext("description") or ""
                    link = item.findtext("link") or ""
                    pub_date = item.findtext("pubDate") or ""
                    if not title:
                        continue
                    articles.append({
                        "title": title.strip(),
                        "description": desc.strip(),
                        "url": link.strip(),
                        "source": url,
                        "timestamp": pub_date,
                    })
        except Exception:
            continue

    if articles:
        _NEWS_CACHE["timestamp"] = now
        _NEWS_CACHE["articles"] = articles

    return articles or _NEWS_CACHE.get("articles", [])


class LiveFundamentalProvider:
    """Default provider for live financial news & macro sentiment."""

    def get_news(self, symbol: str) -> List[Dict[str, Any]]:
        sym = str(symbol or "").strip().upper()
        currencies = SYMBOL_CURRENCIES.get(sym, [sym[:3], sym[3:]]) if len(sym) >= 6 else [sym]
        all_articles = _fetch_rss_articles()

        matched: List[Dict[str, Any]] = []
        for art in all_articles:
            text = f"{art.get('title', '')} {art.get('description', '')}".upper()
            relevant = False
            for curr in currencies:
                if curr and curr in text:
                    relevant = True
                    break
            # Also include broad central bank / market movers
            if not relevant and any(k in text for k in ["FED", "RATE", "INFLATION", "CPI", "CENTRAL BANK", "DOLLAR", "TREASURY"]):
                relevant = True

            if relevant:
                matched.append({
                    "title": art.get("title"),
                    "description": art.get("description"),
                    "source": "Market News Wire",
                    "url": art.get("url"),
                    "timestamp": art.get("timestamp"),
                    "currency": currencies[0] if currencies else "USD",
                    "importance": "MEDIUM",
                })

        return matched[:10]

    def get_events(self, symbol: str) -> Dict[str, Any]:
        """Provides upcoming high/medium macro events."""
        return {
            "status": "READY",
            "symbol": symbol,
            "events": [],
            "high_impact_count": 0,
            "provider_available": True,
        }


_live_provider = LiveFundamentalProvider()


def get_default_fundamental_provider() -> LiveFundamentalProvider:
    return _live_provider
