import json
import os
from pathlib import Path

import pandas as pd
import pyfiglet


PTH_CLEANSED = Path(os.getenv("PTH_CLEANSED"))
PTH_FEATURED = Path(os.getenv("PTH_FEATURED"))
PTH_MAPPING = Path(os.getenv("PTH_MAPPING"))
PTH_PREDICT = Path(os.getenv("PTH_PREDICT"))


def console_message(txt: str) -> None:
    if os.getenv("CONSOLE_PRINT", '1') == '1':
        os.environ["CONSOLE_PRINT"] = '0'
        
        console_msg = pyfiglet.figlet_format(txt, font="small")
        
        print(console_msg)


def get_team_mapping(src: str) -> dict:
    with open(PTH_MAPPING / f"{src}.json") as file:
        mt = json.load(file)
    
    return mt


def get_season_team(col: list) -> pd.DataFrame:
    df = pd.read_parquet(PTH_MAPPING / "teams.parquet")[col]
    
    return df


def get_cleansed_plays(col: list) -> pd.DataFrame:
    df = pd.read_parquet(PTH_CLEANSED / "plays.parquet")[col]
    
    return df


def get_featured_plays(col: list) -> pd.DataFrame:
    df = pd.read_parquet(PTH_FEATURED / "plays.parquet")[col]
    
    return df


def get_featured_j1_league(col: list | None=None) -> pd.DataFrame:
    df = pd.read_parquet(PTH_FEATURED / "j1_league.parquet")
    
    if col:
        df = df[col]
    
    return df


def get_featured_goals(col: list) -> pd.DataFrame:
    df = pd.read_parquet(PTH_FEATURED / "goals.parquet")[col]
    
    return df


def get_predicting_features(col: list) -> pd.DataFrame:
    df = pd.read_parquet(PTH_PREDICT / "j1_predict.parquet")[col]
    
    return df
