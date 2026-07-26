import re
import warnings
from itertools import permutations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from dagster import AssetExecutionContext, Failure, Output, RetryPolicy, asset
from multielo import Tracker
from scipy.stats import poisson
from statsmodels.tools.sm_exceptions import PerfectSeparationWarning

from betsim.pipeline.io import write_artefact
from betsim.pipeline.resources import MySQLResource
from betsim.shared.settings import SentinelConfig

warnings.filterwarnings("ignore", category=PerfectSeparationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)


def load_snapshots(
    mysql: MySQLResource
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fixtures = mysql.read("fixtures")
    plays = mysql.read("plays")
    xgs = mysql.query(
        "SELECT gid, xg_h2h_lose, xg_h2h_win, xg_net, xg_sup FROM jleague "
        f"WHERE season <> {SentinelConfig.SEASON}"
    )
    return fixtures, plays, xgs


def merge_snapshot(snap: pd.DataFrame, incr: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([snap, incr]) \
        .drop_duplicates(subset="gid", keep="last") \
        .sort_values(by="date", ignore_index=True)


def attach_inference_templates(
    fixtures: pd.DataFrame,
    plays: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    teams = set(fixtures["away"]) | set(fixtures["home"])
    tpl = pd.DataFrame({"teams": list(permutations(teams, 2))})
    tpl[["season", "date"]] = SentinelConfig.SEASON, SentinelConfig.DATE
    tpl[["home", "away"]] = tpl["teams"].tolist()
    fixtures = pd.concat([fixtures, tpl], ignore_index=True)

    tpl = plays[["team"]].drop_duplicates()
    tpl[["season", "date"]] = SentinelConfig.SEASON, SentinelConfig.DATE
    plays = pd.concat([plays, tpl], ignore_index=True)

    return fixtures, plays


def add_h2h_rates(df: pd.DataFrame) -> pd.DataFrame:
    df["teams"] = df[["home", "away"]].apply(tuple, axis=1)
    df["n_h2h_game"] = df.groupby("teams")["date"].cumcount() + 1

    for res, val in {"win": "H", "lose": "A"}.items():
        df[f"n_{res}"] = df.groupby("teams", as_index=False)["res"] \
            .apply(lambda x: (x == val).cumsum()) \
            .reset_index() \
            .sort_values(by="level_1", ignore_index=True)["res"]
        df[f"rate_h2h_{res}"] = df[f"n_{res}"] / df["n_h2h_game"]
    return df


def add_hcap_magnitude(df: pd.DataFrame) -> pd.DataFrame:
    df["hcap_mag"] = np.where(
        df["hcap_side"].eq("H"),
        -df["hcap_line"],
        df["hcap_line"],
    )
    return df


def load_xg_snapshot(df: pd.DataFrame, xgs: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(xgs, on="gid", how="left")
    df["is_snap"] = df["xg_net"].notna()
    df.fillna({
        "xg_h2h_lose": 0.3,
        "xg_h2h_win": 0.3,
        "xg_net": 0.0,
        "xg_sup": 0.5,
    }, inplace=True)
    return df


def add_expected_goal(
    fixtures: pd.DataFrame,
    plays: pd.DataFrame,
    max_goals: int = 6,
    half_life: int = 365,
) -> pd.DataFrame:
    dates = fixtures.query("~is_snap and season != season.min()")["date"]

    for date in dates.unique():
        df = plays.query("date < @date").copy()

        recency = (
            pd.Timestamp(df["date"].max()) + pd.Timedelta(days=6)
            if date == SentinelConfig.DATE
            else pd.Timestamp(date)
        ) - pd.to_datetime(df["date"])
        df["weight"] = np.exp(-np.log(2) * recency.dt.days / half_life)

        model = smf.glm(
            formula="goals ~ team + opponent + stadium",
            data=df,
            family=sm.families.Poisson(),
            freq_weights=df["weight"],
        ).fit()

        for idx, rw in fixtures.query("date == @date").iterrows():
            home, away = rw["home"], rw["away"]
            if df.query(
                "team in [@home, @away] and opponent in [@home, @away]"
            ).empty:
                continue

            xg_h = model.predict(
                pd.DataFrame([{"team": home, "opponent": away, "stadium": 1}])
            ).iloc[0]
            xg_a = model.predict(
                pd.DataFrame([{"team": away, "opponent": home, "stadium": 0}])
            ).iloc[0]

            xg = np.outer(*[
                [poisson.pmf(i, lambda_hat) for i in range(max_goals + 1)]
                for lambda_hat in [xg_h, xg_a]
            ])
            xg_h2h = np.unravel_index(xg.argmax(), xg.shape)

            fixtures.loc[idx, "xg_h2h_lose"] = np.triu(xg, k=1).sum()
            fixtures.loc[idx, "xg_h2h_win"] = np.tril(xg, k=-1).sum()
            fixtures.loc[idx, "xg_net"] = -np.diff(xg_h2h)[0]
            fixtures.loc[idx, "xg_sup"] = xg.max()
    return fixtures


def enrich_fixtures(
    fixtures: pd.DataFrame,
    plays: pd.DataFrame,
    xgs: pd.DataFrame,
) -> pd.DataFrame:
    return fixtures.pipe(add_h2h_rates) \
        .pipe(add_hcap_magnitude) \
        .pipe(load_xg_snapshot, xgs) \
        .pipe(add_expected_goal, plays)


def add_rest_days(df: pd.DataFrame) -> pd.DataFrame:
    df["dt"] = pd.to_datetime(df["date"])
    df["dt_next"] = df.groupby(["season", "team"])["dt"].shift(-1)

    df["n_rest_day"] = (df["dt_next"] - df["dt"]).dt.days
    df["n_rest_day"] = df["n_rest_day"].where(df["n_rest_day"].lt(14), 7) \
        .astype(int)
    return df


def add_wl_rates(df: pd.DataFrame) -> pd.DataFrame:
    df["n_game"] = df.groupby(["season", "team"])["date"].cumcount() + 1

    for res, val in {"win": 3, "lose": 0}.items():
        df[f"n_{res}"] = df.groupby(["season", "team"])["points"] \
            .apply(lambda x: (x == val).cumsum()) \
            .reset_index() \
            .sort_values(by="level_2", ignore_index=True)["points"]
        df[f"rate_seas_{res}"] = df[f"n_{res}"] / df["n_game"]
    return df


def add_scores(df: pd.DataFrame) -> pd.DataFrame:
    df["scores"] = df.groupby(["season", "team"])["points"].cumsum()
    return df


def build_rank_template(df: pd.DataFrame) -> pd.DataFrame:
    season_date = df[["season", "date"]].drop_duplicates().values
    teams = df[["team"]].drop_duplicates()

    return pd.concat([
        teams.assign(season=season, date=date)
        for season, date in season_date
    ], ignore_index=True)[["season", "date", "team"]]


def accumulate_goals(ranks: pd.DataFrame, plays: pd.DataFrame) -> pd.DataFrame:
    goals = ["goals", "net_goals"]
    scores = plays[["season", "date", "team", "scores"]].copy()
    scores[goals] = plays.groupby(["season", "team"])[goals].cumsum()

    return ranks.merge(scores, how="left")


def sort_ranks(df: pd.DataFrame) -> pd.DataFrame:
    criteria = ["scores", "net_goals", "goals"]
    df[criteria] = df.groupby(["season", "team"])[criteria].ffill() \
        .fillna(float("-inf"))
    df["criteria"] = df[criteria].apply(tuple, axis=1)
    df["rank"] = df.groupby(["season", "date"])["criteria"] \
        .rank(method="min", ascending=False) \
        .astype(int)
    return df


def add_rank(df: pd.DataFrame) -> pd.DataFrame:
    ranks = df.pipe(build_rank_template) \
        .pipe(accumulate_goals, plays=df) \
        .pipe(sort_ranks)
    return df.merge(ranks[["date", "rank", "team"]])


def build_results(df: pd.DataFrame) -> pd.DataFrame:
    results = df[["date", "season"]].copy()

    results["winner"] = np.select(
        [df["res"].eq("H"), df["res"].eq("A")],
        [df["home"], df["away"]],
        default=df[["home", "away"]].apply(tuple, axis=1),
    )
    results["loser"] = np.select(
        [df["res"].eq("A"), df["res"].eq("H")],
        [df["home"], df["away"]],
        default=None,
    )
    return results


def build_elo(df: pd.DataFrame, category: str) -> pd.DataFrame:
    tracker = Tracker()
    tracker.process_data(df[["date", "winner", "loser"]])

    return tracker.get_history_df().rename(
        columns={"player_id": "team", "rating": f"rating_{category}"},
    )


def add_elo_score(plays: pd.DataFrame, fixtures: pd.DataFrame) -> pd.DataFrame:
    results = build_results(
        fixtures.query(f"season != {SentinelConfig.SEASON}")
    )

    elo = pd.concat([
        build_elo(results.query("season == @season"), "seas")
        for season in results["season"].unique()
    ], ignore_index=True)
    plays = plays.merge(elo, how="left")

    elo = build_elo(results, "hist")
    plays = plays.merge(elo, how="left")

    return plays


def enrich_plays(fixtures: pd.DataFrame, plays: pd.DataFrame) -> pd.DataFrame:
    return plays.pipe(add_rest_days) \
        .pipe(add_scores) \
        .pipe(add_wl_rates) \
        .pipe(add_rank) \
        .pipe(add_elo_score, fixtures=fixtures)


def shift_fixture_features(df: pd.DataFrame) -> pd.DataFrame:
    col = ["rate_h2h_win", "rate_h2h_lose"]
    df[col] = df.groupby("teams")[col].shift()

    return df.fillna({
        "rate_h2h_lose": .3,
        "rate_h2h_win": .4,
    })


def shift_play_features(df: pd.DataFrame) -> pd.DataFrame:
    is_future = df["date"].eq(SentinelConfig.DATE)

    col = ["rank", "rate_seas_lose", "rate_seas_win"]
    df.loc[is_future, col] = [pd.NA] * len(col)

    col = [
        "scores", "rate_seas_win", "rate_seas_lose", "rank",
        "rating_seas", "rating_hist",
    ]
    df[col] = df.groupby("team")[col].ffill()
    df.loc[~is_future, col] = df.loc[~is_future]\
        .groupby(["season", "team"])[col] \
        .shift()

    return df.fillna({
        "rank": 0,
        "rate_seas_lose": .3,
        "rate_seas_win": .4,
        "rating_hist": 1_000,
        "rating_seas": 1_000,
        "scores": 0,
    })


def apply_feature_shift(
    fixtures: pd.DataFrame,
    plays: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    return shift_fixture_features(fixtures), shift_play_features(plays)


def formulate_h2h_fixtures(
    fixtures: pd.DataFrame,
    plays: pd.DataFrame,
) -> pd.DataFrame:
    matches = fixtures[[
        "away", "date", "gdt", "gid",
        "hcap_mag", "hcap_res", "home", "rate_h2h_lose",
        "rate_h2h_win", "season", "xg_h2h_lose", "xg_h2h_win",
        "xg_net", "xg_sup",
    ]].copy()

    teams = plays[[
        "date", "n_rest_day", "rank", "rate_seas_lose",
        "rate_seas_win", "rating_hist", "rating_seas", "scores",
        "team",
    ]].copy()

    return matches.merge(
        teams.rename(columns={"team": "home"}),
        how="left",
        on=["date", "home"],
    ).merge(
        teams.rename(columns={"team": "away"}),
        how="left",
        on=["date", "away"],
        suffixes=("_h", "_a"),
    )


def feature_net_difference(df: pd.DataFrame) -> pd.DataFrame:
    col_h = [col for col in df.columns if col.endswith("_h")]
    col_a = [col for col in df.columns if col.endswith("_a")]

    col = [re.sub("_h$", "_net", col) for col in col_h]
    df[col] = df[col_h].values - df[col_a].values
    return df


def preprocess_response(df: pd.DataFrame) -> pd.DataFrame:
    df["hcap_res"] = df["hcap_res"].map({"H": 1, "A": 0})

    return df[[
        "gid", "gdt", "season", "home",
        "away", "hcap_res", "hcap_mag", "n_rest_day_net",
        "rank_net", "rate_h2h_lose", "rate_h2h_win", "rate_seas_lose_net",
        "rate_seas_win_net", "rating_hist_net", "rating_seas_net",
        "scores_net", "xg_h2h_lose", "xg_h2h_win", "xg_net", "xg_sup",
    ]].sort_values(by="gid", ignore_index=True).round(6)


def populate_temporary_gid(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["gid"].isna()
    df.loc[mask, "gid"] = [f"next-{i}" for i in range(1, mask.sum() + 1)]

    df["gdt"].fillna(SentinelConfig.DATETIME, inplace=True)
    df["hcap_res"].fillna(-999, inplace=True)
    df["hcap_mag"].fillna(-999, inplace=True)
    return df


def build_jleague(fixtures: pd.DataFrame, plays: pd.DataFrame) -> pd.DataFrame:
    jl = fixtures.pipe(formulate_h2h_fixtures, plays=plays) \
        .pipe(feature_net_difference) \
        .pipe(preprocess_response) \
        .pipe(populate_temporary_gid)

    if len(jl) != len(fixtures):
        raise Failure(
            description=(
                "Expected the engineered J-League to contain one row per "
                f"fixture, but found {len(jl)} J-League rows for "
                f"{len(fixtures)} fixtures."
            ),
            allow_retries=False,
        )

    return jl.query("season > season.min()")


@asset(
    name="jleague",
    description=(
        "Engineers Elo, expected-goals, form, and head-to-head features "
        "(plus inference templates) for training and inference."
    ),
    group_name="FeatureEngineering",
    retry_policy=RetryPolicy(max_retries=3, delay=30),
)
def engineer_features(
    context: AssetExecutionContext,
    mysql: MySQLResource,
    fixtures: pd.DataFrame,
    plays: pd.DataFrame,
) -> Output[pd.DataFrame]:
    snap_fixtures, snap_plays, snap_xgs = load_snapshots(mysql)

    fixtures = merge_snapshot(snap_fixtures, fixtures)
    plays = merge_snapshot(snap_plays, plays)
    fixtures, plays = attach_inference_templates(fixtures, plays)

    fixtures = enrich_fixtures(fixtures, plays, snap_xgs)
    plays = enrich_plays(fixtures, plays)

    fixtures, plays = apply_feature_shift(fixtures, plays)
    jleague = build_jleague(fixtures, plays)

    write_artefact(jleague, "processed/jleague", context.run.run_id)

    context.log.info(f"Accumulated {len(jleague):,} jleague feature rows.")

    return Output(
        jleague,
        metadata={
            "rows": len(jleague),
            "seasons": sorted(jleague["season"].unique().tolist())[:-1],
        }
    )
