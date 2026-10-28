"""Replace individual output files atomically on the destination filesystem."""
import json
import os
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd

from ginicast_data.io.paths import METADATA_DIR, RAW_DIR, STANDARDIZED_DIR


@contextmanager
def atomic_text(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=path.parent,
                                prefix=f".{path.name}.", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def write_json(data: dict, path: Path) -> Path:
    with atomic_text(path) as stream:
        json.dump(data, stream, indent=2, default=str, allow_nan=False)
        stream.write("\n")
    return path


def write_csv(df: pd.DataFrame, path: Path) -> Path:
    with atomic_text(path) as stream:
        df.to_csv(stream, index=False)
    return path


def write_raw_csv(df: pd.DataFrame, source: str, metric_id: str) -> Path:
    return write_csv(df, RAW_DIR / source / f"{metric_id}.csv")


def write_standardized_csv(df: pd.DataFrame, metric_id: str) -> Path:
    return write_csv(df, STANDARDIZED_DIR / f"{metric_id}.csv")


def write_metadata_json(metadata: dict, source: str, metric_id: str) -> Path:
    return write_json(metadata, METADATA_DIR / source / f"{metric_id}.json")
