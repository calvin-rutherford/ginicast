import shutil
from pathlib import Path

import pytest
import requests


@pytest.fixture(autouse=True)
def block_offline_network(request, monkeypatch):
    if request.node.get_closest_marker("live"):
        return

    def blocked(*args, **kwargs):
        raise AssertionError("Network forbidden in offline tests")

    monkeypatch.setattr(requests.sessions.Session, "request", blocked)


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    from ginicast_data import pipeline, registry
    from ginicast_data.io import readers, writers

    fixture = Path(__file__).resolve().parents[1] / "examples" / "offline"
    shutil.copytree(fixture / "config", tmp_path / "config")
    shutil.copytree(fixture / "data", tmp_path / "data")
    monkeypatch.setattr(registry, "METRICS_CONFIG_PATH", tmp_path / "config/metrics.yaml")
    monkeypatch.setattr(registry, "SOURCES_CONFIG_PATH", tmp_path / "config/sources.yaml")
    monkeypatch.setattr(readers, "RAW_MANUAL_DIR", tmp_path / "data/raw_manual")
    monkeypatch.setattr(writers, "RAW_DIR", tmp_path / "data/raw")
    monkeypatch.setattr(writers, "STANDARDIZED_DIR", tmp_path / "data/standardized")
    monkeypatch.setattr(writers, "METADATA_DIR", tmp_path / "data/metadata")
    monkeypatch.setattr(pipeline, "RUNS_DIR", tmp_path / "data/runs")
    return tmp_path, registry.Registry()
