from unittest.mock import Mock

import pytest

from ginicast_data.io.writers import write_csv, write_json


def test_failed_csv_write_preserves_destination_and_cleans_temporary(tmp_path):
    output = tmp_path / "metric.csv"
    output.write_text("original\n")

    def fail(stream, **kwargs):
        stream.write("partial\n")
        raise OSError("disk failure")

    frame = Mock()
    frame.to_csv.side_effect = fail
    with pytest.raises(OSError):
        write_csv(frame, output)
    assert output.read_text() == "original\n"
    assert list(tmp_path.iterdir()) == [output]


def test_failed_json_write_preserves_destination(tmp_path):
    output = tmp_path / "manifest.json"
    output.write_text('{"original": true}\n')
    with pytest.raises(ValueError):
        write_json({"value": float("nan")}, output)
    assert output.read_text() == '{"original": true}\n'
    assert list(tmp_path.iterdir()) == [output]
