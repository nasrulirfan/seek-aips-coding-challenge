from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Sequence


HALF_HOUR = timedelta(minutes=30)


@dataclass(frozen=True)
class TrafficRecord:
    """Represents the number of cars seen during a half-hour window."""

    timestamp: datetime
    cars: int

    def __post_init__(self) -> None:  # type: ignore[override]
        if self.cars < 0:
            raise ValueError("car count must be non-negative")


def parse_records(lines: Iterable[str]) -> List[TrafficRecord]:
    """Parse traffic records from an iterable of raw lines."""

    records: List[TrafficRecord] = []
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line:
            continue
        try:
            timestamp_str, cars_str = line.split(maxsplit=1)
        except ValueError as exc:
            raise ValueError(f"Line {number} is not in '<timestamp> <count>' format: {raw!r}") from exc
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError as exc:
            raise ValueError(f"Line {number} has invalid timestamp: {timestamp_str}") from exc
        try:
            cars = int(cars_str)
        except ValueError as exc:
            raise ValueError(f"Line {number} has invalid car count: {cars_str}") from exc
        records.append(TrafficRecord(timestamp=timestamp, cars=cars))
    records.sort(key=lambda record: record.timestamp)
    return records


def read_records(path: Path) -> List[TrafficRecord]:
    """Read and parse traffic records from a file path."""

    with path.open("r", encoding="utf-8") as handle:
        return parse_records(handle)


def total_cars(records: Sequence[TrafficRecord]) -> int:
    return sum(record.cars for record in records)


def totals_by_day(records: Sequence[TrafficRecord]) -> List[tuple[str, int]]:
    daily: dict[str, int] = {}
    for record in records:
        day = record.timestamp.date().isoformat()
        daily[day] = daily.get(day, 0) + record.cars
    return sorted(daily.items())


def top_half_hours(records: Sequence[TrafficRecord], limit: int = 3) -> List[TrafficRecord]:
    return sorted(records, key=lambda record: (-record.cars, record.timestamp))[:limit]


def contiguous_windows(records: Sequence[TrafficRecord], size: int) -> Iterable[tuple[TrafficRecord, ...]]:
    if size <= 0:
        raise ValueError("size must be positive")
    for start in range(len(records) - size + 1):
        window = records[start : start + size]
        if all(window[index + 1].timestamp - window[index].timestamp == HALF_HOUR for index in range(size - 1)):
            yield tuple(window)


def quietest_period(records: Sequence[TrafficRecord], size: int = 3) -> tuple[TrafficRecord, ...]:
    best: tuple[TrafficRecord, ...] | None = None
    best_total = None
    for window in contiguous_windows(records, size):
        window_total = sum(record.cars for record in window)
        if best is None or window_total < best_total or (
            window_total == best_total and window[0].timestamp < best[0].timestamp
        ):
            best = window
            best_total = window_total
    if best is None:
        raise ValueError("No contiguous window found")
    return best


__all__ = [
    "TrafficRecord",
    "parse_records",
    "read_records",
    "total_cars",
    "totals_by_day",
    "top_half_hours",
    "quietest_period",
]
