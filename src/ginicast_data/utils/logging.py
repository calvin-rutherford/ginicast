import logging
import logging.config
import sys
from pathlib import Path

import yaml

from ginicast_data.io.paths import LOGGING_CONFIG_PATH, PROJECT_ROOT


def setup_logging():
    """Sets up Python logging using the logging.yaml configuration."""
    if LOGGING_CONFIG_PATH.exists():
        with open(LOGGING_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Ensure log directory exists specifically for file handlers
        for handler in config.get('handlers', {}).values():
            if 'filename' in handler:
                log_file = PROJECT_ROOT / Path(handler['filename'])
                handler['filename'] = str(log_file)
                log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def get_logger(name: str) -> logging.Logger:
    """Helper to get a logger by name."""
    return logging.getLogger(name)
