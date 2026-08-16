from datetime import datetime

from betsim.shared.settings import SeasonConfig


def get_current_season(date: datetime | None = None) -> str:
    d = date or datetime.now()
    if (d.year, d.month) >= (SeasonConfig.SWITCH_YEAR, SeasonConfig.ROLLOVER_MONTH):
        start = d.year if d.month >= SeasonConfig.ROLLOVER_MONTH else d.year - 1
        return f"{start}-{start + 1}"
    return f"{d.year - 1}-{d.year}"
