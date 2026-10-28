#!/usr/bin/env python3
"""Exercise the installed CLI using synthetic CSVs, never external data APIs."""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "examples" / "offline"


def run_demo(root: Path) -> None:
    # copytree refuses existing targets to protect prior data.
    shutil.copytree(FIXTURE / "config", root / "config")
    shutil.copytree(FIXTURE / "data", root / "data")
    env = dict(os.environ, GINICAST_ROOT=str(root))
    listed = subprocess.run([sys.executable, "-m", "ginicast_data.cli", "metrics", "--json"],
                            env=env, check=True, capture_output=True, text=True)
    assert [metric["metric_id"] for metric in json.loads(listed.stdout)] == ["demo_index", "demo_ratio"]
    subprocess.run([sys.executable, "-m", "ginicast_data.cli", "doctor"], env=env, check=True)
    subprocess.run([sys.executable, "-m", "ginicast_data.cli", "pull", "--all"], env=env, check=True)
    for expected in (FIXTURE / "expected").glob("*.csv"):
        actual = root / "data" / "standardized" / expected.name
        if actual.read_bytes() != expected.read_bytes():
            raise AssertionError(f"Output differs from fixture: {expected.name}")
    manifests = list((root / "data" / "runs").glob("*.json"))
    assert len(manifests) == 1
    manifest = json.loads(manifests[0].read_text())
    assert manifest["summary"] == {"success": 2, "failed": 0, "skipped": 0}
    assert manifest["exit_code"] == 0
    assert sum(item["rows"] for item in manifest["metrics"]) == 5
    assert sum(item["missing_values"] for item in manifest["metrics"]) == 1
    subprocess.run([sys.executable, "-m", "ginicast_data.cli", "audit"], env=env, check=True)
    assert (root / "data" / "audit" / "summary.csv").is_file()
    print("Demo verified: 2 successful synthetic metrics, 5 rows, 1 missing observation; exact CSVs match")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="New directory to retain demo artifacts")
    args = parser.parse_args()
    if args.output_dir:
        root = args.output_dir.resolve()
        root.mkdir(parents=True, exist_ok=False)
        run_demo(root)
        print(f"Demo artifacts: {root}")
    else:
        with TemporaryDirectory(prefix="ginicast-demo-") as directory:
            run_demo(Path(directory))


if __name__ == "__main__":
    main()
