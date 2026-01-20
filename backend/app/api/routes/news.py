"""
News API Routes
"""
from fastapi import APIRouter, HTTPException
from loguru import logger
from app.services.news_service import (
    get_economy_news, 
    get_general_news,
    DEMO_ECONOMY_NEWS,
    DEMO_GENERAL_NEWS
)

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/economy")
async def economy_news():
    """Ekonomi haberlerini getir"""
    try:
        news = await get_economy_news()
        # Eğer haber çekemediyse demo data döndür
        if not news["turkey"] and not news["world"]:
            logger.warning("No economy news fetched, returning demo data")
            return DEMO_ECONOMY_NEWS
        return news
    except Exception as e:
        logger.error(f"Error fetching economy news: {e}")
        return DEMO_ECONOMY_NEWS


@router.get("/general")
async def general_news():
    """Gündem haberlerini getir"""
    try:
        news = await get_general_news()
        # Eğer haber çekemediyse demo data döndür
        if not news["turkey"] and not news["world"]:
            logger.warning("No general news fetched, returning demo data")
            return DEMO_GENERAL_NEWS
        return news
    except Exception as e:
        logger.error(f"Error fetching general news: {e}")
        return DEMO_GENERAL_NEWS
