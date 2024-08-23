from pydantic import BaseModel


class RegisterModelInput(BaseModel):
    run_id: str="Experiment run id"