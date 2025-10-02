from __future__ import annotations

from textwrap import dedent

import pytest

from traffic_counter import cli


def write_data(tmp_path, text: str):
    data_file = tmp_path / "data.txt"
    data_file.write_text(dedent(text).strip() + "\n", encoding="utf-8")
    return data_file


def test_cli_outputs_expected_sections(tmp_path, capsys):
    path = write_data(
        tmp_path,
        """
        2021-12-01T05:00:00 5
        2021-12-01T05:30:00 12
        2021-12-01T06:00:00 14
        2021-12-01T06:30:00 15
        2021-12-01T07:00:00 25
        """,
    )

    exit_code = cli.main([str(path)])
    assert exit_code == 0

    captured = capsys.readouterr().out
    assert "Total: 71" in captured
    assert "Cars per day:" in captured
    assert "2021-12-01 71" in captured
    assert "Top 3 half hours:" in captured
    assert "2021-12-01T07:00:00 25" in captured
    assert "Least busy 1.5h period:" in captured
    assert "Start: 2021-12-01T05:00:00" in captured
    assert "Total: 31" in captured


def test_cli_handles_insufficient_window(tmp_path, capsys):
    path = write_data(
        tmp_path,
        """
        2021-12-01T05:00:00 5
        2021-12-01T07:00:00 3
        """,
    )

    exit_code = cli.main([str(path)])
    assert exit_code == 0

    captured = capsys.readouterr().out
    assert "<not available>" in captured


def test_cli_missing_file(tmp_path):
    with pytest.raises(SystemExit):
        cli.main([str(tmp_path / "missing.txt")])
