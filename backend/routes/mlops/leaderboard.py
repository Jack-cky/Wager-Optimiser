from fastapi import APIRouter

from services.mlops import get_leadboard


router = APIRouter()


@router.get("/leaderboard")
async def load_leaderboard(expt: str, metric: str):
    lb = get_leadboard(expt, metric)
    
    return {"response": lb}
