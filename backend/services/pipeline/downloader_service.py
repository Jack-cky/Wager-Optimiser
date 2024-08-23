import os
from pathlib import Path

import pandas as pd


PTH_RAW = Path(os.getenv("PTH_RAW"))

URL = "https://www.football-data.co.uk/new/JPN.csv"


def loads_data() -> None:
    df = pd.read_csv(URL)
    df.to_parquet(PTH_RAW / "raw_data.parquet")
