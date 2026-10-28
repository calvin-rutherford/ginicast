import hashlib
import logging
from typing import Any, Tuple

import pandas as pd

from ginicast_data.fetch.base import BaseFetcher
from ginicast_data.io.readers import find_manual_raw_file, read_manual_csv
from ginicast_data.utils.time import current_timestamp_iso

logger = logging.getLogger(__name__)

class CensusFetcher(BaseFetcher):
    """
    Fetches Census metrics.
    Due to the complexity and variability of Census API endpoints (ACS, CPS, etc.),
    this fetcher relies on manual file drops for Phase 1.
    Users should download the relevant table (e.g. from data.census.gov) as CSV
    and place it in `data/raw_manual/census/<metric_id>.csv`.
    """

    def __init__(self, source_config: dict[str, Any]):
        super().__init__(source_config)

    def fetch(self, metric_config: dict[str, Any]) -> Tuple[pd.DataFrame, dict[str, Any]]:
        metric_id = metric_config.get("metric_id")
        manual_file = find_manual_raw_file("census", metric_id)

        if not manual_file:
            logger.warning(
                f"No manual CSV found for Census metric '{metric_id}'. "
                f"Please download it and place it in 'data/raw_manual/census/{metric_id}.csv'.\n"
                f"Returning empty dataframe."
            )
            df = pd.DataFrame(columns=["date", "value"])
        else:
            logger.info(f"Process manual Census file: {manual_file}")
            df = read_manual_csv(manual_file)

            # We expect the user to have provided a basic CSV with at least 'date' and 'value'
            # Or we try to coerce. For this MVP, we enforce 'date' and 'value' columns.
            if "date" not in df.columns or "value" not in df.columns:
                raise ValueError(f"Manual file for {metric_id} must have 'date' and 'value' columns.")

            df = df[["date", "value"]]

        metadata = {
            "metric_id": metric_id,
            "display_name": metric_config.get("display_name"),
            "source": "census",
            "source_series_id": metric_config.get("source_series_id"),
            "units": metric_config.get("units"),
            "expected_frequency": metric_config.get("expected_frequency"),
            "retrieval_timestamp": current_timestamp_iso(),
            "input_file": str(manual_file) if manual_file else None,
            "input_sha256": hashlib.sha256(manual_file.read_bytes()).hexdigest() if manual_file else None,
            "provenance_status": "unverified_manual_input",
            "raw_rows_count": len(df),
            "observation_start": df["date"].min() if not df.empty else None,
            "observation_end": df["date"].max() if not df.empty else None,
            "notes": metric_config.get("notes", "") + " (Manual ingest)"
        }

        return df, metadata
