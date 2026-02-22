import pandas as pd

def normalize_date_column(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """
    Normalizes a date column to ISO 'YYYY-MM-DD' format.
    Handles different formats gracefully depending on the input.
    """
    df = df.copy()
    if date_col not in df.columns:
        return df
        
    # parse dates, coerce errors to NaT
    parsed = pd.to_datetime(df[date_col], errors="coerce", format="mixed")
    
    # format back to string YYYY-MM-DD
    # We must filter NaT to avoid converting it to a string 'NaT'
    df[date_col] = parsed.dt.strftime("%Y-%m-%d")
    df[date_col] = df[date_col].fillna("N/A")

    
    return df
