from patsy import PatsyError

from fastapi import APIRouter, HTTPException
from mlflow.exceptions import MlflowException

from schemas.prediction import ProbabilityMatrixInput
from services.prediction import get_probability_matrix


router = APIRouter()


@router.post("/probability_matrix")
async def predict_probability_matrix(data: ProbabilityMatrixInput):
    try:
        data = data.model_dump()
        prob_matrix = get_probability_matrix(**data)
    except MlflowException:
        raise HTTPException(status_code=404, detail="Missing model.")
    except PatsyError:
        raise HTTPException(status_code=422, detail="Untrained record.")
    
    return {"response": prob_matrix}
