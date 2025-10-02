from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence

HALF_HOUR = timedelta(minutes=30)


@dataclass(frozen=True)
class TrafficRecord:
    """Represents the number of cars seen during a half-hour window."""

    timestamp: datetime
    cars: int

    def __post_init__(self) -> None:  # type: ignore[override]
        if self.cars < 0:
            raise ValueError("car count must be non-negative")


@dataclass(frozen=True)
class AnalysisResult:
    total: int
    per_day: List[tuple[str, int]]
    top_half_hours: List[TrafficRecord]
    quietest_window: tuple[TrafficRecord, ...] | None


def _parse_line(raw: str, number: int) -> TrafficRecord | None:
    line = raw.strip()
    if not line:
        return None
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
    return TrafficRecord(timestamp=timestamp, cars=cars)


def parse_records(lines: Iterable[str]) -> List[TrafficRecord]:
    """Parse traffic records from an iterable of raw lines."""

    records: List[TrafficRecord] = []
    for number, raw in enumerate(lines, 1):
        record = _parse_line(raw, number)
        if record is not None:
            records.append(record)
    # Ensure downstream logic consumes records in chronological order.
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


def contiguous_windows(records: Sequence[TrafficRecord], size: int) -> Iterator[tuple[TrafficRecord, ...]]:
    if size <= 0:
        raise ValueError("size must be positive")
    for start in range(len(records) - size + 1):
        window = records[start : start + size]
        # Skip windows that include gaps; only strict 30-minute steps qualify.
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
            # On ties prefer the earliest start so results stay deterministic.
            best = window
            best_total = window_total
    if best is None:
        raise ValueError("No contiguous window found")
    return best


def analyse_stream(
    lines: Iterable[str],
    *,
    window_size: int = 3,
    top_limit: int = 3,
) -> AnalysisResult:
    if window_size <= 0:
        raise ValueError("window_size must be positive")
    if top_limit <= 0:
        raise ValueError("top_limit must be positive")

    total = 0
    daily: dict[str, int] = {}
    top_records: List[TrafficRecord] = []
    buffer: List[TrafficRecord] = []
    best_window: tuple[TrafficRecord, ...] | None = None
    best_total: int | None = None

    for number, raw in enumerate(lines, 1):
        record = _parse_line(raw, number)
        if record is None:
            continue

        total += record.cars
        day_key = record.timestamp.date().isoformat()
        daily[day_key] = daily.get(day_key, 0) + record.cars

        # Maintain the top busiest periods with deterministic ordering.
        top_records.append(record)
        top_records.sort(key=lambda item: (-item.cars, item.timestamp))
        if len(top_records) > top_limit:
            top_records.pop()

        # Track the rolling contiguous window for the quietest period.
        if not buffer:
            buffer = [record]
        else:
            delta = record.timestamp - buffer[-1].timestamp
            if delta == HALF_HOUR:
                buffer.append(record)
                if len(buffer) > window_size:
                    buffer.pop(0)
            else:
                buffer = [record]

        if len(buffer) == window_size:
            window_total = sum(item.cars for item in buffer)
            if best_window is None or window_total < best_total or (
                window_total == best_total and buffer[0].timestamp < best_window[0].timestamp
            ):
                best_window = tuple(buffer)
                best_total = window_total

    per_day = sorted(daily.items())
    top_sorted = top_records[:top_limit]
    return AnalysisResult(total=total, per_day=per_day, top_half_hours=top_sorted, quietest_window=best_window)


def analyse_file(path: Path, *, window_size: int = 3, top_limit: int = 3) -> AnalysisResult:
    with path.open("r", encoding="utf-8") as handle:
        return analyse_stream(handle, window_size=window_size, top_limit=top_limit)


__all__ = [
    "AnalysisResult",
    "TrafficRecord",
    "analyse_file",
    "analyse_stream",
    "parse_records",
    "quietest_period",
    "read_records",
    "top_half_hours",
    "total_cars",
    "totals_by_day",
]
