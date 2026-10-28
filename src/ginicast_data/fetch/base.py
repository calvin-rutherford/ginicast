from abc import ABC, abstractmethod
from typing import Any, Tuple

import pandas as pd


class BaseFetcher(ABC):
    """Abstract base class for all data source fetchers."""

    def __init__(self, source_config: dict[str, Any]):
        self.source_config = source_config

    @abstractmethod
    def fetch(self, metric_config: dict[str, Any]) -> Tuple[pd.DataFrame, dict[str, Any]]:
        """
        Fetches the raw data for a given metric.

        Args:
            metric_config: The dictionary configuring this metric from metrics.yaml

        Returns:
            Tuple of (DataFrame, Metadata Dict)
            DataFrame must at least contain 'date' and 'value' columns.
        """
        pass
