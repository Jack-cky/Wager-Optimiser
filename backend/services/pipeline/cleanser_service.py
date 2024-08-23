import json
import os
from pathlib import Path

import pandas as pd
from pytz import timezone


PTH_CLEANSED = Path(os.getenv("PTH_CLEANSED"))
PTH_MAPPING = Path(os.getenv("PTH_MAPPING"))
PTH_RAW = Path(os.getenv("PTH_RAW"))

DT_FORMAT = "%d/%m/%Y %H:%M"
JP_TZ = timezone("Asia/Tokyo")
UK_TZ = timezone("Europe/London")


def preprocess_data() -> pd.DataFrame:
    def convert_column_case(df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [col.lower() for col in df.columns]
        
        return df
    
    def convert_bst_to_jst(df: pd.DataFrame) -> pd.DataFrame:
        df["date_time"] = df["date"] + " " + df["time"]
        
        df["jst"] = pd.to_datetime(df["date_time"], format=DT_FORMAT) \
            .map(UK_TZ.localize) \
            .map(lambda x: x.astimezone(JP_TZ))
        
        df["date"] = df["jst"].dt.strftime("%Y-%m-%d")
        df["time"] = df["jst"].dt.strftime("%H:%M")
        
        return df
    
    def encode_team_name(df: pd.DataFrame) -> pd.DataFrame:
        teams = pd.unique(df[["home", "away"]].values.ravel("K"))
        teams.sort()
        
        encoder = {team:str(idx) for idx, team in enumerate(teams)}
        encoder.update({"None": "-1"})
        
        decoder = {idx:team for team, idx in encoder.items()}
        
        df["home"] = df["home"].map(encoder)
        df["away"] = df["away"].map(encoder)
        
        with open(PTH_MAPPING / "encoder.json", "w") as file:
            json.dump(encoder, file)
        
        with open(PTH_MAPPING / "decoder.json", "w") as file:
            json.dump(decoder, file)
        
        return df
    
    def calculate_goal_difference(df: pd.DataFrame) -> pd.DataFrame:
        df["goal_diff"] = df["hg"] - df["ag"]
        df["goal_abs_diff"] = df["goal_diff"].abs()
        
        return df
    
    def filter_column(df: pd.DataFrame) -> pd.DataFrame:
        col = [
            "season", "date", "time",
            "home", "away",
            "hg", "ag", "res",
            "avgch", "avgcd", "avgca",
            "goal_diff", "goal_abs_diff",
        ]
        
        df = df[col].copy()
        
        return df
    
    df = pd.read_parquet(PTH_RAW / "raw_data.parquet") \
        .pipe(convert_column_case) \
        .pipe(convert_bst_to_jst) \
        .pipe(encode_team_name) \
        .pipe(calculate_goal_difference) \
        .pipe(filter_column)
    
    df.to_parquet(PTH_CLEANSED / "cleansed_data.parquet")
    
    return df


def get_fixture_information(df: pd.DataFrame) -> None:
    col = [
        "season", "date", "time",
        "home", "away", "res",
        "avgch", "avgcd", "avgca",
    ]
    
    fixtures = df[col].copy()
    
    fixtures.to_parquet(PTH_CLEANSED / "fixtures.parquet")


def get_individual_team_results(df: pd.DataFrame) -> None:
    dfs = []
    for stadium, team in enumerate(["away", "home"]):
        play = df.rename(columns={team: "team", f"{team[0]}g": "goals"})
        
        multp = (play["res"].str.lower() == team[0]) \
            .map({True: 1, False: -1})
        play["net_goals"] = play["goal_abs_diff"] * multp
        
        play["points"] = play["res"].str.lower() \
            .map({team[0]: 3, "d": 1}) \
            .fillna(0) \
            .astype(int)
        
        play["stadium"] = stadium
        
        dfs.append(play)
    
    col = [
        "season", "date", "team", "stadium",
        "goals", "net_goals", "points",
    ]
    
    plays = pd.concat(dfs)[col] \
        .sort_values(by="date", ignore_index=True)
    
    plays.to_parquet(PTH_CLEANSED / "plays.parquet")
    
    with open(PTH_MAPPING / "decoder.json") as f:
        decoder = json.load(f)
    
    seas_teams = plays[["season", "team"]].drop_duplicates()
    seas_teams["team_encode"] = seas_teams["team"]
    seas_teams["team"] = seas_teams["team"].map(decoder)
    seas_teams.sort_values(by=["season", "team"], ignore_index=True, inplace=True)
    
    seas_teams.to_parquet(PTH_MAPPING / "teams.parquet")


def cleanse_raw_data() -> None:
    df = preprocess_data()
    get_fixture_information(df)
    get_individual_team_results(df)
