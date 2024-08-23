from pydantic import BaseModel


class ProbabilityMatrixInput(BaseModel):
    home: str="Home Team Encoding"
    away: str="Away Team Encoding"
    max_goals: int=6
