import re

from utils import get_cleansed_plays, get_team_mapping


MARKS = {3: "🟢", 1: "🟡", 0: "🔴"}


def get_recent_games(team: str, n_games: int=5) -> str:
    encoder = get_team_mapping("encoder")
    
    df = get_cleansed_plays(["team", "points"])
    
    results = df.query(f"team == '{encoder[team]}'")["points"] \
        .tail(n_games) \
        .map(MARKS) \
        .to_list()[::-1]
    
    results = re.sub(r"[\[\],']", "", str(results))
    
    return results
