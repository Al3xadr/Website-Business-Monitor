from app.messages import format_alert_message, format_recovered_message


def test_format_alert_contains_url_and_reason():
    result = {
        "url": "https://example.com",
        "status_code": 500,
        "response_time": 0.42,
        "reason": "HTTP_500",
        "checked_at": "2026-10-02T15:20:31+00:00",
    }

    msg = format_alert_message(result)

    assert "🔴" in msg
    assert "Website DOWN" in msg
    assert "https://example.com" in msg
    assert "500" in msg
    assert "HTTP_500" in msg


def test_format_recovered_contains_url_and_time():
    result = {
        "url": "https://example.com",
        "status_code": 200,
        "response_time": 0.42,
        "reason": "OK",
        "checked_at": "2026-10-02T15:25:12+00:00",
    }

    msg = format_recovered_message(result)

    assert "🟢" in msg
    assert "RECOVERED" in msg
    assert "https://example.com" in msg
    assert "200" in msg
    assert "0.42" in msg


def test_format_alert_without_status_code():
    """Timeout — нет HTTP-статуса."""
    result = {
        "url": "https://example.com",
        "status_code": None,
        "response_time": None,
        "reason": "TIMEOUT",
        "checked_at": "2026-10-02T15:20:31+00:00",
    }

    msg = format_alert_message(result)

    assert "TIMEOUT" in msg
    assert "HTTP status" not in msg  # не должно быть строки про статус