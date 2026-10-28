from typing import Any

from ginicast_data.fetch.base import BaseFetcher
from ginicast_data.fetch.bls import BLSFetcher
from ginicast_data.fetch.census import CensusFetcher
from ginicast_data.fetch.fred import FREDFetcher
from ginicast_data.fetch.manual import ManualFetcher
from ginicast_data.fetch.oecd import OECDFetcher
from ginicast_data.fetch.wiid import WIIDFetcher


def get_fetcher(source_name: str, source_config: dict[str, Any]) -> BaseFetcher:
    """Factory to get the right fetcher class for a given source."""
    if source_name == "fred":
        return FREDFetcher(source_config)
    elif source_name == "bls":
        return BLSFetcher(source_config)
    elif source_name == "census":
        return CensusFetcher(source_config)
    elif source_name == "oecd":
        return OECDFetcher(source_config)
    elif source_name == "wiid":
        return WIIDFetcher(source_config)
    elif source_name == "manual":
        return ManualFetcher(source_config)
    else:
        raise ValueError(f"Unknown source: {source_name}")
