import csv
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


def read_csv_strict(path: Path, required_columns: list[str]) -> pd.DataFrame:
    """Reject ambiguous headers/row widths instead of letting pandas infer an index."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, None)
        if (not header or any(not column for column in header)
                or len(set(header)) != len(header)
                or not set(required_columns).issubset(header)):
            raise ValueError("CSV requires unique named columns and all required fields")
        rows = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError("CSV row width does not match header")
            rows.append([value if value != "" else None for value in row])
    return pd.DataFrame(rows, columns=header)


def read_manual_csv(path: Path) -> pd.DataFrame:
    return read_csv_strict(path, ["date", "value"])[["date", "value"]]
