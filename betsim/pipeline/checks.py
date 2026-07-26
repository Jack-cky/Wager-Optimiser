import pandas as pd
from dagster import AssetCheckResult, MetadataValue, asset_check

from betsim.shared.settings import SentinelConfig


@asset_check(asset="jleague", blocking=True)
def nonempty(jleague: pd.DataFrame) -> AssetCheckResult:
    n = len(jleague)
    return AssetCheckResult(
        passed=n > 0,
        metadata={"rows": n},
    )


@asset_check(asset="jleague", blocking=True)
def unique_gid(jleague: pd.DataFrame) -> AssetCheckResult:
    dupes = int(jleague["gid"].duplicated().sum())
    return AssetCheckResult(
        passed=dupes == 0,
        metadata={"duplicate_gids": dupes},
    )


@asset_check(asset="jleague", blocking=True)
def target_present(jleague: pd.DataFrame) -> AssetCheckResult:
    real = jleague[jleague["season"] != SentinelConfig.SEASON]
    missing = int(real["hcap_res"].isna().sum())
    return AssetCheckResult(
        passed=missing == 0,
        metadata={"rows_missing_target": missing},
    )


@asset_check(asset="jleague", blocking=True)
def rate_bounds(jleague: pd.DataFrame) -> AssetCheckResult:
    out_of_range = {}
    for col, lo, hi in (
        [(c, 0, 1) for c in ["rate_h2h_lose", "rate_h2h_win"]]
        + [(c, -1, 1) for c in ["rate_seas_lose_net", "rate_seas_win_net"]]
    ):
        s = jleague[col].dropna()
        bad = int(((s < lo) | (s > hi)).sum())
        if bad:
            out_of_range[col] = bad
    return AssetCheckResult(
        passed=not out_of_range,
        metadata={"out_of_range": MetadataValue.json(out_of_range)},
    )


@asset_check(asset="jleague", blocking=True)
def inference_templates_present(
    jleague: pd.DataFrame,
) -> AssetCheckResult:
    n = int((jleague["season"] == SentinelConfig.SEASON).sum())
    return AssetCheckResult(
        passed=n > 0,
        metadata={"template_rows": n},
    )
