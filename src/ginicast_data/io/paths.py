import os
from pathlib import Path

# Base project directory is three levels up from this file, assuming src/ginicast_data/io/paths.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_MANUAL_DIR = DATA_DIR / "raw_manual"
STANDARDIZED_DIR = DATA_DIR / "standardized"
METADATA_DIR = DATA_DIR / "metadata"
AUDIT_DIR = DATA_DIR / "audit"
LOGS_DIR = PROJECT_ROOT / "logs"

CONFIG_DIR = PROJECT_ROOT / "config"
METRICS_CONFIG_PATH = CONFIG_DIR / "metrics.yaml"
SOURCES_CONFIG_PATH = CONFIG_DIR / "sources.yaml"
LOGGING_CONFIG_PATH = CONFIG_DIR / "logging.yaml"

def ensure_directories():
    """Ensure all required data and log directories exist."""
    directories = [
        RAW_DIR, RAW_MANUAL_DIR, STANDARDIZED_DIR, 
        METADATA_DIR, AUDIT_DIR, LOGS_DIR
    ]
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
