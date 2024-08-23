import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


PTH_INDX = Path(os.getenv("PTH_INDEX"))


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index():
    with open(PTH_INDX / "index.html", "r") as file:
        content = file.read()
    
    return content
