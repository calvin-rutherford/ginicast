from unittest.mock import Mock

import pandas as pd
import pytest

from ginicast_data.fetch.bls import BLSFetcher
from ginicast_data.fetch.fred import FREDFetcher
from ginicast_data.standardize.schema import enforce_schema


def test_fred_missing_marker_is_preserved_but_bad_tokens_fail(monkeypatch):
    from ginicast_data.fetch import fred
    monkeypatch.setenv("FRED_API_KEY", "test-only")
    response = Mock()
    response.json.return_value = {"observations": [
        {"date": "2020-01-01", "value": "."},
        {"date": "2020-02-01", "value": "2"},
    ]}
    monkeypatch.setattr(fred, "safe_get", lambda *args, **kwargs: response)
    fetcher = FREDFetcher({})
    frame, _ = fetcher.fetch({"metric_id": "example", "source_series_id": "example"})
    assert pd.isna(frame["value"].iloc[0])
    normalized = enforce_schema(frame, "example", "fred", "monthly", "Index")
    assert normalized["value"].isna().sum() == 1
    response.json.return_value["observations"][1]["value"] = "bad-token"
    frame, _ = fetcher.fetch({"metric_id": "example", "source_series_id": "example"})
    with pytest.raises(ValueError):
        enforce_schema(frame, "example", "fred", "monthly", "Index")


def test_fred_without_key_fails_before_http(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    with pytest.raises(ValueError, match="required"):
        FREDFetcher({}).fetch({"source_series_id": "example"})


@pytest.mark.parametrize("key,span", [(None, 10), ("test-only", 20)])
def test_bls_window_and_annual_average_handling(monkeypatch, key, span):
    from ginicast_data.fetch import bls
    if key:
        monkeypatch.setenv("BLS_API_KEY", key)
    else:
        monkeypatch.delenv("BLS_API_KEY", raising=False)
    response = Mock()
    response.json.return_value = {"status": "REQUEST_SUCCEEDED", "Results": {"series": [{"data": [
        {"year": "2020", "period": "M01", "value": "2"},
        {"year": "2020", "period": "M13", "value": "3"},
    ]}]}}
    post = Mock(return_value=response)
    monkeypatch.setattr(bls, "safe_post", post)
    frame, _ = BLSFetcher({}).fetch({"source_series_id": "example", "metric_id": "example"})
    payload = post.call_args.kwargs["json"]
    assert int(payload["endyear"]) - int(payload["startyear"]) + 1 == span
    assert len(frame) == 1
    assert frame["date"].tolist() == ["2020-01-01"]


def test_bls_invalid_period_fails(monkeypatch):
    from ginicast_data.fetch import bls
    response = Mock()
    response.json.return_value = {"status": "REQUEST_SUCCEEDED", "Results": {"series": [{"data": [
        {"year": "2020", "period": "M99", "value": "2"},
    ]}]}}
    monkeypatch.setattr(bls, "safe_post", lambda *args, **kwargs: response)
    with pytest.raises(ValueError, match="period"):
        BLSFetcher({}).fetch({"source_series_id": "example", "metric_id": "example"})
