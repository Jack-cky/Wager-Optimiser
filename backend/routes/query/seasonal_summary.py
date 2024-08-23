from fastapi import APIRouter

from services.query import get_seasonal_summary


router = APIRouter()


@router.get("/seasonal_summary")
async def load_seasonal_summary(home: str, away: str):
    smy = get_seasonal_summary(home, away)
    
    return {"response": smy}
