from datetime import datetime
from pathlib import Path

import pandas as pd

from betsim.shared.paths import DATA_DIR


def load_cache(season: str, name: str) -> str | None:
    pth = DATA_DIR / f"cache/{season}/{name}.html"
    return pth.read_text(encoding="utf-8") if pth.exists() else None


def write_cache(html: str, season: str, name: str) -> None:
    pth = DATA_DIR / f"cache/{season}/{name}.html"
    pth.parent.mkdir(parents=True, exist_ok=True)
    pth.write_text(html, encoding="utf-8")


def atomic_write(df: pd.DataFrame, pth_out: Path) -> None:
    pth_out.parent.mkdir(parents=True, exist_ok=True)
    pth_tmp = pth_out.with_suffix(f"{pth_out.suffix}.tmp")
    df.to_parquet(pth_tmp, index=False)
    pth_tmp.replace(pth_out)


def write_artefact(df: pd.DataFrame, name: str, run_id: str) -> None:
    pth = DATA_DIR / f"{name}_{datetime.now():%Y%m%d}_{run_id}.parquet"
    atomic_write(df, pth)
