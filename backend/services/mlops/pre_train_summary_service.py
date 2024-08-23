import os

from utils import get_featured_goals, get_featured_j1_league


EXPT_GP = os.getenv("EXPT_GP")
EXPT_HC = os.getenv("EXPT_HC")


def get_pre_train_summary(expt: str, season: int) -> tuple[int, int]:
    if expt == EXPT_GP:
        df = get_featured_goals(["season"])
        
        train_size = len(df.query(f"season <= {season}"))
        dev_size = 0
    
    elif expt == EXPT_HC:
        df = get_featured_j1_league(["season"])
        
        train_size = len(df.query(f"season <= {season-1}"))
        dev_size = len(df.query(f"season == {season}"))
    
    return train_size, dev_size
