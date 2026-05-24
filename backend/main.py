"""
ForexPulse Pro — FastAPI Backend
Entry point: uvicorn main:app --reload
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

from routers import prices, news, signals, analysis, calendar, ai_chat
from engines.currency_engine import CurrencyEngine

# ─── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background tasks on startup, clean up on shutdown."""
    # Start price refresh task
    task = asyncio.create_task(broadcast_price_loop())
    yield
    task.cancel()

# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ForexPulse Pro API",
    description="Elite AI-powered forex intelligence platform backend",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS ────────────────────────────────────────────────────────────────────

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────

app.include_router(prices.router,   prefix="/api/prices",   tags=["Prices"])
app.include_router(news.router,     prefix="/api/news",     tags=["News"])
app.include_router(signals.router,  prefix="/api/signals",  tags=["Signals"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(ai_chat.router,  prefix="/api/chat",     tags=["AI Chat"])

# ─── WebSocket Manager ───────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active_connections.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.active_connections.remove(d)

manager = ConnectionManager()

# ─── WebSocket: Live Prices ───────────────────────────────────────────────────

@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; prices are pushed by broadcast_price_loop
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_price_loop():
    """Push price updates to all WebSocket clients every 2 seconds."""
    engine = CurrencyEngine()
    while True:
        try:
            prices = await engine.get_live_prices()
            await manager.broadcast({"type": "prices", "data": prices})
        except Exception as e:
            print(f"Price broadcast error: {e}")
        await asyncio.sleep(2)

# ─── WebSocket: News Stream ───────────────────────────────────────────────────

news_manager = ConnectionManager()

@app.websocket("/ws/news")
async def websocket_news(websocket: WebSocket):
    await news_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        news_manager.disconnect(websocket)

# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "service": "ForexPulse Pro API",
        "version": "1.0.0",
        "docs": "/docs",
    }

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}
