import os
from pathlib import Path

# Run from a repository/data workspace, or set GINICAST_ROOT explicitly.
PROJECT_ROOT = Path(os.environ.get("GINICAST_ROOT", Path.cwd())).resolve()

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_MANUAL_DIR = DATA_DIR / "raw_manual"
STANDARDIZED_DIR = DATA_DIR / "standardized"
METADATA_DIR = DATA_DIR / "metadata"
AUDIT_DIR = DATA_DIR / "audit"
RUNS_DIR = DATA_DIR / "runs"
LOGS_DIR = PROJECT_ROOT / "logs"

CONFIG_DIR = PROJECT_ROOT / "config"
METRICS_CONFIG_PATH = CONFIG_DIR / "metrics.yaml"
SOURCES_CONFIG_PATH = CONFIG_DIR / "sources.yaml"
LOGGING_CONFIG_PATH = CONFIG_DIR / "logging.yaml"

def ensure_directories():
    """Ensure all required data and log directories exist."""
    directories = [
        RAW_DIR, RAW_MANUAL_DIR, STANDARDIZED_DIR,
        METADATA_DIR, AUDIT_DIR, RUNS_DIR, LOGS_DIR
    ]
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
