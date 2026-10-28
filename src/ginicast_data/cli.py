import argparse
import json
import logging
from pathlib import Path

from dotenv import load_dotenv

from ginicast_data.io.paths import PROJECT_ROOT, ensure_directories
from ginicast_data.selection import SelectionError

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GiniCast Phase 1 Data Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    pull_parser = subparsers.add_parser("pull", help="Pull data from active fetchers")
    group = pull_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Pull all configured metrics")
    group.add_argument("--core", action="store_true", help="Pull core metrics only")
    group.add_argument("--metric", action="append", metavar="ID",
                       help="Pull one configured metric; repeat for multiple IDs")
    group.add_argument("--retry-manifest", type=Path, metavar="PATH",
                       help="Rerun only failed metrics from a previous run manifest")
    metrics_parser = subparsers.add_parser("metrics", help="List configured metric targets offline")
    metrics_parser.add_argument("--source", help="Filter by configured source")
    metrics_parser.add_argument("--category", help="Filter by category, e.g. core or candidate")
    metrics_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    subparsers.add_parser("audit", help="Generate metadata audit report")
    subparsers.add_parser("doctor", help="Check local config/dependencies offline")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    try:
        if args.command == "doctor":
            from ginicast_data.doctor import check_offline
            messages, exit_code = check_offline()
            print("\n".join(messages))
            return exit_code
        if args.command == "metrics":
            from ginicast_data.registry import get_registry
            metrics = get_registry().filter_metrics(source=args.source, category=args.category)
            if args.json:
                print(json.dumps(metrics, indent=2))
            elif not metrics:
                print("No metrics match the filters")
            else:
                print("metric_id\tsource\tcategory\tfrequency\tunits")
                for metric in metrics:
                    print("\t".join(str(metric.get(key, "")) for key in
                                    ("metric_id", "source", "category", "expected_frequency", "units")))
                print(f"{len(metrics)} configured targets; availability and definitions unverified")
            return 0
        metric_ids = None
        retry_of = None
        if args.command == "pull":
            from ginicast_data.registry import get_registry
            from ginicast_data.selection import (
                failed_metrics_from_manifest,
                select_metrics,
            )
            if args.retry_manifest is not None:
                metric_ids, retry_of = failed_metrics_from_manifest(args.retry_manifest, get_registry())
                if not metric_ids:
                    print("No failed metrics in the manifest; no acquisition performed")
                    return 0
            elif args.metric is not None:
                metric_ids = [metric["metric_id"] for metric in select_metrics(get_registry(), args.metric)]
        from ginicast_data.utils.logging import setup_logging
        ensure_directories()
        setup_logging()
        if args.command == "pull":
            from ginicast_data.pipeline import run_pipeline
            return run_pipeline(core_only=args.core, metric_ids=metric_ids, retry_of=retry_of).exit_code
        from ginicast_data.audit import generate_audit_report
        return generate_audit_report()
    except SelectionError as exc:
        logger.error("Invalid selection: %s", exc)
        return 1
    except Exception as exc:
        logger.error("Command failed (%s)", type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
