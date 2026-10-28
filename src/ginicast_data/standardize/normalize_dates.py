import pandas as pd


def normalize_date_column(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Reject missing/invalid dates; normalize valid date strings to ISO dates."""
    if date_col not in df.columns:
        raise ValueError(f"Missing date column: {date_col}")
    df = df.copy()
    # Require a complete date. Pandas otherwise anchors time-only/partial inputs
    # to the current date, making the same input vary between runs.
    values = df[date_col].astype("string")
    date_only = (r"(?:[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}|[0-9]{4}/[0-9]{1,2}/[0-9]{1,2}|"
                 r"[0-9]{1,2}-[0-9]{1,2}-[0-9]{4}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}|[0-9]{8})")
    if not values.str.fullmatch(date_only, na=False).all():
        raise ValueError("Input must contain complete calendar dates")
    parsed = pd.to_datetime(values, errors="coerce", format="mixed")
    if parsed.isna().any():
        raise ValueError("Input contains missing or invalid dates")
    df[date_col] = parsed.dt.strftime("%Y-%m-%d")
    return df
