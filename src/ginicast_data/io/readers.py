from pathlib import Path

import pandas as pd

from ginicast_data.io.paths import RAW_MANUAL_DIR, STANDARDIZED_DIR


def read_standardized_csv(metric_id: str) -> pd.DataFrame:
    """Reads a standardized CSV for a given metric."""
    file_path = STANDARDIZED_DIR / f"{metric_id}.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Standardized file for {metric_id} not found at {file_path}")
    return pd.read_csv(file_path)

def list_standardized_files() -> list[Path]:
    """Returns a list of all files in the standardized directory."""
    return list(STANDARDIZED_DIR.glob("*.csv"))

def find_manual_raw_file(source: str, metric_id: str) -> Path | None:
    """Finds a manual raw file for a given source and metric if it exists."""
    path = RAW_MANUAL_DIR / source / f"{metric_id}.csv"
    return path if path.is_file() else None
