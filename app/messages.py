from datetime import datetime


def format_alert_message(result):
    """Форматирует сообщение о падении для Telegram."""
    dt = datetime.fromisoformat(result["checked_at"])
    time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "🔴 Website DOWN",
        "",
        f"URL: {result['url']}",
    ]

    if result["status_code"] is not None:
        lines.append(f"HTTP status: {result['status_code']}")

    lines.append(f"Reason: {result['reason']}")
    lines.append(f"Time: {time_str}")

    return "\n".join(lines)


def format_recovered_message(result):
    """Форматирует сообщение о восстановлении для Telegram."""
    dt = datetime.fromisoformat(result["checked_at"])
    time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = [
        "🟢 Website RECOVERED",
        "",
        f"URL: {result['url']}",
    ]

    if result["status_code"] is not None:
        lines.append(f"HTTP status: {result['status_code']}")

    if result["response_time"] is not None:
        lines.append(f"Response time: {result['response_time']:.2f} seconds")

    lines.append(f"Time: {time_str}")

    return "\n".join(lines)