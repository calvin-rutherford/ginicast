import json
import os
import subprocess
import sys


def command(root, *args):
    return subprocess.run([sys.executable, "-m", "ginicast_data.cli", *args],
                          env=dict(os.environ, GINICAST_ROOT=str(root)),
                          capture_output=True, text=True)


def test_cli_nonzero_partial_failure(workspace):
    root, _ = workspace
    (root / "data/raw_manual/manual/demo_ratio.csv").unlink()
    result = command(root, "pull", "--all")
    assert result.returncode == 1
    assert "demo_ratio: failed" in result.stdout
    assert "demo_index: success" in result.stdout
    manifest = json.loads(next((root / "data/runs").glob("*.json")).read_text())
    assert manifest["summary"]["failed"] == 1


def test_offline_doctor_is_truthful(workspace, monkeypatch):
    root, _ = workspace
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    result = command(root, "doctor")
    assert result.returncode == 0
    assert "PASS config structure: 2 metrics" in result.stdout
    assert "validity unverified" in result.stdout
    assert "no requests made" in result.stdout
    assert "healthy" not in result.stdout
    assert not (root / "logs").exists()


def test_doctor_invalid_config_fails_without_traceback(workspace):
    root, _ = workspace
    (root / "config/metrics.yaml").write_text("metrics: []\n")
    result = command(root, "doctor")
    assert result.returncode == 1
    assert "FAIL config" in result.stdout
    assert "Traceback" not in result.stderr


def test_help_needs_no_configuration(tmp_path):
    result = command(tmp_path, "--help")
    assert result.returncode == 0
    assert not (tmp_path / "data").exists()


def test_metric_discovery_is_offline_and_does_not_create_outputs(workspace):
    root, _ = workspace
    result = command(root, "metrics", "--source", "manual", "--json")
    assert result.returncode == 0
    assert [metric["metric_id"] for metric in json.loads(result.stdout)] == ["demo_index", "demo_ratio"]
    assert not (root / "data/runs").exists()
    assert not (root / "logs").exists()
    result = command(root, "metrics", "--category", "not-configured")
    assert result.returncode == 0
    assert "No metrics match" in result.stdout
    result = command(root, "metrics")
    assert result.returncode == 0
    assert "demo_index\tmanual" in result.stdout
    assert "availability and definitions unverified" in result.stdout


def test_targeted_pull_ignores_other_missing_inputs_and_deduplicates(workspace):
    root, _ = workspace
    (root / "data/raw_manual/manual/demo_index.csv").unlink()
    result = command(root, "pull", "--metric", "demo_ratio", "--metric", "demo_ratio")
    assert result.returncode == 0
    manifest = json.loads(next((root / "data/runs").glob("*.json")).read_text())
    assert manifest["selection"] == "metrics"
    assert [entry["metric_id"] for entry in manifest["metrics"]] == ["demo_ratio"]
    assert not (root / "data/standardized/demo_index.csv").exists()


def test_unknown_target_is_rejected_before_any_output(workspace):
    root, _ = workspace
    result = command(root, "pull", "--metric", "demo_ratio", "--metric", "not_configured")
    assert result.returncode == 1
    assert "Unknown metric ID" in result.stderr
    assert not (root / "data/runs").exists()
    assert not (root / "data/standardized").exists()


def test_retry_failed_manifest_only_reruns_failed_metrics(workspace):
    root, _ = workspace
    manual = root / "data/raw_manual/manual/demo_ratio.csv"
    original_input = manual.read_bytes()
    manual.unlink()
    assert command(root, "pull", "--all").returncode == 1
    prior_path = next((root / "data/runs").glob("*.json"))
    prior = json.loads(prior_path.read_text())
    successful_metadata = (root / "data/metadata/manual/demo_index.json").read_bytes()
    manual.write_bytes(original_input)
    result = command(root, "pull", "--retry-manifest", str(prior_path))
    assert result.returncode == 0
    new_path, = [path for path in (root / "data/runs").glob("*.json") if path != prior_path]
    new = json.loads(new_path.read_text())
    assert new["selection"] == "retry_failed"
    assert new["retry_of"] == prior["run_id"]
    assert new["summary"] == {"success": 1, "failed": 0, "skipped": 0}
    assert [entry["metric_id"] for entry in new["metrics"]] == ["demo_ratio"]
    assert (root / "data/metadata/manual/demo_index.json").read_bytes() == successful_metadata
    assert json.loads(prior_path.read_text()) == prior
    # A successful manifest has nothing to rerun and produces no acquisition.
    result = command(root, "pull", "--retry-manifest", str(new_path))
    assert result.returncode == 0
    assert "No failed metrics" in result.stdout
    assert len(list((root / "data/runs").glob("*.json"))) == 2


def test_bad_retry_manifest_is_rejected_before_outputs(workspace):
    root, _ = workspace
    bad = root / "bad.json"
    bad.write_text('{"manifest_version": 500}')
    result = command(root, "pull", "--retry-manifest", str(bad))
    assert result.returncode == 1
    assert "Unsupported run manifest" in result.stderr
    assert not (root / "data/runs").exists()


def test_pull_selectors_are_mutually_exclusive(workspace):
    root, _ = workspace
    result = command(root, "pull", "--core", "--metric", "demo_index")
    assert result.returncode == 2
    assert not (root / "data/runs").exists()
