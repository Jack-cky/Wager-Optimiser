import os
import re
from itertools import permutations
from pathlib import Path

import numpy as np
import pandas as pd

from multielo import Tracker


PTH_CLEANSED = Path(os.getenv("PTH_CLEANSED"))
PTH_FEATURED = Path(os.getenv("PTH_FEATURED"))
PTH_PREDICT = Path(os.getenv("PTH_PREDICT"))

FTS_SHIFT, FTS_NSHIFT = {}, []


def engineer_goals() -> None:
    col = ["season", "home", "away", "hg", "ag"]
    df = pd.read_parquet(PTH_CLEANSED / "cleansed_data.parquet")[col]
    
    opponent = {"away": "home", "home": "away"}
    dfs = []
    for stadium, team in enumerate(["away", "home"]):
        goal = df[["season", team, opponent[team], f"{team[0]}g"]] \
            .rename(
                columns={
                    team: "team", opponent[team]: "opponent",
                    f"{team[0]}g": "goals",
                }
            ).assign(stadium=stadium)
        
        dfs.append(goal)
    
    goals = pd.concat(dfs, ignore_index=True)
    
    goals.to_parquet(PTH_FEATURED / "goals.parquet")


def engineer_fixtures() -> pd.DataFrame:
    def normalise_odds(df: pd.DataFrame) -> pd.DataFrame:
        mkts = ["rate_mkt_h", "rate_mkt_d", "rate_mkt_a"]
        odds = ["avgch", "avgcd", "avgca"]
        
        df[mkts] = 1 / df[odds]
        df[mkts] = df[mkts].div(df[mkts].sum(axis=1), axis=0)
        
        FTS_NSHIFT.extend(["rate_mkt_h", "rate_mkt_a"])
        
        return df
    
    def apply_market_intelligence(df: pd.DataFrame) -> pd.DataFrame:
        df["knwl_mkt_intel"] = np.select(
            [df["rate_mkt_h"] >= .4, df["rate_mkt_a"] >= .3],
            ["H", "A"],
            default="D",
        )
        
        FTS_NSHIFT.append("knwl_mkt_intel")
        
        return df
    
    def categorise_time_frame(df: pd.DataFrame) -> pd.DataFrame:
        df["timestamp"] = pd.to_datetime(df["time"], format="%H:%M")
        
        df["time_frame"] = np.where(
            df["timestamp"].dt.hour < 18,
            "noon", "night",
        )
        
        FTS_NSHIFT.append("time_frame")
        
        return df
    
    def formulate_h2h_rate(df: pd.DataFrame) -> pd.DataFrame:
        df["teams"] = df[["home", "away"]].apply(tuple, axis=1)
        
        df["n_h2h_game"] = df.groupby("teams")["date"].cumcount() + 1
        
        for res, val in {"win": "H", "lose": "A"}.items():
            df[f"n_{res}"] = df.groupby("teams", as_index=False)["res"] \
                .apply(lambda x: (x==val).cumsum()) \
                .reset_index() \
                .sort_values(by="level_1", ignore_index=True)["res"]
            
            df[f"rate_h2h_{res}"] = df[f"n_{res}"] / df["n_h2h_game"]
        
        FTS_SHIFT.update({"rate_h2h_win": .4, "rate_h2h_lose": .3})
        
        return df
    
    def apply_h2h_rate_difference(df: pd.DataFrame) -> pd.DataFrame:
        df["rate_h2h_diff"] = df["rate_h2h_win"] - df["rate_h2h_lose"]
        
        df["knwl_h2h"] = np.select(
            [df["rate_h2h_diff"] > .3, df["rate_h2h_diff"] < -.2],
            ["H", "A"],
            default="D",
        )
        
        FTS_SHIFT.update({"knwl_h2h": "H"})
        
        return df
    
    def filter_column(df: pd.DataFrame) -> pd.DataFrame:
        col = [
            "season", "date", "time", "time_frame",
            "home", "away", "res",
            "avgch", "avgcd", "avgca", "knwl_mkt_intel",
            "rate_mkt_h", "rate_mkt_d", "rate_mkt_a",
            "teams", "rate_h2h_win", "rate_h2h_lose", "knwl_h2h",
        ]
        
        df = df[col].copy()
        
        return df
    
    df = pd.read_parquet(PTH_CLEANSED / "fixtures.parquet") \
        .pipe(normalise_odds) \
        .pipe(apply_market_intelligence) \
        .pipe(categorise_time_frame) \
        .pipe(formulate_h2h_rate) \
        .pipe(apply_h2h_rate_difference) \
        .pipe(filter_column) \
    
    df.to_parquet(PTH_FEATURED / "fixtures.parquet")
    
    return df


def engineer_plays(fixtures: pd.DataFrame) -> pd.DataFrame:
    def formulate_seasonal_rest(df: pd.DataFrame) -> pd.DataFrame:
        df["dt"] = pd.to_datetime(df["date"])
        df["dt_next"] = df.groupby(["season", "team"])["dt"].shift(-1)
        
        df["n_rest_day"] = df["dt_next"] - df["dt"]
        df["n_rest_day"] = df["n_rest_day"].dt.days
        df["n_rest_day"] = df["n_rest_day"].where(df["n_rest_day"] < 14, 7) \
            .astype(int)
        
        FTS_NSHIFT.append("n_rest_day")
        
        return df
    
    def formulate_seasonal_rate(df: pd.DataFrame) -> pd.DataFrame:
        df["n_game"] = df.groupby(["season", "team"])["date"].cumcount() + 1
        
        for res, val in {"win": 3, "lose": 0}.items():
            df[f"n_{res}"] = df.groupby(["season", "team"])["points"] \
                .apply(lambda x: (x==val).cumsum()) \
                .reset_index() \
                .sort_values(by="level_2", ignore_index=True)["points"]
            
            df[f"rate_seas_{res}"] = df[f"n_{res}"] / df["n_game"]
        
        FTS_SHIFT.update({"rate_seas_win": .4, "rate_seas_lose": .3})
        
        return df
    
    def formulate_seasonal_scores(df: pd.DataFrame) -> pd.DataFrame:
        df["scores"] = df.groupby(["season", "team"])["points"].cumsum()
        
        FTS_SHIFT.update({"scores": 0})
        
        return df
    
    def formulate_seasonal_rank(df: pd.DataFrame) -> pd.DataFrame:
        def create_rank_template(df: pd.DataFrame) -> pd.DataFrame:
            season_date = df[["season", "date"]].drop_duplicates().values
            teams = df[["team"]].drop_duplicates()
            
            tpls = []
            for season, date in season_date:
                tpl = teams.copy()
                tpl[["season", "date"]] = season, date
                tpls.append(tpl)
            
            col = ["season", "date", "team"]
            ranks_tpl = pd.concat(tpls, ignore_index=True)[col]
            
            return ranks_tpl
        
        def accumulate_goals(df: pd.DataFrame) -> pd.DataFrame:
            goals = ["goals", "net_goals"]
            
            scores = df[["season", "date", "team", "scores"]].copy()
            scores[goals] = df.groupby(["season", "team"]) \
                [goals].cumsum()
            
            return scores
        
        def sort_ranks(df: pd.DataFrame) -> pd.DataFrame:
            criteria = ["scores", "net_goals", "goals"]
            
            df[criteria] = df.groupby(["season", "team"])[criteria].ffill() \
                .fillna(float("-inf"))
            
            df["criteria"] = df[criteria].apply(tuple, axis=1)
            
            df["rank"] = df.groupby(["season", "date"])["criteria"] \
                .rank(method="min", ascending=False) \
                .astype(int)
            
            df = df[["date", "team", "rank"]].copy()
            
            return df
        
        tpl = create_rank_template(df)
        scores = accumulate_goals(df)
        
        ranks = tpl.merge(scores, how="left")
        ranks = sort_ranks(ranks)
        
        df = df.merge(ranks)
        
        FTS_SHIFT.update({"rank": 0})
        
        return df
    
    def formulate_seasonal_rating(df: pd.DataFrame) -> pd.DataFrame:
        results = fixtures[["season", "date"]].copy()
        
        results["winner"] = np.select(
            [fixtures["res"] == "H", fixtures["res"] == "A"],
            [fixtures["home"], fixtures["away"]],
            default=fixtures[["home", "away"]].apply(tuple, axis=1),
        )
        
        results["loser"] = np.select(
            [fixtures["res"] == "A", fixtures["res"] == "H"],
            [fixtures["home"], fixtures["away"]],
            default=None,
        )
        
        elos = []
        col = ["date", "winner", "loser"]
        for season in results["season"].unique():
            tracker = Tracker()
            tracker.process_data(results.query(f"season == {season}")[col])
            
            elo_season = tracker.get_history_df() \
                .rename(columns={"player_id": "team", "rating": "rating_seas"})
            
            elos.append(elo_season)
        
        elo = pd.concat(elos, ignore_index=True)
        
        df = df.merge(elo)
        
        FTS_SHIFT.update({"rating_seas": 1_000})
        
        return df
    
    def formulate_historical_rating(df: pd.DataFrame) -> pd.DataFrame:
        results = fixtures[["season", "date"]].copy()
        
        results["winner"] = np.select(
            [fixtures["res"] == "H", fixtures["res"] == "A"],
            [fixtures["home"], fixtures["away"]],
            default=fixtures[["home", "away"]].apply(tuple, axis=1),
        )
        
        results["loser"] = np.select(
            [fixtures["res"] == "A", fixtures["res"] == "H"],
            [fixtures["home"], fixtures["away"]],
            default=None,
        )
        
        tracker = Tracker()
        tracker.process_data(results[["date", "winner", "loser"]])
        
        elo = tracker.get_history_df() \
            .rename(columns={"player_id": "team", "rating": "rating_hist"})
        
        df = df.merge(elo)
        
        FTS_SHIFT.update({"rating_hist": 1_000})
        
        return df
    
    def filter_column(df: pd.DataFrame) -> pd.DataFrame:
        col = [
            "season", "date", "team",
            "goals", "net_goals", "points",
            "n_game", "rank", "scores",
            "rate_seas_win", "rate_seas_lose",
            "rating_seas", "rating_hist",
            "stadium", "n_rest_day",
        ]
        
        df = df[col].copy()
        
        return df
    
    df = pd.read_parquet(PTH_CLEANSED / "plays.parquet") \
        .pipe(formulate_seasonal_rest) \
        .pipe(formulate_seasonal_rate) \
        .pipe(formulate_seasonal_scores) \
        .pipe(formulate_seasonal_rank) \
        .pipe(formulate_seasonal_rating) \
        .pipe(formulate_historical_rating) \
        .pipe(filter_column)
    
    df.to_parquet(PTH_FEATURED / "plays.parquet")
    
    return df


def shift_features(
    fixtures: pd.DataFrame, plays: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    def shift_fixtures(df: pd.DataFrame) -> pd.DataFrame:
        teams = set()
        for team in ["away", "home"]:
            teams.update(df[team].to_list())
        
        df_nxt = pd.DataFrame({"teams": list(permutations(teams, 2))})
        df_nxt[["season", "date"]] = df["season"].max(), "-1"
        df_nxt[["home", "away"]] = df_nxt["teams"].tolist()
        
        df = pd.concat([df, df_nxt], ignore_index=True)
        
        col = [col for col in df.columns if col in FTS_SHIFT.keys()]
        df[col] = df.groupby("teams")[col].shift()
        
        df.fillna(FTS_SHIFT, inplace=True)
        
        return df
    
    def shift_plays(df: pd.DataFrame) -> pd.DataFrame:
        df_nxt = df.query("season == season.max()")[["season", "team"]] \
            .drop_duplicates()
        df_nxt["date"] = "-1"
        
        df = pd.concat([df, df_nxt], ignore_index=True)
        
        col = [col for col in df.columns if col in FTS_SHIFT.keys()]
        df[col] = df.groupby(["season", "team"])[col].shift()
        
        df.fillna(FTS_SHIFT, inplace=True)
        
        return df
    
    fixtures = shift_fixtures(fixtures)
    plays = shift_plays(plays)
    
    return fixtures, plays


def denormalise_data(fixtures: pd.DataFrame, plays: pd.DataFrame) -> None:
    def combine_dfs(
        fixtures: pd.DataFrame, plays: pd.DataFrame
    ) -> pd.DataFrame:
        fts = FTS_NSHIFT + list(FTS_SHIFT.keys())
        
        col = ["season", "date", "res", "home", "away"] \
            + [col for col in fixtures.columns if col in fts]
        games = fixtures[col].copy()
        
        col = ["date", "team"] \
            + [col for col in plays.columns if col in fts]
        teams = plays[col].copy()
        
        df = games.merge(
            teams.rename(columns={"team": "home"}),
            how="left",
            on=["date", "home"],
        ).merge(
            teams.rename(columns={"team": "away"}),
            how="left",
            on=["date", "away"],
            suffixes=("_h", "_a"),
        )
        
        return df
    
    def calculate_feature_difference(df: pd.DataFrame) -> pd.DataFrame:
        col_h = [col for col in df.columns if col.endswith("_h")]
        col_a = [col for col in df.columns if col.endswith("_a")]
        
        col = [re.sub("_h$", "_net", col) for col in col_h]
        df[col] = df[col_h].values - df[col_a].values
        
        df.drop(columns=col_h+col_a, inplace=True)
        
        return df
    
    def convert_hda_to_hcap_results(df: pd.DataFrame) -> pd.DataFrame:
        hcap = np.where(df["rank_net"] > 0, "A", "H")
        df["res"] = df["res"].where(df["res"] != "D", hcap)
        
        return df
    
    j1 = combine_dfs(fixtures, plays) \
        .pipe(calculate_feature_difference) \
        .pipe(convert_hda_to_hcap_results)
    
    j1_full = j1.query("res == res") \
        .sort_values(by="date", ignore_index=True) \
        .drop(columns=["date", "home", "away"])
    
    j1_full.to_parquet(PTH_FEATURED / "j1_league.parquet")
    
    init_diff = {
        "rate_h2h_win": .1,
        "rate_h2h_lose": -.1,
        "knwl_h2h": "H",
        "rank_net": 0,
        "scores_net": 0,
        "rate_seas_win_net": .1,
        "rate_seas_lose_net": -.1,
        "rating_seas_net": 0,
        "rating_hist_net": 0,
    }
    
    j1_predict = j1.query("res != res") \
        .fillna(init_diff) \
        .drop(columns="date") \
        .reset_index(drop=True)
    
    j1_predict.to_parquet(PTH_PREDICT / "j1_predict.parquet")


def engineer_features() -> None:
    engineer_goals()
    fixtures = engineer_fixtures()
    plays = engineer_plays(fixtures)
    fixtures, plays = shift_features(fixtures, plays)
    denormalise_data(fixtures, plays)
