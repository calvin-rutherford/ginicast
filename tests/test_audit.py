import json

import pytest

from tests.test_cli import command


def test_audit_without_files_fails(workspace):
    root, _ = workspace
    result = command(root, "audit")
    assert result.returncode == 1
    assert "No standardized CSV" in result.stdout


@pytest.mark.parametrize("bad_csv", [
    "date,value\n2020-01-01,1\n",
    "not,the,right,columns\n1,2,3,4\n",
    "date,value,metric,source,frequency,units\n12:30,1,example,manual,monthly,Index\n",
    "date,value,metric,source,frequency,units\n2020-01-01,nope,example,manual,monthly,Index\n",
    "date,value,metric,source,frequency,units\n2020-01-01,1,example,manual,monthly,Index,extra\n",
    "date,value,metric,source,frequency,units\n",
])
def test_audit_failure_preserves_prior_reports(workspace, bad_csv):
    root, _ = workspace
    assert command(root, "pull", "--all").returncode == 0
    assert command(root, "audit").returncode == 0
    paths = [root / "data/audit/summary.csv", root / "data/audit/summary.md"]
    before = [path.read_bytes() for path in paths]
    (root / "data/standardized/bad.csv").write_text(bad_csv)
    result = command(root, "audit")
    assert result.returncode == 1
    assert "prior reports were not replaced" in result.stdout
    assert [path.read_bytes() for path in paths] == before
    assert json.loads(next((root / "data/runs").glob("*.json")).read_text())["exit_code"] == 0
