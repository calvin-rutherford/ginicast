from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import requests
import logging

logger = logging.getLogger(__name__)

def log_retry_attempt(retry_state):
    """Logs when a retry happens."""
    if retry_state.attempt_number > 1:
        logger.warning(
            f"Retrying: attempt {retry_state.attempt_number} after error: {retry_state.outcome.exception()}"
        )

# Common retry decorator for HTTP requests
api_retry = retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(4),
    retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.HTTPError, requests.exceptions.Timeout)),
    after=log_retry_attempt,
    reraise=True
)
