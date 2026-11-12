"""Inspect the 2024–2026 Spotify Top 200 chart archives in Downloads."""

import csv
import gzip
import sys
from datetime import date
from pathlib import Path


# Build the path to the current Windows user's Downloads folder.
DOWNLOADS_FOLDER = Path.home() / "Downloads"
YEARS = (2024, 2025, 2026)
REQUIRED_COLUMNS = {"week_end", "cc", "track_id"}


def inspect_file(file_path):
    """Read one compressed CSV row by row and summarize its chart records."""
    row_count = 0
    earliest_date = None
    latest_date = None
    markets = set()
    tracks = set()

    # gzip.open reads the compressed CSV directly; nothing is extracted.
    # DictReader uses the CSV header to access fields by their column names.
    with gzip.open(file_path, "rt", encoding="utf-8-sig", newline="") as compressed_file:
        reader = csv.DictReader(compressed_file)
        columns = reader.fieldnames

        if columns is None:
            raise ValueError(f"The file has no CSV header: {file_path.name}")

        missing_columns = REQUIRED_COLUMNS.difference(columns)
        if missing_columns:
            missing_list = ", ".join(sorted(missing_columns))
            raise ValueError(f"Missing required column(s) in {file_path.name}: {missing_list}")

        for row in reader:
            # Count each CSV data row and collect its date, market, and track ID.
            row_count += 1

            week_end_text = (row.get("week_end") or "").strip()
            try:
                week_end = date.fromisoformat(week_end_text)
            except ValueError as error:
                raise ValueError(
                    f"Invalid week_end value {week_end_text!r} in {file_path.name} "
                    f"near CSV line {reader.line_num}"
                ) from error

            if earliest_date is None or week_end < earliest_date:
                earliest_date = week_end
            if latest_date is None or week_end > latest_date:
                latest_date = week_end

            # Sets keep each distinct market and track only once per file.
            market = (row.get("cc") or "").strip()
            track_id = (row.get("track_id") or "").strip()
            if market:
                markets.add(market)
            if track_id:
                tracks.add(track_id)

    return {
        "columns": columns,
        "rows": row_count,
        "earliest": earliest_date,
        "latest": latest_date,
        "markets": markets,
        "tracks": tracks,
        "size_bytes": file_path.stat().st_size,
    }


def main():
    """Check the yearly files, print their summaries, and combine totals."""
    if not DOWNLOADS_FOLDER.is_dir():
        print(f"ERROR: Downloads folder not found: {DOWNLOADS_FOLDER}")
        return 1

    # Use the exact yearly filenames. This selects one 2026 archive and ignores
    # a second copy with a suffix such as " (1)".
    yearly_files = {
        year: DOWNLOADS_FOLDER / f"spotify_top200_positions_{year}.csv.gz"
        for year in YEARS
    }

    missing_files = [path for path in yearly_files.values() if not path.is_file()]
    if missing_files:
        print("ERROR: These expected files were not found:")
        for path in missing_files:
            print(f"  {path}")
        return 1

    combined_rows = 0
    combined_earliest = None
    combined_latest = None
    combined_markets = set()
    combined_tracks = set()
    combined_columns = None

    for year, file_path in yearly_files.items():
        result = inspect_file(file_path)
        combined_columns = combined_columns or result["columns"]
        combined_rows += result["rows"]
        combined_markets.update(result["markets"])
        combined_tracks.update(result["tracks"])

        if result["earliest"] is not None:
            if combined_earliest is None or result["earliest"] < combined_earliest:
                combined_earliest = result["earliest"]
            if combined_latest is None or result["latest"] > combined_latest:
                combined_latest = result["latest"]

        size_mib = result["size_bytes"] / (1024 * 1024)
        print(f"\n{year} FILE: {file_path.name}")
        print(f"Size: {result['size_bytes']:,} bytes ({size_mib:.2f} MiB)")
        print(f"Rows: {result['rows']:,}")
        print(f"Columns: {', '.join(result['columns'])}")
        print(f"week_end range: {result['earliest']} to {result['latest']}")
        print(f"Unique markets (cc): {len(result['markets']):,}")
        print(f"Unique tracks (track_id): {len(result['tracks']):,}")

    print("\nCOMBINED TOTALS (2024–2026; one file per year)")
    print(f"Rows: {combined_rows:,}")
    print(f"Columns: {', '.join(combined_columns or [])}")
    print(f"week_end range: {combined_earliest} to {combined_latest}")
    print(f"Unique markets (cc): {len(combined_markets):,}")
    print(f"Unique tracks (track_id): {len(combined_tracks):,}")
    print("Duplicate 2026 copy with a filename suffix was not included.")
    return 0


# Run main() when this file is launched as a script.
if __name__ == "__main__":
    sys.exit(main())