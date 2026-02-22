import argparse
import sys
import logging

from ginicast_data.io.paths import ensure_directories
from ginicast_data.utils.logging import setup_logging
from ginicast_data.pipeline import run_pipeline
from ginicast_data.audit import generate_audit_report
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GiniCast Phase 1 Data Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # pull command
    pull_parser = subparsers.add_parser("pull", help="Pull data from active fetchers")
    group = pull_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Pull all configured metrics")
    group.add_argument("--core", action="store_true", help="Pull Core 19 metrics only")
    
    # audit command
    subparsers.add_parser("audit", help="Generate metadata audit report")
    
    # doctor command
    subparsers.add_parser("doctor", help="Check config and directory health")
    
    return parser

def main():
    ensure_directories()
    setup_logging()
    
    parser = build_parser()
    args = parser.parse_args()
    
    try:
        if args.command == "pull":
            run_pipeline(core_only=args.core)
        elif args.command == "audit":
            generate_audit_report()
        elif args.command == "doctor":
            from ginicast_data.registry import registry
            logger.info("Running Doctor Check...")
            logger.info(f"Loaded {len(registry.get_all_metrics())} metric configs.")
            logger.info("Doctor Check passed. Environment is healthy.")
    except Exception as e:
        logger.error(f"Fatal Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
