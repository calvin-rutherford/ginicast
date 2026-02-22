import os
import pandas as pd
import logging
from typing import Tuple, Any
from datetime import datetime

from ginicast_data.fetch.base import BaseFetcher
from ginicast_data.utils.http import create_session, safe_post
from ginicast_data.utils.time import current_timestamp_iso
from ginicast_data.standardize.normalize_dates import normalize_date_column

logger = logging.getLogger(__name__)

class BLSFetcher(BaseFetcher):
    """Fetches series from the BLS API V2."""
    
    def __init__(self, source_config: dict[str, Any]):
        super().__init__(source_config)
        self.api_key = os.environ.get("BLS_API_KEY") # Optional, but higher limits
        self.base_url = self.source_config.get("base_url", "https://api.bls.gov/publicAPI/v2/timeseries/data/")
        self.session = create_session()
        
    def fetch(self, metric_config: dict[str, Any]) -> Tuple[pd.DataFrame, dict[str, Any]]:
        series_id = metric_config.get("source_series_id")
        if not series_id or series_id == "TBD":
            raise ValueError(f"No valid series_id provided for BLS metric: {metric_config.get('metric_id')}")
            
        current_year = datetime.now().year
        start_year = max(1959, current_year - 20) # BLS max span is usually 20 years per request
        
        # We'll just fetch the most recent 20 years for Phase 1 MVP to stay simple,
        # or we could loop. Let's start with a single 20-year trailing window.
        payload = {
            "seriesid": [series_id],
            "startyear": str(start_year),
            "endyear": str(current_year)
        }
        if self.api_key:
            payload["registrationkey"] = self.api_key
            
        headers = {'Content-type': 'application/json'}
        response = safe_post(self.session, self.base_url, json=payload, headers=headers)
        data = response.json()
        
        if data.get("status") != "REQUEST_SUCCEEDED":
            errs = data.get("message", [])
            raise RuntimeError(f"BLS API error for {series_id}: {errs}")
            
        series_data = data["Results"]["series"][0]["data"]
        
        if not series_data:
            df = pd.DataFrame(columns=["date", "value"])
        else:
            # BLS returns year and period (e.g. M01, Q01).
            parsed_data = []
            for item in series_data:
                year = item["year"]
                period = item["period"] # e.g. M01, M02... M12, or Q01
                value = item["value"]
                
                # Simple month parser: M01 -> 01. If it's Annual (A01), Q1 (Q01), map to months.
                month = "01"
                if period.startswith("M") and period != "M13": # M13 is annual avg sometimes
                    month = period[1:]
                elif period == "Q01": month = "01"
                elif period == "Q02": month = "04"
                elif period == "Q03": month = "07"
                elif period == "Q04": month = "10"
                elif period.startswith("A"): month = "01"
                
                date_str = f"{year}-{month}-01"
                parsed_data.append({"date": date_str, "value": value})
                
            df = pd.DataFrame(parsed_data)[["date", "value"]]
            df = df.sort_values("date").reset_index(drop=True)
            
        metadata = {
            "metric_id": metric_config.get("metric_id"),
            "display_name": metric_config.get("display_name"),
            "source": "bls",
            "source_series_id": series_id,
            "units": metric_config.get("units"),
            "expected_frequency": metric_config.get("expected_frequency"),
            "retrieval_timestamp": current_timestamp_iso(),
            "raw_rows_count": len(df),
            "observation_start": df["date"].min() if not df.empty else None,
            "observation_end": df["date"].max() if not df.empty else None,
            "notes": metric_config.get("notes", "") + f" (fetched {start_year}-{current_year})"
        }
        
        return df, metadata
