# ForexPulse Pro 🚀

> Bloomberg Terminal + TradingView + AI Forex Assistant — Combined into one elite forex intelligence platform.

![ForexPulse Pro](https://img.shields.io/badge/Status-Production%20Ready-00ff88?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge)
![Vercel](https://img.shields.io/badge/Frontend-Vercel-black?style=for-the-badge)

---

## 📁 Project Structure

```
forexpulse-pro/
├── frontend/                  # Static HTML/CSS/JS (deploy to Vercel)
│   ├── index.html             # Main terminal dashboard
│   ├── pages/
│   │   ├── signals.html       # AI Signal Center
│   │   ├── analysis.html      # Technical Analysis
│   │   ├── calendar.html      # Economic Calendar
│   │   ├── ai-analyst.html    # Full AI Chat
│   │   └── community.html     # Social Trading
│   ├── components/
│   │   ├── ticker.js          # Live ticker component
│   │   ├── charts.js          # Chart utilities
│   │   ├── chat.js            # AI chat component
│   │   └── signals.js         # Signal card renderer
│   ├── styles/
│   │   └── main.css           # Global styles
│   └── js/
│       ├── api.js             # API client
│       ├── state.js           # App state manager
│       └── utils.js           # Utilities
│
├── backend/                   # FastAPI backend (deploy to Render)
│   ├── main.py                # FastAPI app entry point
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment variables template
│   ├── routers/
│   │   ├── prices.py          # Live price endpoints
│   │   ├── news.py            # News feed endpoints
│   │   ├── signals.py         # AI signal endpoints
│   │   ├── analysis.py        # Technical analysis endpoints
│   │   ├── calendar.py        # Economic calendar endpoints
│   │   └── ai_chat.py         # AI analyst chat endpoints
│   ├── engines/
│   │   ├── signal_engine.py   # AI signal generation
│   │   ├── sentiment_engine.py # News sentiment analysis
│   │   ├── ta_engine.py       # Technical analysis engine
│   │   ├── currency_engine.py # Currency strength calculator
│   │   └── news_engine.py     # News fetching & processing
│   └── models/
│       ├── signal.py          # Pydantic signal models
│       ├── news.py            # News models
│       └── price.py           # Price models
│
├── docs/
│   ├── API.md                 # API documentation
│   └── DEPLOYMENT.md          # Deployment guide
│
├── vercel.json                # Vercel deployment config
└── README.md                  # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ (optional, for local dev server)
- API Keys (see Environment Variables)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # Fill in your API keys
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
# Option 1: Simple file server
python -m http.server 3000

# Option 2: VS Code Live Server extension
# Option 3: Deploy directly to Vercel (no build step needed)
```

---

## 🔑 Environment Variables

Create `backend/.env` from `.env.example`:

```env
# Anthropic AI
ANTHROPIC_API_KEY=sk-ant-...

# Market Data
ALPHA_VANTAGE_KEY=your_key
TWELVE_DATA_KEY=your_key
FINNHUB_KEY=your_key

# News
NEWS_API_KEY=your_key

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key

# CORS
FRONTEND_URL=https://your-app.vercel.app
```

---

## 🌐 Deployment

### Frontend → Vercel
```bash
npm install -g vercel
cd frontend
vercel --prod
```

### Backend → Render
1. Push to GitHub
2. Create new Web Service on render.com
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables in Render dashboard

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/prices` | Live forex prices |
| GET | `/api/prices/{pair}` | Single pair price |
| GET | `/api/news` | AI-analyzed news feed |
| GET | `/api/signals` | AI-generated signals |
| GET | `/api/signals/{pair}` | Signal for specific pair |
| GET | `/api/analysis/{pair}` | Technical analysis |
| GET | `/api/calendar` | Economic calendar |
| GET | `/api/strength` | Currency strength meter |
| GET | `/api/sentiment` | Market sentiment |
| POST | `/api/chat` | AI analyst chat |
| WS | `/ws/prices` | WebSocket live prices |
| WS | `/ws/news` | WebSocket news stream |

---

## 🧠 AI Features

- **Signal Engine**: Combines TA + fundamental + sentiment → BUY/SELL signals
- **Sentiment Engine**: Claude AI analyzes news impact on currencies
- **Currency Impact AI**: Auto-detects which currencies are affected by news
- **AI Analyst Chat**: Ask anything about markets, powered by Claude
- **Pattern Recognition**: Detects 15+ candlestick/chart patterns
- **SMC Analysis**: Smart Money Concepts (OB, FVG, liquidity zones)

---

## 📊 Data Sources

| Source | Used For | Free Tier |
|--------|----------|-----------|
| Alpha Vantage | Historical OHLCV | 25 req/day |
| Twelve Data | Real-time prices | 800 req/day |
| Finnhub | News + fundamentals | 60 req/min |
| NewsAPI | Forex news | 100 req/day |
| TradingEconomics | Economic calendar | Limited |

---

## 🛡️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Vanilla JS, TailwindCSS, Chart.js |
| Backend | Python 3.11, FastAPI, Uvicorn |
| AI | Anthropic Claude (claude-sonnet-4) |
| Database | Supabase (PostgreSQL) |
| Cache | Redis (optional, via Render) |
| Hosting | Vercel (FE) + Render (BE) |
| Real-time | WebSockets + Server-Sent Events |

---

## 📜 License

MIT License — Build something great.
