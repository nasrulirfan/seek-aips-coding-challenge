from __future__ import annotations

from textwrap import dedent

import pytest

from traffic_counter import (
    AnalysisResult,
    TrafficRecord,
    analyse_stream,
    parse_records,
    quietest_period,
    top_half_hours,
    total_cars,
    totals_by_day,
)


@pytest.fixture
def sample_text() -> str:
    return dedent(
        """
        2021-12-01T05:00:00 5
        2021-12-01T05:30:00 12
        2021-12-01T06:00:00 14
        2021-12-01T10:00:00 3
        2021-12-01T10:30:00 2
        2021-12-02T07:00:00 9
        2021-12-02T07:30:00 9
        2021-12-02T08:00:00 11
        """
    ).strip()


@pytest.fixture
def records(sample_text: str):
    return parse_records(sample_text.splitlines())


def test_parse_records_sorted(records):
    timestamps = [record.timestamp for record in records]
    assert timestamps == sorted(timestamps)


def test_total_cars(records):
    assert total_cars(records) == sum(record.cars for record in records)


def test_totals_by_day(records):
    assert totals_by_day(records) == [
        ("2021-12-01", 5 + 12 + 14 + 3 + 2),
        ("2021-12-02", 9 + 9 + 11),
    ]


def test_top_half_hours(records):
    top = top_half_hours(records, limit=2)
    assert [item.cars for item in top] == [14, 12]


def test_quietest_period_skips_non_contiguous(records):
    # Expect to skip the window that crosses the 4-hour gap
    window = quietest_period(records, size=3)
    assert tuple(item.timestamp.isoformat() for item in window) == (
        "2021-12-02T07:00:00",
        "2021-12-02T07:30:00",
        "2021-12-02T08:00:00",
    )


def test_quietest_period_requires_window(records):
    with pytest.raises(ValueError):
        quietest_period(records[:2], size=3)


def test_traffic_record_rejects_negative_counts(records):
    with pytest.raises(ValueError):
        TrafficRecord(timestamp=records[0].timestamp, cars=-1)


def test_analyse_stream_matches_batch(records, sample_text):
    result = analyse_stream(sample_text.splitlines())
    assert isinstance(result, AnalysisResult)
    assert result.total == total_cars(records)
    assert result.per_day == totals_by_day(records)
    assert [item.cars for item in result.top_half_hours] == [14, 12, 11]
    assert result.quietest_window is not None
    assert tuple(entry.timestamp.isoformat() for entry in result.quietest_window) == (
        "2021-12-02T07:00:00",
        "2021-12-02T07:30:00",
        "2021-12-02T08:00:00",
    )
