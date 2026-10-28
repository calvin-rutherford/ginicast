import pandas as pd
import pytest

from ginicast_data.standardize.normalize_dates import normalize_date_column
from ginicast_data.standardize.schema import STANDARD_COLUMNS, enforce_schema


def test_enforce_schema():
    df = pd.DataFrame({
        "date": ["2020-01-01", "2020-02-01"],
        "value": ["100.5", "200.7"],
        "extra_col": [1, 2] # Should be dropped
    })

    std_df = enforce_schema(df, "test_metric", "test_source", "monthly", "Index")

    # Check columns
    assert list(std_df.columns) == STANDARD_COLUMNS

    # Check values
    assert std_df["value"].iloc[0] == 100.5
    assert std_df["metric"].iloc[0] == "test_metric"
    assert std_df["source"].iloc[0] == "test_source"

def test_normalize_date_column():
    df = pd.DataFrame({
        "date": ["2020/01/01", "01-15-2020", "20200201"]
    })

    norm_df = normalize_date_column(df, "date")

    assert norm_df["date"].iloc[0] == "2020-01-01"
    assert norm_df["date"].iloc[1] == "2020-01-15"
    assert norm_df["date"].iloc[2] == "2020-02-01"


@pytest.mark.parametrize("date", ["12:00", "12:30", "January 1", "2020", "2020-01", "today", None])
def test_incomplete_dates_are_rejected(date):
    with pytest.raises(ValueError):
        normalize_date_column(pd.DataFrame({"date": [date]}))
