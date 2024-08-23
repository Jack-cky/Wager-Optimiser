from pydantic import BaseModel


class TrainModelInput(BaseModel):
    expt: str="Experiment Name"
    season: int=2013
    is_latest: bool=False
