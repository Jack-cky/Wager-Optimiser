import os

from .mlops_service import (
    assign_prod_alias, assign_tags, create_experiment,
    is_best_run,
)
from .training_job_service import train_handicap_model, train_goals_probability_model


EXPT_BD = os.getenv("EXPT_BD")
EXPT_GP = os.getenv("EXPT_GP")
EXPT_HC = os.getenv("EXPT_HC")


def goals_probability_model(season: int, is_latest: bool) -> None:
    create_experiment(EXPT_GP)
    
    run_id = train_goals_probability_model(season)
    
    assign_tags(run_id, season, EXPT_GP, is_latest)
    
    assign_prod_alias(run_id)


def handicap_model(season: int, is_latest: bool) -> None:
    create_experiment(EXPT_HC)
    create_experiment(EXPT_BD)
    
    run_id_hc, run_id_bd = train_handicap_model(season)
    
    assign_tags(run_id_hc, season, EXPT_HC, is_latest)
    assign_tags(run_id_bd, season, EXPT_BD, is_latest)
    
    if is_best_run(EXPT_HC, run_id_hc, "logloss"):
        assign_prod_alias(run_id_hc)
        assign_prod_alias(run_id_bd)


def submit_train_job(expt: str, season: int, is_latest: bool) -> None:
    if expt == EXPT_GP:
        goals_probability_model(season, is_latest)
    
    elif expt == EXPT_HC:
        handicap_model(season, is_latest)
