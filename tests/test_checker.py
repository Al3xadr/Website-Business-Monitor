import requests
from unittest.mock import patch, Mock

from app.checker import check_site


@patch("app.checker.requests.get")
def test_http_200(mock_get):
    fake_response = Mock()
    fake_response.status_code = 200
    mock_get.return_value = fake_response

    result = check_site("https://example.com")

    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["reason"] == "OK"


@patch("app.checker.requests.get")
def test_http_404(mock_get):
    fake_response = Mock()
    fake_response.status_code = 404
    mock_get.return_value = fake_response

    result = check_site("https://example.com")

    assert result["ok"] is False
    assert result["status_code"] == 404
    assert result["reason"] == "HTTP_404"


@patch("app.checker.requests.get")
def test_http_500(mock_get):
    fake_response = Mock()
    fake_response.status_code = 500
    mock_get.return_value = fake_response

    result = check_site("https://example.com")

    assert result["ok"] is False
    assert result["status_code"] == 500
    assert result["reason"] == "HTTP_500"


@patch("app.checker.requests.get")
def test_timeout(mock_get):
    mock_get.side_effect = requests.exceptions.Timeout

    result = check_site("https://example.com")

    assert result["ok"] is False
    assert result["status_code"] is None
    assert result["response_time"] is None
    assert result["reason"] == "TIMEOUT"


@patch("app.checker.requests.get")
def test_connection_error(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError

    result = check_site("https://example.com")

    assert result["ok"] is False
    assert result["status_code"] is None
    assert result["response_time"] is None
    assert result["reason"] == "CONNECTION_ERROR"


@patch("app.checker.requests.get")
def test_result_has_common_fields(mock_get):
    fake_response = Mock()
    fake_response.status_code = 200
    mock_get.return_value = fake_response

    result = check_site("https://example.com")

    assert "url" in result
    assert "ok" in result
    assert "status_code" in result
    assert "response_time" in result
    assert "reason" in result
    assert "checked_at" in result
    assert result["url"] == "https://example.com"