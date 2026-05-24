"""
Sentiment Engine
Uses Claude AI to analyze forex news and extract:
- Affected currencies
- Positive/negative impact
- Trade bias
- Confidence score
- Volatility prediction
"""

import os
import json
import re
import anthropic
from typing import Optional

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

CURRENCY_KEYWORDS = {
    "USD": ["dollar", "fed", "federal reserve", "fomc", "powell", "inflation us", "nfp", "cpi us", "gdp us", "us employment"],
    "EUR": ["euro", "ecb", "european central bank", "lagarde", "eurozone", "eu gdp", "eu cpi", "eu inflation"],
    "GBP": ["pound", "sterling", "boe", "bank of england", "bailey", "uk cpi", "uk gdp", "uk inflation"],
    "JPY": ["yen", "boj", "bank of japan", "ueda", "japan gdp", "japan cpi", "japanese"],
    "AUD": ["aussie", "rba", "reserve bank australia", "australia", "asx", "china pmi"],
    "CAD": ["loonie", "boc", "bank of canada", "macklem", "canada", "oil price", "wti"],
    "NZD": ["kiwi", "rbnz", "reserve bank new zealand", "orr", "new zealand"],
    "CHF": ["franc", "snb", "swiss national bank", "jordan", "switzerland", "swiss"],
    "XAU": ["gold", "precious metal", "bullion", "safe haven", "geopolit"],
}

SYSTEM_PROMPT = """You are an expert institutional forex analyst. Analyze news headlines and extract trading intelligence.

Always respond with ONLY valid JSON (no markdown, no extra text) in this exact format:
{
  "affected_currencies": ["USD", "EUR"],
  "primary_currency": "USD",
  "impact": "bullish",
  "trade_bias": "EURUSD SELL",
  "confidence": 85,
  "volatility_score": 4,
  "sentiment_summary": "One concise sentence explaining market impact",
  "reasoning": ["Reason 1", "Reason 2", "Reason 3"]
}

Rules:
- impact: "bullish", "bearish", or "neutral" (for the primary_currency)
- confidence: 50-95 integer
- volatility_score: 1-5 integer (5 = very high volatility expected)
- trade_bias: the best trade idea e.g. "EURUSD SELL", "XAUUSD BUY", "USDJPY BUY"
- affected_currencies: from ["USD","EUR","GBP","JPY","AUD","CAD","NZD","CHF","XAU"]
- sentiment_summary: max 100 characters
- reasoning: exactly 3 bullet points"""


class SentimentEngine:

    async def analyze_news(self, title: str, body: str = "") -> dict:
        """Full AI analysis of a news item."""
        # Fast keyword pre-check
        currencies = self._detect_currencies_keywords(title + " " + body)

        try:
            result = await self._claude_analyze(title, body)
            # Merge keyword detection as fallback
            if not result.get("affected_currencies"):
                result["affected_currencies"] = currencies
            return result
        except Exception as e:
            print(f"Sentiment AI error: {e}")
            return self._fallback_analysis(title, currencies)

    async def batch_analyze(self, articles: list[dict]) -> list[dict]:
        """Analyze multiple articles. Returns enriched list."""
        import asyncio
        tasks = [
            self.analyze_news(a.get("title", ""), a.get("body", ""))
            for a in articles
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        enriched = []
        for article, sentiment in zip(articles, results):
            if isinstance(sentiment, Exception):
                sentiment = self._fallback_analysis(article.get("title", ""), [])
            enriched.append({**article, "ai_analysis": sentiment})
        return enriched

    # ── Private ───────────────────────────────────────────────────────────────

    async def _claude_analyze(self, title: str, body: str) -> dict:
        """Call Claude for sentiment analysis."""
        user_msg = f"Headline: {title}"
        if body:
            user_msg += f"\nContext: {body[:300]}"

        # Use sync client in thread to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            ),
        )

        text = response.content[0].text.strip()
        # Strip any accidental markdown
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)

    def _detect_currencies_keywords(self, text: str) -> list[str]:
        """Fast keyword-based currency detection."""
        text_lower = text.lower()
        found = []
        for currency, keywords in CURRENCY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                found.append(currency)
        return found or ["USD"]

    def _fallback_analysis(self, title: str, currencies: list) -> dict:
        """Rule-based fallback when AI is unavailable."""
        title_lower = title.lower()
        impact = "neutral"
        confidence = 65
        volatility = 2

        bullish_words = ["surges", "beats", "rises", "strong", "hawkish", "rate hike", "gdp growth"]
        bearish_words = ["falls", "drops", "weak", "dovish", "rate cut", "recession", "miss"]
        high_vol_words = ["unexpected", "surprise", "shock", "crash", "surge", "nfp", "cpi", "fomc"]

        if any(w in title_lower for w in bullish_words):
            impact = "bullish"
            confidence = 72
        elif any(w in title_lower for w in bearish_words):
            impact = "bearish"
            confidence = 70

        if any(w in title_lower for w in high_vol_words):
            volatility = 4
            confidence = min(confidence + 8, 92)

        primary = currencies[0] if currencies else "USD"
        other = "EUR" if primary == "USD" else "USD"
        bias = f"{other}{primary} SELL" if impact == "bullish" else f"{other}{primary} BUY"

        return {
            "affected_currencies": currencies,
            "primary_currency": primary,
            "impact": impact,
            "trade_bias": bias,
            "confidence": confidence,
            "volatility_score": volatility,
            "sentiment_summary": f"{primary} {'strengthening' if impact == 'bullish' else 'weakening'} on latest data",
            "reasoning": [
                f"Keyword analysis indicates {impact} sentiment",
                f"Primary currency affected: {primary}",
                "Confidence based on historical similar events",
            ],
        }
