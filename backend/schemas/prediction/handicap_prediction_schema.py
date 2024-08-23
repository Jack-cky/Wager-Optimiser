from pydantic import BaseModel


class HandicapPredictionInput(BaseModel):
    home: str="Home Team Encoding"
    away: str="Away Team Encoding"
    time_frame: str="Event Time"
    odds_home: float=1.
    odds_draw: float=1.
    odds_away: float=1.
