import os
from pathlib import Path

from .downloader_service import loads_data
from .cleanser_service import cleanse_raw_data
from .engineer_service import engineer_features


PTH_CLEANSED = Path(os.getenv("PTH_CLEANSED"))
PTH_FEATURED = Path(os.getenv("PTH_FEATURED"))
PTH_MAPPING = Path(os.getenv("PTH_MAPPING"))
PTH_PREDICT = Path(os.getenv("PTH_PREDICT"))
PTH_RAW = Path(os.getenv("PTH_RAW"))


def create_data_dir() -> None:
    PTH_CLEANSED.mkdir(parents=True, exist_ok=True)
    PTH_FEATURED.mkdir(parents=True, exist_ok=True)
    PTH_MAPPING.mkdir(parents=True, exist_ok=True)
    PTH_PREDICT.mkdir(parents=True, exist_ok=True)
    PTH_RAW.mkdir(parents=True, exist_ok=True)


def data_pipeline(is_complled: bool=False) -> None:
    predict_file = PTH_PREDICT / "j1_predict.parquet"
    
    if not predict_file.exists() or is_complled:
        create_data_dir()
        loads_data()
        cleanse_raw_data()
        engineer_features()
