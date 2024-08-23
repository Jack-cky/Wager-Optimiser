from dotenv import load_dotenv
load_dotenv("config/.env")

from contextlib import asynccontextmanager
from fastapi import FastAPI

from routes.api import (
    router_default, router_mlops, router_pipeline,
    router_predict, router_query,
)
from services.mlops import start_client_server
from services.pipeline import data_pipeline
from utils import console_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    # code to execute when app is loading
    data_pipeline()
    start_client_server()
    yield
    # code to execute when app is shutting down


console_message("Wager Optimisation Backend Server")

app = FastAPI(title="Wager Optimisation — API Document", lifespan=lifespan)

app.include_router(router_pipeline)
app.include_router(router_query)
app.include_router(router_predict)
app.include_router(router_mlops)
app.include_router(router_default)
