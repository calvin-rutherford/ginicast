import json

import pytest

from ginicast_data.selection import SelectionError, failed_metrics_from_manifest


@pytest.mark.parametrize("data", [
    [],
    {"manifest_version": 2},
    {"manifest_version": True},
    {"manifest_version": 1, "run_id": "invalid", "metrics": []},
    {"manifest_version": 1, "run_id": "a" * 32, "metrics": "invalid"},
    {"manifest_version": 1, "run_id": "a" * 32, "metrics": [None]},
    {"manifest_version": 1, "run_id": "a" * 32,
     "metrics": [{"metric_id": "demo_index", "status": "unknown"}]},
    {"manifest_version": 1, "run_id": "a" * 32,
     "metrics": [{"metric_id": "not_configured", "status": "failed"}]},
    {"manifest_version": 1, "run_id": "a" * 32,
     "metrics": [{"metric_id": "../escape", "status": "failed"}]},
    {"manifest_version": 1, "run_id": "a" * 32,
     "metrics": [{"metric_id": "demo_index", "status": "failed"}] * 2},
])
def test_invalid_manifest(workspace, data):
    root, registry = workspace
    path = root / "run.json"
    path.write_text(json.dumps(data))
    with pytest.raises(SelectionError):
        failed_metrics_from_manifest(path, registry)


@pytest.mark.parametrize("contents", [None, "not json", "{}"])
def test_unreadable_or_malformed_manifest(workspace, contents):
    root, registry = workspace
    path = root / "run.json"
    if contents is not None:
        path.write_text(contents)
    with pytest.raises(SelectionError):
        failed_metrics_from_manifest(path, registry)


def test_retry_ignores_paths_config_and_skipped_entries(workspace):
    root, registry = workspace
    path = root / "run.json"
    path.write_text(json.dumps({"manifest_version": 1, "run_id": "a" * 32, "metrics": [
        {"metric_id": "demo_index", "status": "failed", "source": "untrusted-source",
         "outputs": {"standardized": "/must/not/be/accessed"}},
        {"metric_id": "demo_ratio", "status": "skipped"},
    ]}))
    assert failed_metrics_from_manifest(path, registry) == (["demo_index"], "a" * 32)


def test_filter_metrics_combines_source_and_category(workspace):
    _, registry = workspace
    registry.metrics[0]["category"] = "core"
    registry.metrics[1]["category"] = "candidate"
    assert registry.filter_metrics(source="manual", category="core") == [registry.metrics[0]]
    assert registry.filter_metrics(source="fred", category="core") == []
