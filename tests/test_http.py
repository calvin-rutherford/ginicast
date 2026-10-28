from unittest.mock import Mock

import pytest
import requests
from tenacity import wait_none

from ginicast_data.utils.http import safe_get, safe_post


@pytest.mark.parametrize("method", [safe_get, safe_post])
@pytest.mark.parametrize("status,attempts", [(429, 4), (503, 4), (401, 1), (404, 1)])
def test_http_retry_bound_and_permanent_failure(method, status, attempts, caplog):
    response = requests.Response()
    response.status_code = status
    response.url = "https://example.invalid/?api_key=private-token"
    session = Mock()
    session.get.return_value = session.post.return_value = response
    with pytest.raises(requests.HTTPError):
        method.retry_with(wait=wait_none())(session, "https://example.invalid")
    call = session.get if method is safe_get else session.post
    assert call.call_count == attempts
    assert call.call_args.kwargs["timeout"] == 10
    assert "private-token" not in caplog.text


@pytest.mark.parametrize("failure", [requests.Timeout, requests.ConnectionError])
def test_transient_connection_recovers(failure):
    response = Mock()
    session = Mock()
    session.get.side_effect = [failure(), response]
    assert safe_get.retry_with(wait=wait_none())(session, "https://example.invalid") is response
    assert session.get.call_count == 2
