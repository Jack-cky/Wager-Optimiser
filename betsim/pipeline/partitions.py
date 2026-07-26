from dagster import TimeWindowPartitionsDefinition

from betsim.shared.settings import ScheduleConfig


partition_week = TimeWindowPartitionsDefinition(
    cron_schedule=ScheduleConfig.CRON_SCHEDULE,
    start=ScheduleConfig.START_FROM,
    timezone=ScheduleConfig.TIMEZONE,
    fmt=ScheduleConfig.FORMAT_YMD,
)
