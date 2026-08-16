from collections.abc import Iterator

import numpy as np
import pandas as pd
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetOut,
    Failure,
    LastPartitionMapping,
    Output,
    multi_asset,
)

from betsim.pipeline.io import write_artefact
from betsim.shared.settings import ScheduleConfig, SeasonConfig


def parse_identifiers(df: pd.DataFrame) -> pd.DataFrame:
    df["gid"] = df["source"].str.split("-").str[-1]
    return df


def parse_datetime(df: pd.DataFrame) -> pd.DataFrame:
    jst = pd.to_datetime(df["date"], format="%d/%m/%Y %H:%M %Z", utc=True) \
        .dt.tz_convert(ScheduleConfig.TIMEZONE)

    new_era_autumn = (jst.dt.year >= SeasonConfig.SWITCH_YEAR) \
        & (jst.dt.month >= SeasonConfig.ROLLOVER_MONTH)
    df["season"] = jst.dt.year + new_era_autumn
    df["date"] = jst.dt.strftime("%Y-%m-%d")
    df["time"] = jst.dt.strftime("%H:%M")
    df["gdt"] = df["date"] + " " + df["time"]
    return df


def parse_goals(df: pd.DataFrame) -> pd.DataFrame:
    df[["hg", "ag"]] = df["full_goal"].str.split(" - ", expand=True) \
        .astype(int)
    df["res"] = np.select(
        [df["hg"].gt(df["ag"]), df["hg"].lt(df["ag"])],
        ["H", "A"],
        default="D",
    )
    df["goals_abs_diff"] = (df["hg"] - df["ag"]).abs()
    return df


def parse_handicap(df: pd.DataFrame) -> pd.DataFrame:
    df[["hcap_side", "hcap_line"]] = df["handicap"].str.split(expand=True)
    df["hcap_side"] = df["hcap_side"].str[0]
    df["hcap_line"] = pd.to_numeric(df["hcap_line"], errors="coerce").fillna(0)

    is_favourite = df["hcap_line"].gt(0)
    df.loc[is_favourite, "hcap_line"] *= -1
    df.loc[is_favourite, "hcap_side"] = df.loc[is_favourite, "hcap_side"] \
        .map({"H": "A", "A": "H"})
    return df


def formulate_results(df: pd.DataFrame) -> pd.DataFrame:
    df["hcap_hg"] = df["hg"] \
        + df["hcap_line"].where(df["hcap_side"].eq("H"), 0)
    df["hcap_ag"] = df["ag"] \
        + df["hcap_line"].where(df["hcap_side"].eq("A"), 0)

    df["hcap_res"] = np.select(
        [df["hcap_hg"].gt(df["hcap_ag"]), df["hcap_hg"].lt(df["hcap_ag"])],
        ["H", "A"],
        default="D",
    )

    is_draw = df["hcap_res"].eq("D")
    df.loc[is_draw, "hcap_res"] = df.loc[is_draw, "hcap_side"] \
        .map({"H": "A", "A": "H"})
    return df


def cleanse_match_results(df: pd.DataFrame) -> pd.DataFrame:
    return df.pipe(parse_identifiers) \
        .pipe(parse_datetime) \
        .pipe(parse_goals) \
        .pipe(parse_handicap) \
        .pipe(formulate_results)


def build_fixtures(df: pd.DataFrame) -> pd.DataFrame:
    return df[[
        "gid", "gdt", "season", "date",
        "home", "away", "hg", "ag",
        "res", "hcap_line", "hcap_res", "hcap_side",
    ]].sort_values(by="gdt", ignore_index=True)


def build_play(df: pd.DataFrame, team: str, stadium: int) -> pd.DataFrame:
    opponent = "away" if team == "home" else "home"
    df = df.rename(
        columns={team: "team", opponent: "opponent", f"{team[0]}g": "goals"},
    )

    df["gid"] = df["gid"] + "-" + str(stadium)
    df["net_goals"] = df["goals_abs_diff"].where(
        df["res"].eq(team[0].upper()),
        -df["goals_abs_diff"],
    )
    df["points"] = df["res"].str.lower() \
        .map({team[0]: 3, "d": 1}) \
        .fillna(0) \
        .astype(int)
    df["stadium"] = stadium
    return df


def build_plays(df: pd.DataFrame) -> pd.DataFrame:
    plays = pd.concat([
        df.pipe(build_play, team=team, stadium=stadium)
        for stadium, team in enumerate(["away", "home"])
    ])

    return plays[[
        "gid", "season", "date", "team",
        "opponent", "goals", "net_goals", "points",
        "stadium",
    ]].sort_values(by="date", ignore_index=True)


def normalise_matches(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    fixtures = build_fixtures(df)
    plays = build_plays(df)

    if len(fixtures) != len(plays) // 2:
        raise Failure(
            description=(
                "Expected two play records per fixture after normalisation, "
                f"but found {len(fixtures)} fixtures and {len(plays)} plays."
            ),
            allow_retries=False,
        )

    return fixtures, plays


@multi_asset(
    ins={
        "match_results": AssetIn(partition_mapping=LastPartitionMapping()),
    },
    outs={
        "fixtures": AssetOut(
            description=(
                "Parses scraped match HTML into one fixture row per match."
            ),
        ),
        "plays": AssetOut(
            description=(
                "Parses scraped match HTML into two team-level play rows "
                "per match."
            ),
        ),
    },
    group_name="Cleansing",
)
def normalised_matches(
    context: AssetExecutionContext,
    match_results: pd.DataFrame,
) -> Iterator[Output[pd.DataFrame]]:
    match_results = cleanse_match_results(match_results)
    fixtures, plays = normalise_matches(match_results)

    write_artefact(fixtures, "interim/fixtures", context.run.run_id)
    write_artefact(plays, "interim/plays", context.run.run_id)

    context.log.info(
        f"Decomposed {len(fixtures):,} fixtures and {len(plays):,} plays."
    )

    yield Output(
        fixtures,
        output_name="fixtures",
        metadata={
            "rows": len(fixtures),
        },
    )
    yield Output(
        plays,
        output_name="plays",
        metadata={
            "rows": len(plays),
        },
    )
