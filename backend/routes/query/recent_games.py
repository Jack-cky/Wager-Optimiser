from fastapi import APIRouter

from services.query import get_recent_games


router = APIRouter()


@router.get("/recent_games")
async def load_recent_games(team: str, n_games: int=5):
    results = get_recent_games(team, n_games)
    
    return {"response": results}
