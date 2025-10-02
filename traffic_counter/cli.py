from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence

from .core import (
    TrafficRecord,
    quietest_period,
    read_records,
    top_half_hours,
    total_cars,
    totals_by_day,
)


def format_record(record: TrafficRecord) -> str:
    return f"{record.timestamp.isoformat()} {record.cars}"


def print_section(title: str, lines: Iterable[str]) -> None:
    print(title)
    for line in lines:
        print(line)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyse automated traffic counts.")
    parser.add_argument("data_file", type=Path, help="Path to the traffic data file.")
    args = parser.parse_args(argv)

    try:
        records = read_records(args.data_file)
    except FileNotFoundError:
        parser.error(f"File not found: {args.data_file}")

    total = total_cars(records)
    print(f"Total: {total}")

    daily_lines = (f"{day} {count}" for day, count in totals_by_day(records))
    print_section("Cars per day:", daily_lines)

    top_lines = (format_record(record) for record in top_half_hours(records, limit=3))
    print_section("Top 3 half hours:", top_lines)

    try:
        quiet_window = quietest_period(records, size=3)
    except ValueError:
        print("Least busy 1.5h period:")
        print("<not available>")
    else:
        window_lines = [
            f"Start: {quiet_window[0].timestamp.isoformat()}",
            f"Total: {sum(record.cars for record in quiet_window)}",
        ] + [format_record(record) for record in quiet_window]
        print_section("Least busy 1.5h period:", window_lines)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
