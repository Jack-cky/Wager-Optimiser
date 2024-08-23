import numpy as np

from utils import get_featured_plays, get_team_mapping


def get_seasonal_summary(home: str, away: str) -> dict:
    encoder = get_team_mapping("encoder")
    decoder = get_team_mapping("decoder")
    
    df = get_featured_plays(["team", "rank", "scores", "rate_seas_win"])
    
    smy = df.query(f"team == '{encoder[home]}' or team == '{encoder[away]}'") \
        .groupby("team", as_index=False) \
        .last()
    
    smy["idx"] = np.where(smy["team"] == encoder[home], 0, 1)
    smy["team"] = smy["team"].map(decoder)
    smy["rate_seas_win"] *= 100
    
    smy = smy.sort_values(by="idx") \
        .drop(columns="idx") \
        .rename(columns={
            "team": "Team", "rank": "Rank",
            "scores": "Scores", "rate_seas_win": "Win Rate (%)",
        }) \
        .set_index("Team") \
        .to_dict()
    
    return smy
