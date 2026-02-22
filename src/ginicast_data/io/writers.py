import json
from pathlib import Path
import pandas as pd

from ginicast_data.io.paths import RAW_DIR, STANDARDIZED_DIR, METADATA_DIR

def write_raw_csv(df: pd.DataFrame, source: str, metric_id: str) -> Path:
    """Writes the raw dataframe to a CSV file."""
    source_dir = RAW_DIR / source
    source_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = source_dir / f"{metric_id}.csv"
    df.to_csv(file_path, index=False)
    return file_path

def write_standardized_csv(df: pd.DataFrame, metric_id: str) -> Path:
    """Writes standardized dataframe to a CSV file."""
    file_path = STANDARDIZED_DIR / f"{metric_id}.csv"
    df.to_csv(file_path, index=False)
    return file_path

def write_metadata_json(metadata: dict, source: str, metric_id: str) -> Path:
    """Writes metadata dictionary to a JSON file."""
    source_dir = METADATA_DIR / source
    source_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = source_dir / f"{metric_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)
    return file_path
