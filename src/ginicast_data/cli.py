import argparse
import logging

from dotenv import load_dotenv

from ginicast_data.io.paths import PROJECT_ROOT, ensure_directories

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GiniCast Phase 1 Data Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    pull_parser = subparsers.add_parser("pull", help="Pull data from active fetchers")
    group = pull_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Pull all configured metrics")
    group.add_argument("--core", action="store_true", help="Pull core metrics only")
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
        from ginicast_data.utils.logging import setup_logging
        ensure_directories()
        setup_logging()
        if args.command == "pull":
            from ginicast_data.pipeline import run_pipeline
            return run_pipeline(core_only=args.core).exit_code
        from ginicast_data.audit import generate_audit_report
        generate_audit_report()
        return 0
    except Exception as exc:
        logger.error("Command failed (%s)", type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
