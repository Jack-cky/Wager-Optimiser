from dagster import (
    AssetSelection,
    build_schedule_from_partitioned_job,
    define_asset_job,
)

from .partitions import partition_week


data_asset_selection = AssetSelection.groups(
    "Ingestion",
    "Cleansing",
    "FeatureEngineering",
    "Publishing",
)

ml_asset_selection = AssetSelection.groups(
    "Monitoring",
    "Training",
    "Deployment",
)

weekly_asset_selection = AssetSelection.groups(
    "Ingestion",
    "Cleansing",
    "FeatureEngineering",
    "Publishing",
    "Monitoring",
    "Training",
    "Deployment",
)


betsim_data_job = define_asset_job(
    name="betsim_data_pipeline",
    selection=data_asset_selection,
    partitions_def=partition_week,
)

betsim_ml_job = define_asset_job(
    name="betsim_ml_pipeline",
    selection=ml_asset_selection,
)

betsim_weekly_job = define_asset_job(
    name="betsim_weekly_pipeline",
    selection=weekly_asset_selection,
    partitions_def=partition_week,
)


betsim_weekly_schedule = build_schedule_from_partitioned_job(betsim_weekly_job)
