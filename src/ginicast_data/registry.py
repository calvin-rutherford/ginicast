import re
from functools import lru_cache
from typing import Any

import yaml

from ginicast_data.io.paths import METRICS_CONFIG_PATH, SOURCES_CONFIG_PATH


class Registry:
    """Loads and provides access to metric and source configurations."""

    def __init__(self):
        self.metrics: list[dict[str, Any]] = []
        self.sources: dict[str, Any] = {}
        self._load()

    def _load(self):
        with open(METRICS_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            self.metrics = data.get("metrics", [])

        with open(SOURCES_CONFIG_PATH, "r", encoding="utf-8") as f:
            s_data = yaml.safe_load(f)
            self.sources = s_data.get("sources", {})
        self.validate()

    def validate(self):
        if not isinstance(self.metrics, list) or not self.metrics:
            raise ValueError("Configuration must contain a nonempty metrics list")
        if not isinstance(self.sources, dict) or not self.sources:
            raise ValueError("Configuration must contain a nonempty sources mapping")
        seen = set()
        supported = {"fred", "bls", "census", "wiid", "oecd", "manual"}
        for metric in self.metrics:
            if not isinstance(metric, dict):
                raise ValueError("Metric entries must be mappings")
            metric_id = metric.get("metric_id", "")
            source = metric.get("source", "")
            if not isinstance(metric_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", metric_id):
                raise ValueError("Invalid metric_id")
            if metric_id in seen:
                raise ValueError("Duplicate metric_id")
            seen.add(metric_id)
            if source not in supported or not isinstance(self.sources.get(source), dict):
                raise ValueError("Metric references an unsupported or missing source")
            if not metric.get("expected_frequency") or not metric.get("units"):
                raise ValueError("Metric requires expected_frequency and units")
            if source in {"fred", "bls"} and metric.get("source_series_id") in {None, "", "TBD"}:
                raise ValueError("API metric requires a source_series_id")

    def get_all_metrics(self) -> list[dict[str, Any]]:
        return self.metrics

    def filter_metrics(self, *, source=None, category=None) -> list[dict[str, Any]]:
        """List configured targets without instantiating fetchers or touching data."""
        return [metric for metric in self.metrics
                if (source is None or metric["source"] == source)
                and (category is None or metric.get("category") == category)]

    def get_core_metrics(self) -> list[dict[str, Any]]:
        return [m for m in self.metrics if m.get("category") == "core"]

    def get_metric(self, metric_id: str) -> dict[str, Any] | None:
        for m in self.metrics:
            if m.get("metric_id") == metric_id:
                return m
        return None

    def get_source_config(self, source_name: str) -> dict[str, Any]:
        return self.sources.get(source_name, {})

@lru_cache(maxsize=1)
def get_registry() -> Registry:
    """Load lazily so CLI config errors can be reported without an import traceback."""
    return Registry()
