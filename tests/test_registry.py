import pytest

from ginicast_data.registry import Registry


def test_registry_loads_metrics():
    registry = Registry()
    metrics = registry.get_all_metrics()
    assert len(metrics) > 0, "No metrics loaded."

    # Check that core metrics exist
    core_metrics = registry.get_core_metrics()
    assert len(core_metrics) > 0, "No core metrics flagged."

    # Check that required fields are present in a sample metric
    sample = core_metrics[0]
    assert "metric_id" in sample
    assert "source" in sample
    assert "source_series_id" in sample

def test_registry_loads_sources():
    registry = Registry()
    fred_config = registry.get_source_config("fred")
    assert fred_config, "FRED config not loaded."
    assert "base_url" in fred_config


@pytest.mark.parametrize("edit", [
    lambda metrics: metrics.append(dict(metrics[0])),
    lambda metrics: metrics[0].update(metric_id="../escape"),
    lambda metrics: metrics[0].update(source="unsupported"),
    lambda metrics: metrics[0].pop("units"),
])
def test_invalid_registry_configuration(workspace, edit):
    _, registry = workspace
    edit(registry.metrics)
    with pytest.raises(ValueError):
        registry.validate()
