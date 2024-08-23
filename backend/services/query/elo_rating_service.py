import pandas as pd

from utils import get_featured_plays, get_team_mapping


def query_seas_elo(team: str, df: pd.DataFrame, mt: dict) -> pd.DataFrame:
    elo = df.query(f"team == '{mt[team]}'")[["rating_seas"]] \
        .rename(columns={"rating_seas": team}) \
        .reset_index(drop=True)
    
    return elo


def get_elo_rating(season: int, home: str, away: str) -> dict:
    encoder = get_team_mapping("encoder")
    
    df = get_featured_plays(["season", "team", "rating_seas"])
    
    plays = df.query(f"season == {season}")
    
    elo_h, elo_a = pd.DataFrame(), pd.DataFrame()
    
    if home != "None":
        elo_h = query_seas_elo(home, plays, encoder)
    
    if away != "None":
        elo_a = query_seas_elo(away, plays, encoder)
    
    elo = pd.concat([elo_h, elo_a], axis=1) \
        .ffill() \
        .fillna(-1) \
        .to_dict()
    
    return elo
