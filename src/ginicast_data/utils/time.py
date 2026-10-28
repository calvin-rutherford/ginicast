from datetime import datetime, timezone


def current_timestamp_iso() -> str:
    """Returns the current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()
