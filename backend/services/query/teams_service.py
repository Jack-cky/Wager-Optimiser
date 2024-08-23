from utils.helper import get_season_team


def get_teams(season: int) -> list:
    df = get_season_team(["season", "team"])
    
    teams = df.query(f"season == {season}")["team"] \
        .tolist()
    
    return teams
