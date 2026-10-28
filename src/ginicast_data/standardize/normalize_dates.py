import pandas as pd


def normalize_date_column(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """Reject missing/invalid dates; normalize valid date strings to ISO dates."""
    if date_col not in df.columns:
        raise ValueError(f"Missing date column: {date_col}")
    df = df.copy()
    # String conversion prevents integer years from becoming nanoseconds since epoch.
    parsed = pd.to_datetime(df[date_col].astype("string"), errors="coerce", format="mixed")
    if parsed.isna().any():
        raise ValueError("Input contains missing or invalid dates")
    df[date_col] = parsed.dt.strftime("%Y-%m-%d")
    return df
