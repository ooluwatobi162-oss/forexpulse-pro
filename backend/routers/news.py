"""routers/news.py"""
from fastapi import APIRouter, Query
from engines.news_engine import NewsEngine

router = APIRouter()
engine = NewsEngine()

@router.get("")
async def get_news(currency: str = Query(None), limit: int = Query(20, le=50)):
    return await engine.get_news(currency, limit)

@router.get("/breaking")
async def get_breaking_news(limit: int = Query(5, le=10)):
    return await engine.get_breaking_news(limit)
