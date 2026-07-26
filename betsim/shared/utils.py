from datetime import datetime


def get_current_season(date: datetime | None = None) -> str:
    yr = (date or datetime.now()).year
    return f"{yr - 1}-{yr}"
