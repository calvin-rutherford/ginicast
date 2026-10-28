import json

import pytest

from ginicast_data.pipeline import process_metric, run_pipeline


def test_partial_failure_continues_and_records_manifest(workspace):
    root, registry = workspace
    (root / "data/raw_manual/manual/demo_index.csv").unlink()
    run = run_pipeline(config_registry=registry)
    assert run.exit_code == 1
    assert run.summary == {"success": 1, "failed": 1, "skipped": 0}
    failed, succeeded = run.metrics
    assert failed.error == "no_observations"
    assert not failed.outputs
    assert succeeded.status == "success"
    manifest = json.loads(run.manifest.read_text())
    assert manifest["exit_code"] == 1
    assert manifest["metrics"][0]["status"] == "failed"
    metadata = json.loads((root / "data/metadata/manual/demo_ratio.json").read_text())
    assert metadata["run_id"] == run.run_id
    assert metadata["input_sha256"]
    assert metadata["provenance_status"] == "unverified_manual_input"


def test_success_manifest_and_missing_observation_counts(workspace):
    root, registry = workspace
    run = run_pipeline(config_registry=registry)
    assert run.exit_code == 0
    assert run.summary == {"success": 2, "failed": 0, "skipped": 0}
    assert run.metrics[0].rows == 3
    assert run.metrics[0].missing_values == 1
    # Every invocation has a distinct manifest; no overwritten run history.
    assert run_pipeline(config_registry=registry).manifest != run.manifest


@pytest.mark.parametrize("csv", [
    "date,value\n2020-01-01,oops\n",
    "date,value\n2020-01-01,NaN\n2020-02-01,2\n",
    "date,value\n2020-01-01,N/A\n2020-02-01,2\n",
    "date,value\ninvalid,2\n",
    "date,value\n,2\n",
    "date,wrong_column\n2020-01-01,2\n",
    "date,value\n2020-01-01,inf\n",
    "date,value\n2020-01-01,\n",
    "date,value\n2020-01-01,1\n2020-01-01,2\n",
    "date,value\n",
])
def test_invalid_input_preserves_prior_outputs(workspace, csv):
    root, registry = workspace
    original = run_pipeline(config_registry=registry)
    assert original.exit_code == 0
    paths = [root / "data/standardized/demo_index.csv",
             root / "data/raw/manual/demo_index.csv",
             root / "data/metadata/manual/demo_index.json"]
    before = [path.read_bytes() for path in paths]
    (root / "data/raw_manual/manual/demo_index.csv").write_text(csv)
    result = process_metric(registry.get_metric("demo_index"), config_registry=registry)
    assert result.status == "failed"
    assert not result.outputs
    assert [path.read_bytes() for path in paths] == before


def test_disabled_and_empty_selection_are_not_success(workspace):
    _, registry = workspace
    registry.sources["manual"]["enabled"] = False
    run = run_pipeline(config_registry=registry)
    assert run.summary == {"success": 0, "failed": 0, "skipped": 2}
    assert run.exit_code == 1
    assert run_pipeline(core_only=True, config_registry=registry).exit_code == 1


def test_manifest_redacts_exception_text(workspace, monkeypatch, caplog):
    from ginicast_data import pipeline
    _, registry = workspace

    def failed(*args):
        raise RuntimeError("credential-bearing-url")

    monkeypatch.setattr(pipeline, "get_fetcher", failed)
    run = run_pipeline(config_registry=registry)
    assert run.exit_code == 1
    assert "credential-bearing-url" not in run.manifest.read_text()
    assert "credential-bearing-url" not in caplog.text


def test_source_with_default_options_is_valid(workspace):
    _, registry = workspace
    registry.sources["manual"] = {}
    assert run_pipeline(config_registry=registry).exit_code == 0


def test_output_failure_is_recorded_and_other_metrics_continue(workspace, monkeypatch):
    from ginicast_data import pipeline
    root, registry = workspace
    original = pipeline.write_metadata_json

    def fail_first(metadata, source, metric_id):
        if metric_id == "demo_index":
            raise OSError("disk failure")
        return original(metadata, source, metric_id)

    monkeypatch.setattr(pipeline, "write_metadata_json", fail_first)
    run = run_pipeline(config_registry=registry)
    assert run.exit_code == 1
    failed, succeeded = run.metrics
    assert failed.status == "failed"
    assert failed.error == "OSError"
    assert failed.rows == 3
    assert failed.missing_values == 1
    assert set(failed.outputs) == {"raw", "standardized"}
    assert not (root / "data/metadata/manual/demo_index.json").exists()
    assert succeeded.status == "success"
