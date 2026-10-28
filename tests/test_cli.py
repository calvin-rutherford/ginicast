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
