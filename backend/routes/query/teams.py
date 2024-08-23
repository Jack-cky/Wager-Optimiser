from fastapi import APIRouter

from services.query import get_teams


router = APIRouter()


@router.get("/teams")
async def load_teams(season: int):
    teams = get_teams(season)
    
    return {"response": teams}
