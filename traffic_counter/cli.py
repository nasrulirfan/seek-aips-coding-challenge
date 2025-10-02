from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Sequence

from .core import AnalysisResult, TrafficRecord, analyse_file


def format_record(record: TrafficRecord) -> str:
    return f"{record.timestamp.isoformat()} {record.cars}"


def print_section(title: str, lines: Iterable[str]) -> None:
    print(title)
    for line in lines:
        print(line)


def print_result(result: AnalysisResult) -> None:
    print(f"Total: {result.total}")

    daily_lines = (f"{day} {count}" for day, count in result.per_day)
    print_section("Cars per day:", daily_lines)

    top_lines = (format_record(record) for record in result.top_half_hours)
    print_section("Top 3 half hours:", top_lines)

    if result.quietest_window is None:
        # Not enough contiguous readings to form a 1.5-hour window.
        print("Least busy 1.5h period:")
        print("<not available>")
    else:
        window = result.quietest_window
        # Print summary and then the contributing half-hour slots.
        window_lines = [
            f"Start: {window[0].timestamp.isoformat()}",
            f"Total: {sum(record.cars for record in window)}",
        ] + [format_record(record) for record in window]
        print_section("Least busy 1.5h period:", window_lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyse automated traffic counts.")
    parser.add_argument("data_file", type=Path, help="Path to the traffic data file.")
    args = parser.parse_args(argv)

    try:
        result = analyse_file(args.data_file)
    except FileNotFoundError:
        parser.error(f"File not found: {args.data_file}")

    print_result(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
