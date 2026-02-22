import os
import pandas as pd
import logging
from typing import Tuple, Any

from ginicast_data.fetch.base import BaseFetcher
from ginicast_data.utils.http import create_session, safe_get
from ginicast_data.utils.time import current_timestamp_iso

logger = logging.getLogger(__name__)

class FREDFetcher(BaseFetcher):
    """Fetches series from the FRED API."""
    
    def __init__(self, source_config: dict[str, Any]):
        super().__init__(source_config)
        self.api_key = os.getenv("FRED_API_KEY")
        if not self.api_key:
            logger.warning("FRED_API_KEY not found in environment. FRED fetching will fail.")
        self.base_url = self.source_config.get("base_url", "https://api.stlouisfed.org/fred")
        self.session = create_session()
        
    def fetch(self, metric_config: dict[str, Any]) -> Tuple[pd.DataFrame, dict[str, Any]]:
        series_id = metric_config.get("source_series_id")
        if not series_id or series_id == "TBD":
            raise ValueError(f"No valid series_id provided for FRED metric: {metric_config.get('metric_id')}")
            
        url = f"{self.base_url}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "observation_start": "1958-01-01",  # get a bit of history before the targeted 1959
            "sort_order": "asc"
        }
        
        response = safe_get(self.session, url, params=params)
        data = response.json()
        
        observations = data.get("observations", [])
        if not observations:
            logger.warning(f"No observations returned for {series_id}")
            df = pd.DataFrame(columns=["date", "value"])
        else:
            df = pd.DataFrame(observations)[["date", "value"]]
            # FRED sometimes returns '.' for missing values
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            
        metadata = {
            "metric_id": metric_config.get("metric_id"),
            "display_name": metric_config.get("display_name"),
            "source": "fred",
            "source_series_id": series_id,
            "units": metric_config.get("units"),
            "expected_frequency": metric_config.get("expected_frequency"),
            "retrieval_timestamp": current_timestamp_iso(),
            "raw_rows_count": len(df),
            "observation_start": df["date"].min() if not df.empty else None,
            "observation_end": df["date"].max() if not df.empty else None,
            "notes": metric_config.get("notes", "")
        }
        
        return df, metadata
