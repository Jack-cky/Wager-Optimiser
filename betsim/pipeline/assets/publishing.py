import pandas as pd
from dagster import AssetExecutionContext, RetryPolicy, TimeWindow, asset

from betsim.pipeline.partitions import partition_week
from betsim.pipeline.resources import MySQLResource
from betsim.shared.settings import SentinelConfig


def keep_incremental(df: pd.DataFrame, window: TimeWindow) -> pd.DataFrame:
    ts = pd.to_datetime(df["gdt"], format="%Y-%m-%d %H:%M") \
        .dt.tz_localize("Asia/Tokyo")

    return df[(
        ((ts >= window.start) & (ts < window.end))
        | (df["season"] == SentinelConfig.SEASON)
    )]


def upsert_tables(
    mysql: MySQLResource,
    tables: dict[str, pd.DataFrame],
) -> None:
    for name, df in tables.items():
        mysql.upsert(df, name)


@asset(
    name="tables",
    description=(
        "Upserts the incremental fixture, play, and J-League feature "
        "rows into MySQL database."
    ),
    partitions_def=partition_week,
    group_name="Publishing",
    retry_policy=RetryPolicy(max_retries=3, delay=30),
)
def sync_tables(
    context: AssetExecutionContext,
    mysql: MySQLResource,
    fixtures: pd.DataFrame,
    plays: pd.DataFrame,
    jleague: pd.DataFrame,
) -> None:
    window = context.partition_time_window
    jleague = keep_incremental(jleague, window)

    upsert_tables(
        mysql,
        {
            "fixtures": fixtures,
            "plays": plays,
            "jleague": jleague,
        }
    )

    context.log.info(
        f"Published {len(fixtures):,} fixtures, "
        f"{len(plays):,} plays, and "
        f"{len(jleague):,} jleague rows."
    )
