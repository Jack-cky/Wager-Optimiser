from fastapi import APIRouter

from services.pipeline import data_pipeline


router = APIRouter()


@router.post("/pipeline")
async def execute_data_pipeline():
    data_pipeline(True)
    
    return {"response": "Updated"}
