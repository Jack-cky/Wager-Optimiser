from fastapi import APIRouter, HTTPException
from mlflow.exceptions import MlflowException

from schemas.prediction import HandicapPredictionInput
from services.prediction import get_handicap_results


router = APIRouter()


@router.post("/handicap_results")
async def predict_handicap_results(data: HandicapPredictionInput):
    try:
        data = data.model_dump()
        y_hat = get_handicap_results(**data)
    except MlflowException:
        raise HTTPException(status_code=404, detail="Missing model.")
    
    return {"response": y_hat}
