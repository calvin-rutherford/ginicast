"""Validate targeted pull requests before any fetcher or output is touched."""
import json
import re
from pathlib import Path


class SelectionError(ValueError):
    """A safe, user-facing selection error, containing no remote exception text."""


def select_metrics(registry, metric_ids: list[str]) -> list[dict]:
    metrics = []
    for metric_id in dict.fromkeys(metric_ids):
        metric = registry.get_metric(metric_id)
        if metric is None:
            raise SelectionError("Unknown metric ID; use 'ginicast-data metrics' to list configured IDs")
        metrics.append(metric)
    return metrics


def failed_metrics_from_manifest(path: Path, registry) -> tuple[list[str], str]:
    """Read IDs only; never reuse file paths or source configuration from a manifest."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise SelectionError("Cannot read run manifest; supply a readable GiniCast JSON manifest") from None
    if (not isinstance(data, dict) or type(data.get("manifest_version")) is not int
            or data["manifest_version"] != 1):
        raise SelectionError("Unsupported run manifest; expected manifest_version 1")
    run_id = data.get("run_id")
    entries = data.get("metrics")
    if not isinstance(run_id, str) or not re.fullmatch(r"[0-9a-f]{32}", run_id):
        raise SelectionError("Invalid manifest run_id")
    if not isinstance(entries, list):
        raise SelectionError("Invalid manifest metrics list")
    seen = set()
    failed = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise SelectionError("Invalid manifest metric entry")
        metric_id = entry.get("metric_id")
        status = entry.get("status")
        if not isinstance(metric_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", metric_id):
            raise SelectionError("Invalid manifest metric_id")
        if metric_id in seen or status not in ("success", "failed", "skipped"):
            raise SelectionError("Duplicate metric or invalid status in manifest")
        seen.add(metric_id)
        if status == "failed":
            failed.append(metric_id)
    select_metrics(registry, failed)
    return failed, run_id
