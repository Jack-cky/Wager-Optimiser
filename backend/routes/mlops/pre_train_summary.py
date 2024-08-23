from fastapi import APIRouter

from services.mlops import get_pre_train_summary


router = APIRouter()


@router.get("/pre_train_summary")
async def load_pre_train_summary(expt: str, season: str):
    season = int(season)
    smy = get_pre_train_summary(expt, season)
    
    return {"response": smy}
