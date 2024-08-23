from fastapi import APIRouter

from .default import index
from .mlops import evaluation, leaderboard, pre_train_summary, registration, training
from .pipeline import pipeline
from .prediction import handicap_prediction, probability_matrix
from .query import elo_rating, recent_games, seasonal_summary, teams


router_default = APIRouter(tags=["Default Index"])
router_default.include_router(index.router)


router_mlops = APIRouter(prefix="/api/v1", tags=["MLOps"])
router_mlops.include_router(leaderboard.router)
router_mlops.include_router(pre_train_summary.router)
router_mlops.include_router(evaluation.router)
router_mlops.include_router(training.router)
router_mlops.include_router(registration.router)


router_pipeline = APIRouter(prefix="/api/v1", tags=["Data Pipeline"])
router_pipeline.include_router(pipeline.router)


router_predict = APIRouter(prefix="/api/v1", tags=["Prediction"])
router_predict.include_router(handicap_prediction.router)
router_predict.include_router(probability_matrix.router)


router_query = APIRouter(prefix="/api/v1", tags=["Data Query"])
router_query.include_router(elo_rating.router)
router_query.include_router(recent_games.router)
router_query.include_router(seasonal_summary.router)
router_query.include_router(teams.router)
