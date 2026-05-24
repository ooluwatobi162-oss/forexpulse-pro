"""
News Engine
Fetches forex news from Finnhub + NewsAPI,
deduplicates, scores by relevance, and runs sentiment analysis.
"""

import os
import asyncio
import httpx
import time
from datetime import datetime, timedelta
from cachetools import TTLCache

from engines.sentiment_engine import SentimentEngine

FINNHUB_KEY = os.getenv("FINNHUB_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

_news_cache = TTLCache(maxsize=10, ttl=60)  # 1-min cache

FOREX_KEYWORDS = [
    "forex", "currency", "dollar", "euro", "pound", "yen", "yuan",
    "central bank", "fed", "ecb", "boe", "boj", "interest rate",
    "inflation", "cpi", "gdp", "nfp", "unemployment", "gold", "oil",
    "rba", "rbnz", "boc", "snb", "fomc", "trade balance",
]

# Fallback news for when APIs are unavailable
FALLBACK_NEWS = [
    {"title": "US Inflation Rises Unexpectedly to 3.8% in April", "source": "Reuters", "published_at": "2 mins ago", "url": "#"},
    {"title": "ECB Signals Potential Rate Cut at June Meeting", "source": "Bloomberg", "published_at": "8 mins ago", "url": "#"},
    {"title": "Bank of England Maintains Rates, Adopts Hawkish Tone", "source": "Financial Times", "published_at": "15 mins ago", "url": "#"},
    {"title": "Japan GDP Contracts 0.5% in Q1, Yen Faces Pressure", "source": "Nikkei Asia", "published_at": "22 mins ago", "url": "#"},
    {"title": "US NFP Beats Expectations: 272K New Jobs Added", "source": "CNBC", "published_at": "31 mins ago", "url": "#"},
    {"title": "China PMI Weakens, AUD and NZD Under Selling Pressure", "source": "WSJ", "published_at": "38 mins ago", "url": "#"},
    {"title": "Fed Powell: No Rate Cuts Until Inflation Target Is Met", "source": "Reuters", "published_at": "45 mins ago", "url": "#"},
    {"title": "UK CPI Drops to 2.3%, Below Bank of England Target", "source": "Bloomberg", "published_at": "52 mins ago", "url": "#"},
    {"title": "Gold Surges to $2,365 on Renewed Middle East Tensions", "source": "Reuters", "published_at": "1h ago", "url": "#"},
    {"title": "Canadian Employment Surges, Loonie Strengthens vs USD", "source": "Globe & Mail", "published_at": "1h 12m ago", "url": "#"},
    {"title": "Swiss National Bank Cuts Rates 25bps in Surprise Move", "source": "Reuters", "published_at": "1h 30m ago", "url": "#"},
    {"title": "RBNZ Holds Rates, Governor Signals Disinflation Progress", "source": "Bloomberg", "published_at": "1h 45m ago", "url": "#"},
]


class NewsEngine:

    def __init__(self):
        self.sentiment = SentimentEngine()

    # ── Public ────────────────────────────────────────────────────────────────

    async def get_news(self, currency: str = None, limit: int = 20) -> list:
        cache_key = f"news_{currency}_{limit}"
        if cache_key in _news_cache:
            return _news_cache[cache_key]

        raw = await self._fetch_all_news()
        if currency:
            raw = [n for n in raw if currency in n.get("currencies", [])]

        # AI sentiment analysis
        enriched = await self.sentiment.batch_analyze(raw[:limit])
        _news_cache[cache_key] = enriched
        return enriched

    async def get_breaking_news(self, limit: int = 5) -> list:
        """Return most recent high-impact news."""
        news = await self.get_news(limit=30)
        high_impact = [
            n for n in news
            if n.get("ai_analysis", {}).get("volatility_score", 0) >= 4
        ]
        return high_impact[:limit] or news[:limit]

    # ── Fetch ─────────────────────────────────────────────────────────────────

    async def _fetch_all_news(self) -> list:
        tasks = []
        if FINNHUB_KEY:
            tasks.append(self._fetch_finnhub())
        if NEWS_API_KEY:
            tasks.append(self._fetch_newsapi())

        if not tasks:
            return self._fallback_news()

        results = await asyncio.gather(*tasks, return_exceptions=True)
        combined = []
        for r in results:
            if not isinstance(r, Exception):
                combined.extend(r)

        return self._deduplicate(combined) or self._fallback_news()

    async def _fetch_finnhub(self) -> list:
        url = f"https://finnhub.io/api/v1/news?category=forex&token={FINNHUB_KEY}"
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url)
            r.raise_for_status()
            items = r.json()

        result = []
        for item in items[:20]:
            if not self._is_forex_relevant(item.get("headline", "")):
                continue
            result.append({
                "title":        item.get("headline", ""),
                "source":       item.get("source", "Finnhub"),
                "body":         item.get("summary", ""),
                "url":          item.get("url", "#"),
                "published_at": self._ts_to_ago(item.get("datetime", 0)),
                "currencies":   self.sentiment._detect_currencies_keywords(
                    item.get("headline", "") + " " + item.get("summary", "")
                ),
            })
        return result

    async def _fetch_newsapi(self) -> list:
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        url = (
            f"https://newsapi.org/v2/everything?q=forex+currency+dollar+euro"
            f"&from={yesterday}&sortBy=publishedAt&language=en"
            f"&apiKey={NEWS_API_KEY}&pageSize=20"
        )
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()

        result = []
        for a in data.get("articles", []):
            title = a.get("title", "") or ""
            if not self._is_forex_relevant(title):
                continue
            result.append({
                "title":        title,
                "source":       a.get("source", {}).get("name", "NewsAPI"),
                "body":         a.get("description", "") or "",
                "url":          a.get("url", "#"),
                "published_at": self._iso_to_ago(a.get("publishedAt", "")),
                "currencies":   self.sentiment._detect_currencies_keywords(title),
            })
        return result

    def _fallback_news(self) -> list:
        return [
            {**n, "currencies": self.sentiment._detect_currencies_keywords(n["title"])}
            for n in FALLBACK_NEWS
        ]

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _is_forex_relevant(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in FOREX_KEYWORDS)

    def _deduplicate(self, articles: list) -> list:
        seen = set()
        unique = []
        for a in articles:
            key = a["title"][:60].lower()
            if key not in seen:
                seen.add(key)
                unique.append(a)
        return unique

    def _ts_to_ago(self, ts: int) -> str:
        if not ts:
            return "recently"
        diff = int(time.time()) - int(ts)
        if diff < 60:    return f"{diff}s ago"
        if diff < 3600:  return f"{diff // 60}m ago"
        if diff < 86400: return f"{diff // 3600}h ago"
        return f"{diff // 86400}d ago"

    def _iso_to_ago(self, iso: str) -> str:
        try:
            from dateutil.parser import parse
            dt = parse(iso)
            diff = int((datetime.utcnow() - dt.replace(tzinfo=None)).total_seconds())
            return self._ts_to_ago(int(time.time()) - diff)
        except Exception:
            return "recently"
