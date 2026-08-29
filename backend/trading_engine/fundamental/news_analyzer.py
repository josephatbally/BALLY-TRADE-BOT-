"""
BALLY FLOW - News Analyzer

Converts raw fundamental news into normalized sentiment evidence.

This module does not make the final trading decision.
"""

from __future__ import annotations

from typing import Any, Dict


POSITIVE_WORDS = {
    "beat",
    "beats",
    "strong",
    "growth",
    "hawkish",
    "bullish",
    "higher",
    "surge",
    "rise",
    "rising",
    "improves",
    "improved",
    "positive",
    "optimistic",
}

NEGATIVE_WORDS = {
    "miss",
    "misses",
    "weak",
    "decline",
    "dovish",
    "bearish",
    "lower",
    "fall",
    "falling",
    "drops",
    "negative",
    "recession",
    "crisis",
    "risk",
    "risks",
}


def _score_text(text: str) -> float:
    words = {
        word.strip(".,!?;:()[]{}").lower()
        for word in text.split()
    }

    positive = len(words.intersection(POSITIVE_WORDS))
    negative = len(words.intersection(NEGATIVE_WORDS))

    if positive == 0 and negative == 0:
        return 0.0

    raw = (positive - negative) * 20.0

    return max(-100.0, min(100.0, raw))


def analyze_news(
    news_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:

    if not isinstance(news_result, dict):
        news_result = {}

    articles = news_result.get("articles", [])

    if not isinstance(articles, list):
        articles = []

    article_scores = []

    for article in articles:
        if not isinstance(article, dict):
            continue

        text = " ".join(
            str(article.get(key, "") or "")
            for key in ("title", "description")
        )

        score = _score_text(text)

        article_scores.append({
            "title": article.get("title", ""),
            "score": round(score, 2),
            "importance": article.get("importance", "UNKNOWN"),
        })

    if article_scores:
        average_score = sum(
            item["score"] for item in article_scores
        ) / len(article_scores)
    else:
        average_score = 0.0

    if average_score >= 20.0:
        sentiment = "BULLISH"
    elif average_score <= -20.0:
        sentiment = "BEARISH"
    else:
        sentiment = "NEUTRAL"

    return {
        "status": "READY",
        "article_count": len(article_scores),
        "sentiment": sentiment,
        "sentiment_score": round(average_score, 2),
        "articles": article_scores,
    }


def analyze_news_sentiment(
    news_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Compatibility alias."""

    return analyze_news(news_result)
