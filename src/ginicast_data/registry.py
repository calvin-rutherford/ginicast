import yaml
from typing import Any
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
            
    def get_all_metrics(self) -> list[dict[str, Any]]:
        return self.metrics
        
    def get_core_metrics(self) -> list[dict[str, Any]]:
        return [m for m in self.metrics if m.get("category") == "core"]
        
    def get_metric(self, metric_id: str) -> dict[str, Any] | None:
        for m in self.metrics:
            if m.get("metric_id") == metric_id:
                return m
        return None
        
    def get_source_config(self, source_name: str) -> dict[str, Any]:
        return self.sources.get(source_name, {})

# Singleton instance
registry = Registry()
