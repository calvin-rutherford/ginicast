"""Sequential acquisition with explicit outcomes and a manifest for every completed batch."""
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from uuid import uuid4

from ginicast_data.fetch import get_fetcher
from ginicast_data.io.paths import RUNS_DIR
from ginicast_data.io.writers import (
    write_json,
    write_metadata_json,
    write_raw_csv,
    write_standardized_csv,
)
from ginicast_data.registry import get_registry
from ginicast_data.selection import select_metrics
from ginicast_data.standardize.normalize_dates import normalize_date_column
from ginicast_data.standardize.schema import enforce_schema
from ginicast_data.utils.time import current_timestamp_iso

logger = logging.getLogger(__name__)


@dataclass
class MetricResult:
    metric_id: str
    source: str
    status: str
    rows: int = 0
    missing_values: int = 0
    error: str | None = None
    outputs: dict[str, str] = field(default_factory=dict)


@dataclass
class RunResult:
    run_id: str
    started_at: str
    finished_at: str
    metrics: list[MetricResult]
    manifest: Path

    @property
    def exit_code(self) -> int:
        return 0 if self.metrics and all(m.status == "success" for m in self.metrics) else 1

    @property
    def summary(self) -> dict[str, int]:
        return {status: sum(m.status == status for m in self.metrics)
                for status in ("success", "failed", "skipped")}


def process_metric(metric_config: dict, *, config_registry=None, run_id=None) -> MetricResult:
    config_registry = config_registry or get_registry()
    metric_id = metric_config["metric_id"]
    source_name = metric_config["source"]
    result = MetricResult(metric_id, source_name, "failed")
    source_config = config_registry.get_source_config(source_name)
    if source_name not in config_registry.sources:
        result.error = "missing_source_config"
        return result
    if not source_config.get("enabled", True):
        result.status = "skipped"
        result.error = "source_disabled"
        return result
    try:
        fetcher = get_fetcher(source_name, source_config)
        df, metadata = fetcher.fetch(metric_config)
        if df is None or df.empty:
            result.error = "no_observations"
            return result
        # Validate the complete frame before replacing any prior output.
        df_std = enforce_schema(
            normalize_date_column(df), metric_id, source_name,
            metric_config.get("expected_frequency", "unknown"),
            metric_config.get("units", "unknown"),
        ).sort_values("date").reset_index(drop=True)
        result.rows = len(df_std)
        result.missing_values = int(df_std["value"].isna().sum())
        metadata = dict(metadata, run_id=run_id, standardized_rows_count=result.rows,
                        missing_values=result.missing_values)
        result.outputs["raw"] = str(write_raw_csv(df, source_name, metric_id))
        result.outputs["standardized"] = str(write_standardized_csv(df_std, metric_id))
        result.outputs["metadata"] = str(write_metadata_json(metadata, source_name, metric_id))
        result.status = "success"
    except Exception as exc:
        # HTTP exception text can contain credential-bearing URLs. Keep reports/logs safe.
        result.error = type(exc).__name__
        logger.error("Metric %s failed (%s)", metric_id, result.error)
    return result


def run_pipeline(core_only: bool = False, *, config_registry=None,
                 metric_ids: list[str] | None = None, retry_of: str | None = None) -> RunResult:
    config_registry = config_registry or get_registry()
    if metric_ids is not None:
        if core_only:
            raise ValueError("Choose core_only or metric_ids, not both")
        metrics = select_metrics(config_registry, metric_ids)
        selection = "retry_failed" if retry_of else "metrics"
    else:
        metrics = config_registry.get_core_metrics() if core_only else config_registry.get_all_metrics()
        selection = "core" if core_only else "all"
    started = current_timestamp_iso()
    run_id = uuid4().hex
    results = [process_metric(metric, config_registry=config_registry, run_id=run_id)
               for metric in metrics]
    run = RunResult(run_id, started, current_timestamp_iso(), results, RUNS_DIR / f"{run_id}.json")
    write_json({
        "manifest_version": 1, "run_id": run_id, "started_at": run.started_at,
        "finished_at": run.finished_at, "selection": selection, "retry_of": retry_of,
        "summary": run.summary, "exit_code": run.exit_code,
        "metrics": [asdict(result) for result in results],
    }, run.manifest)
    for result in results:
        logger.info("%s: %s (%s rows, %s missing)%s", result.metric_id, result.status,
                    result.rows, result.missing_values,
                    f" [{result.error}]" if result.error else "")
    logger.info("Run summary: %s; manifest: %s", run.summary, run.manifest)
    return run
