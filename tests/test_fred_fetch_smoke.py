import os
import pytest
from ginicast_data.fetch.fred import FREDFetcher
from ginicast_data.registry import Registry

@pytest.mark.skipif(not os.environ.get("FRED_API_KEY"), reason="FRED_API_KEY not set")
def test_fred_fetch_smoke():
    registry = Registry()
    source_config = registry.get_source_config("fred")
    
    # We use CPIAUCSL (CPI Total) for smoke test
    metric_config = registry.get_metric("cpi_total")
    assert metric_config is not None
    
    fetcher = FREDFetcher(source_config)
    df, metadata = fetcher.fetch(metric_config)
    
    assert not df.empty
    assert "date" in df.columns
    assert "value" in df.columns
    assert metadata["metric_id"] == "cpi_total"
