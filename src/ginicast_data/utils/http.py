import logging
from typing import Any

import requests

from ginicast_data.utils.retry import api_retry

logger = logging.getLogger(__name__)

def create_session() -> requests.Session:
    """Creates a requests standard session."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "GiniCastPhase1/1.0"
    })
    return session

@api_retry
def safe_get(session: requests.Session, url: str, params: dict | None = None, **kwargs) -> requests.Response:
    """Safe GET request that handles retries."""
    logger.debug(f"GET {url}")
    response = session.get(url, params=params, timeout=10, **kwargs)
    response.raise_for_status()
    return response

@api_retry
def safe_post(session: requests.Session, url: str, json: Any | None = None, **kwargs) -> requests.Response:
    """Safe POST request that handles retries."""
    logger.debug(f"POST {url}")
    response = session.post(url, json=json, timeout=10, **kwargs)
    response.raise_for_status()
    return response
