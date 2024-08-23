from fastapi import APIRouter

from schemas.mlops import TrainModelInput
from services.mlops import submit_train_job


router = APIRouter()


@router.post("/model_training")
async def train_model(data: TrainModelInput):
    data = data.model_dump()
    submit_train_job(**data)
    
    return {"response": "Trained"}
