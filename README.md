# Traffic Counter Analysis

This project analyses automated half-hour traffic counts and reports the key metrics required in the AIPS coding challenge.

## Features
- Parses ISO-8601 timestamps and counts from machine-generated files.
- Aggregates total cars and per-day totals.
- Ranks the top three half-hour periods, breaking ties by earliest timestamp.
- Finds the quietest contiguous 1.5-hour period (three half-hour slots) while ignoring gaps in the data.
- Provides a small CLI as well as unit tests covering the core logic and command behaviour.

## Project Layout
```
traffic_counter/
  core.py       # Parsing and analytics
  cli.py        # Command-line interface wiring
  __main__.py   # Enables `python -m traffic_counter`
tests/
  test_core.py  # Core logic unit tests
  test_cli.py   # CLI integration tests
data/
  example_traffic.txt  # Sample dataset with edge cases
```

## Usage
1. Activate your Python environment (Python 3.9+ recommended).
2. Run the CLI against a data file:
   ```bash
   python -m traffic_counter data/example_traffic.txt
   ```
   Replace the path with your own dataset as needed.

The CLI prints:
- `Total:` total cars across the file.
- `Cars per day:` the aggregated counts for each date.
- `Top 3 half hours:` the busiest half-hour windows.
- `Least busy 1.5h period:` the contiguous three-slot window with the fewest cars, showing the start time, total cars, and component records. If there is no qualifying window it reports `<not available>`.

## Example Dataset
`data/example_traffic.txt` covers representative cases:
- Normal consecutive readings with zero counts.
- Overnight transitions and day changes.
- High-traffic ties to demonstrate stable ordering.
- A quiet window composed of zero readings to validate the least-busy search.

## Testing
Run the automated test suite with:
```bash
python -m pytest
```
The tests cover core aggregation logic, contiguous window handling, error conditions, and CLI output formatting.

## Implementation Notes
- Records are parsed into `TrafficRecord` dataclasses and sorted chronologically.
- Contiguous windows require exact 30-minute gaps to ensure the least-busy calculation ignores broken sequences.
- Functions are pure where practical, making the code easier to test; the CLI composes these functions to produce the final report.
