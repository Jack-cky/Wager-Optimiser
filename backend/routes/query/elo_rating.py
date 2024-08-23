from fastapi import APIRouter

from services.query import get_elo_rating


router = APIRouter()


@router.get("/elo_rating")
async def load_elo_rating(season: int, home: str, away: str):
    elo = get_elo_rating(season, home, away)
    
    return {"response": elo}
