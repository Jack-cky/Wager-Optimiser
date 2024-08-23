from fastapi import APIRouter

from services.mlops import evaluate_handicap_models


router = APIRouter()


@router.get("/model_evaluation")
async def evaluate_models(versions: str):
    evaluation = evaluate_handicap_models(versions)
    
    return {"response": evaluation}
