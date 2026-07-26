import pandas as pd

from sqlalchemy import text
from sqlalchemy.engine import Engine

from betsim.shared.database import get_mysql_engine
from betsim.shared.settings import DatabaseConfig, SentinelConfig


ENGINE = get_mysql_engine(
    user=DatabaseConfig.USER,
    password=DatabaseConfig.PASSWORD,
    host=DatabaseConfig.HOST,
    port=DatabaseConfig.PORT,
    database=DatabaseConfig.DATABASE
)

with ENGINE.connect() as conn:
    TEAMS = pd.read_sql(
        text(
            "SELECT DISTINCT team FROM plays "
            "WHERE season = (SELECT MAX(season) FROM plays) ORDER BY team;"
        ),
        con=conn,
    )["team"].to_list()


def team_options(exclude: str | None) -> list[str]:
    return [team for team in TEAMS if team != exclude]


def recent_results(team: str, n: int = 5, engine: Engine = ENGINE) -> str:
    with engine.connect() as conn:
        return " ".join(
            pd.read_sql(
                text(
                    "SELECT points FROM plays "
                    "WHERE team = :team ORDER BY date DESC LIMIT :n;"
                ),
                con=conn,
                params={"team": team, "n": n},
            )["points"].map({3: "🟢", 1: "🟡", 0: "🔴"}).to_list()
        )


def fetch_features(
    home: str,
    away: str,
    engine: Engine = ENGINE,
) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(
            text(
                "SELECT * FROM jleague "
                "WHERE season = :season "
                "AND home = :home AND away = :away;"
            ),
            con=conn,
            params={
                "season": SentinelConfig.SEASON,
                "home": home,
                "away": away,
            },
        )
