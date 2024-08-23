from fastapi import APIRouter

from schemas.mlops import RegisterModelInput
from services.mlops import assign_prod_alias


router = APIRouter()


@router.post("/model_registration")
async def register_production_model(data: RegisterModelInput):
    data = data.model_dump()
    assign_prod_alias(data["run_id"])
    
    return {"response": "Registered"}
