# ForexPulse Pro — API Reference

Base URL: `https://forexpulse-pro-api.onrender.com`

Interactive docs: `{BASE_URL}/docs` (Swagger UI)

---

## Authentication

Currently open (add API key middleware for production).

---

## Endpoints

### Health

```
GET /health
→ { "status": "healthy", "timestamp": 1234567890 }
```

---

### Prices

```
GET /api/prices
→ {
    "EUR/USD": { "price": 1.08621, "change": 0.0023, "change_pct": 0.21, "source": "TwelveData", "ts": 1234567890 },
    "GBP/USD": { ... },
    ...
  }

GET /api/prices/{pair}
  pair: EUR-USD, GBP-USD, USD-JPY, XAU-USD, etc.
→ { "price": 1.08621, "change": 0.0023, "change_pct": 0.21, ... }

GET /api/prices/strength
→ { "USD": 72.0, "EUR": 58.1, "GBP": 45.2, ... }

GET /api/prices/movers?n=5
→ [{ "pair": "XAU/USD", "price": 2341.5, "change_pct": 0.36 }, ...]

GET /api/prices/sentiment
→ {
    "fear_greed_index": 62,
    "fear_greed_label": "Greed",
    "overall_sentiment": "RISK-ON",
    "usd_sentiment": "BULLISH",
    "dxy": 104.2,
    "vix": 14.2,
    "currency_strength": { "USD": 72, ... }
  }
```

---

### News

```
GET /api/news?currency=USD&limit=20
  currency: USD | EUR | GBP | JPY | AUD | CAD | NZD | CHF (optional)
  limit: 1–50 (default 20)
→ [{
    "title": "US Inflation Rises...",
    "source": "Reuters",
    "published_at": "5m ago",
    "url": "https://...",
    "currencies": ["USD"],
    "ai_analysis": {
      "affected_currencies": ["USD", "EUR"],
      "primary_currency": "USD",
      "impact": "bullish",
      "trade_bias": "EURUSD SELL",
      "confidence": 87,
      "volatility_score": 4,
      "sentiment_summary": "USD strengthening on CPI beat",
      "reasoning": ["...", "...", "..."]
    }
  }, ...]

GET /api/news/breaking?limit=5
→ Top 5 high-volatility news items
```

---

### Signals

```
GET /api/signals?timeframe=H4
  timeframe: M15 | H1 | H4 | D1 | W1 (default H4)
→ [{
    "pair": "EUR/USD",
    "direction": "SELL",
    "entry": 1.0862,
    "tp1": 1.0830,
    "tp2": 1.0790,
    "sl": 1.0895,
    "confidence": 87,
    "risk_level": "LOW",
    "risk_reward": 2.1,
    "reasons": ["...", "...", "...", "..."],
    "invalidation": "Signal invalid if...",
    "timeframe": "H4",
    "expiry_hours": 24,
    "ai_score": 74,
    "trend": { "direction": "DOWN", "strength": "MODERATE", "slope_pct": -0.21 },
    "breakouts": [],
    "support_levels": [1.0820, 1.0790],
    "resistance_levels": [1.0895, 1.0920]
  }, ...]

GET /api/signals/top?n=5
→ Top 5 highest-confidence signals

GET /api/signals/{pair}?timeframe=H4
  pair: EUR-USD, GBP-USD, etc.
→ Single signal for that pair
```

---

### Technical Analysis

```
GET /api/analysis/{pair}?timeframe=H1
  pair: EUR-USD, GBP-USD, USD-JPY, XAU-USD, etc.
  timeframe: M15 | H1 | H4 | D1 | W1
→ {
    "pair": "EUR/USD",
    "timeframe": "H1",
    "current_price": 1.08621,
    "overall_signal": "BULLISH",
    "ai_score": 74,
    "buy_count": 8,
    "sell_count": 3,
    "neutral_count": 1,
    "indicators": [
      { "name": "RSI (14)", "value": 58.4, "signal": "BUY", "progress": 58 },
      { "name": "MACD", "value": "+0.0021", "signal": "BUY", "progress": 72 },
      ...
    ],
    "patterns": [
      { "name": "Bullish Engulfing", "type": "bullish", "confidence": 84 },
      ...
    ],
    "support_levels": [1.0820, 1.0790, 1.0750],
    "resistance_levels": [1.0895, 1.0920, 1.0950],
    "smc": [
      { "concept": "BOS", "description": "Break of Structure — Bullish confirmed", "bias": "bullish" },
      { "concept": "Order Block", "description": "Bullish OB @ 1.08200", "bias": "bullish" },
      ...
    ],
    "trend": { "direction": "UP", "strength": "MODERATE", "slope_pct": 0.21 },
    "breakouts": [],
    "key_levels": { "ema20": 1.0851, "ema50": 1.0832, "ema200": 1.0780, ... }
  }
```

---

### Economic Calendar

```
GET /api/calendar
→ [{
    "time": "14:30",
    "event": "US Core CPI m/m",
    "currency": "USD",
    "impact": "high",
    "forecast": "0.3%",
    "previous": "0.4%",
    "description": "Consumer Price Index...",
    "countdown": "2h 14m",
    "seconds_until": 8040
  }, ...]

GET /api/calendar/upcoming?n=5
→ Next 5 events sorted by time
```

---

### AI Chat

```
POST /api/chat
Content-Type: application/json

{
  "message": "Is EUR/USD bullish today?",
  "history": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Good morning, trader!" }
  ]
}

→ {
    "reply": "EUR/USD is showing bearish momentum...",
    "model": "claude-sonnet-4",
    "status": "success"
  }
```

---

### WebSockets

```
WS /ws/prices
← Every 2 seconds: { "type": "prices", "data": { "EUR/USD": {...}, ... } }

WS /ws/news
← On new high-impact news: { "type": "news", "data": { ...article } }
```
