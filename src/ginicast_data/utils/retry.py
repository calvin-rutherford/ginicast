import logging

import requests
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


def is_transient(exc: BaseException) -> bool:
    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return True
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code == 429 or 500 <= exc.response.status_code < 600
    return False


def log_retry_attempt(retry_state):
    # Exception text may expose API keys embedded in URLs.
    logger.warning("Transient HTTP failure (%s); retrying after attempt %s",
                   type(retry_state.outcome.exception()).__name__, retry_state.attempt_number)


api_retry = retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(4),
    retry=retry_if_exception(is_transient),
    before_sleep=log_retry_attempt,
    reraise=True,
)
