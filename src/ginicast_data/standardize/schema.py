import math

import pandas as pd

# Standard columns for all metrics in the standardized output
STANDARD_COLUMNS = [
    "date",        # YYYY-MM-DD
    "value",       # float
    "metric",      # metric_id
    "source",      # source name
    "frequency",   # expected frequency
    "units"        # units from config
]

def enforce_schema(df: pd.DataFrame, metric_id: str, source: str, frequency: str, units: str) -> pd.DataFrame:
    """
    Ensures the dataframe matches the target standardized schema.
    Assumes df already has 'date' and 'value' columns.
    """
    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(f"DataFrame for {metric_id} must have 'date' and 'value' columns.")

    df = df.copy()

    # Missing observations are allowed, malformed tokens and infinities are not.
    original = df["value"]
    numeric = pd.to_numeric(original, errors="coerce")
    if (original.notna() & numeric.isna()).any():
        raise ValueError("Input contains invalid numeric values")
    if not numeric.dropna().map(math.isfinite).all():
        raise ValueError("Input contains non-finite values")
    if not numeric.notna().any():
        raise ValueError("Input contains no numeric observations")
    if df["date"].duplicated().any():
        raise ValueError("Input contains duplicate dates")
    df["value"] = numeric

    # Add metadata columns
    df["metric"] = metric_id
    df["source"] = source
    df["frequency"] = frequency
    df["units"] = units

    # Select and order columns
    return df[STANDARD_COLUMNS]
