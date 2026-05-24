# 🚀 ForexPulse Pro — Deployment Guide

## Overview

| Component | Platform | Cost |
|-----------|----------|------|
| Frontend  | Vercel   | Free |
| Backend   | Render   | Free (750h/mo) |
| Database  | Supabase | Free (500MB) |

---

## Step 1 — Get API Keys

### Required (Free Tiers Available)

| Service | URL | Free Limit | Used For |
|---------|-----|-----------|---------|
| Anthropic Claude | platform.anthropic.com | Pay-per-use | AI analysis, chat, signals |
| Twelve Data | twelvedata.com | 800 req/day | Live forex prices |
| Finnhub | finnhub.io | 60 req/min | Forex news |
| NewsAPI | newsapi.org | 100 req/day | News feed |
| Supabase | supabase.com | 500MB | Database |

### Optional (Enhanced Data)

| Service | URL | Free Limit | Used For |
|---------|-----|-----------|---------|
| Alpha Vantage | alphavantage.co | 25 req/day | Historical data |
| Trading Economics | tradingeconomics.com | Limited | Economic calendar |

---

## Step 2 — Setup Supabase Database

1. Go to [supabase.com](https://supabase.com) → Create project
2. Open SQL Editor and run:

```sql
-- Signals table
CREATE TABLE signals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  pair TEXT NOT NULL,
  direction TEXT NOT NULL,
  entry DECIMAL NOT NULL,
  tp1 DECIMAL,
  tp2 DECIMAL,
  sl DECIMAL NOT NULL,
  confidence INTEGER,
  risk_level TEXT,
  reasons JSONB,
  timeframe TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  is_active BOOLEAN DEFAULT TRUE
);

-- News table
CREATE TABLE news_cache (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  source TEXT,
  url TEXT,
  published_at TEXT,
  currencies JSONB,
  ai_analysis JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Community posts
CREATE TABLE community_posts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  username TEXT NOT NULL,
  pair TEXT,
  direction TEXT,
  content TEXT NOT NULL,
  likes INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE news_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE community_posts ENABLE ROW LEVEL SECURITY;

-- Public read access
CREATE POLICY "Public read signals" ON signals FOR SELECT USING (true);
CREATE POLICY "Public read news" ON news_cache FOR SELECT USING (true);
CREATE POLICY "Public read posts" ON community_posts FOR SELECT USING (true);
```

3. Go to **Settings → API** → copy your `URL` and `anon key`

---

## Step 3 — Deploy Backend to Render

1. Push your project to GitHub:
```bash
git init
git add .
git commit -m "Initial commit — ForexPulse Pro"
git remote add origin https://github.com/YOUR_USERNAME/forexpulse-pro
git push -u origin main
```

2. Go to [render.com](https://render.com) → New → Web Service

3. Connect your GitHub repo, then configure:

| Setting | Value |
|---------|-------|
| **Root Directory** | `backend` |
| **Runtime** | Python 3.11 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free |

4. Add Environment Variables in Render dashboard:

```
ANTHROPIC_API_KEY     = sk-ant-...
TWELVE_DATA_KEY       = ...
FINNHUB_KEY           = ...
NEWS_API_KEY          = ...
SUPABASE_URL          = https://xxx.supabase.co
SUPABASE_KEY          = your-anon-key
FRONTEND_URL          = https://your-app.vercel.app
ENVIRONMENT           = production
```

5. Deploy → Note your backend URL: `https://forexpulse-pro-api.onrender.com`

---

## Step 4 — Deploy Frontend to Vercel

1. Update `frontend/js/api.js` — set your Render backend URL:
```js
const API_BASE = 'https://forexpulse-pro-api.onrender.com/api';
const WS_BASE  = 'wss://forexpulse-pro-api.onrender.com/ws';
```

2. Install Vercel CLI:
```bash
npm install -g vercel
```

3. Deploy:
```bash
vercel --prod
```

4. Or connect GitHub repo to Vercel dashboard for automatic deploys on push.

---

## Step 5 — Update CORS

After getting your Vercel URL (e.g. `https://forexpulse-pro.vercel.app`):

1. Go to Render dashboard → Environment
2. Update `FRONTEND_URL` = `https://forexpulse-pro.vercel.app`
3. Redeploy backend

---

## Step 6 — Verify Everything Works

```bash
# Test backend health
curl https://forexpulse-pro-api.onrender.com/health

# Test prices
curl https://forexpulse-pro-api.onrender.com/api/prices

# Test news
curl https://forexpulse-pro-api.onrender.com/api/news

# Test signals
curl https://forexpulse-pro-api.onrender.com/api/signals

# Test AI chat
curl -X POST https://forexpulse-pro-api.onrender.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Is EUR/USD bullish today?"}'
```

---

## Common Issues

### Backend not starting
- Check `requirements.txt` is complete
- Verify Python version is 3.11+
- Check all env variables are set

### CORS errors in browser
- Ensure `FRONTEND_URL` matches your exact Vercel URL
- Check for trailing slashes

### API rate limits
- Twelve Data: 800 req/day free → upgrade or add Alpha Vantage fallback
- Finnhub: 60 req/min free → sufficient for production
- NewsAPI: 100 req/day free → cache aggressively (already done)

### WebSocket not connecting on Render free tier
- Render free tier sleeps after 15min inactivity
- Upgrade to Starter ($7/mo) for always-on service
- Alternative: use polling instead of WebSockets for free tier

---

## Performance Tips

1. **Cache everything** — The backend uses TTLCache; extend TTLs for free API tiers
2. **Render free tier sleeps** — Add a health check cron job (UptimeRobot is free)
3. **Rate limit protection** — slowapi is already configured; adjust limits as needed
4. **CDN for static assets** — Vercel handles this automatically

---

## Local Development

```bash
# Terminal 1 — Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Fill in your keys
uvicorn main:app --reload

# Terminal 2 — Frontend
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

Backend API docs available at: `http://localhost:8000/docs`
