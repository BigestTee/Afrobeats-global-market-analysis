"""Combine the three canonical Spotify Top 200 archives into one CSV file."""

import csv
import gzip
import sys
from datetime import date
from pathlib import Path


# Find the project folder from this script's location, so the script works
# even when it is started from a different current folder.
PROJECT_FOLDER = Path(__file__).resolve().parent.parent
DOWNLOADS_FOLDER = Path.home() / "Downloads"
OUTPUT_FILE = PROJECT_FOLDER / "data" / "spotify_top200_cleaned.csv"

# Listing each input by its full, exact filename excludes the duplicate 2026
# archive whose filename ends in " (1).csv.gz".
SOURCE_ARCHIVES = [
    DOWNLOADS_FOLDER / "spotify_top200_positions_2024.csv.gz",
    DOWNLOADS_FOLDER / "spotify_top200_positions_2025.csv.gz",
    DOWNLOADS_FOLDER / "spotify_top200_positions_2026.csv.gz",
]

# These are the 13 original columns, in their original order.
EXPECTED_COLUMNS = [
    "cc",
    "week_end",
    "rank",
    "prev_rank",
    "peak",
    "appearances",
    "streams",
    "entry_status",
    "track_id",
    "title",
    "artists",
    "artist_uris",
    "release_date",
]

EXPECTED_ROW_COUNT = 324_800
EXPECTED_EARLIEST_DATE = "2024-01-04"
EXPECTED_LATEST_DATE = "2026-10-15"


def main():
    """Write the combined CSV and check its row count and chart date range."""
    # Stop with a clear message if an expected canonical archive is missing.
    missing_archives = [path for path in SOURCE_ARCHIVES if not path.is_file()]
    if missing_archives:
        print("ERROR: Could not find these required source archive(s):")
        for path in missing_archives:
            print(f"  {path}")
        return 1

    # Make sure the destination folder exists before opening the output file.
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    row_count = 0
    earliest_date = None
    latest_date = None

    try:
        # newline="" is recommended by Python's CSV module for reliable CSV
        # line handling on Windows as well as other operating systems.
        with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(EXPECTED_COLUMNS)

            # Read each compressed archive directly, without extracting or
            # changing the original files.
            for archive_path in SOURCE_ARCHIVES:
                with gzip.open(
                    archive_path, "rt", encoding="utf-8-sig", newline=""
                ) as archive:
                    reader = csv.reader(archive)
                    header = next(reader, None)
                    if header != EXPECTED_COLUMNS:
                        raise ValueError(
                            f"Unexpected columns in {archive_path.name}: {header}"
                        )

                    for row in reader:
                        # Copy the source row as read. Blank CSV fields stay
                        # blank, and values such as prev_rank=-1 stay unchanged.
                        if len(row) != len(EXPECTED_COLUMNS):
                            raise ValueError(
                                f"A row in {archive_path.name} has "
                                f"{len(row)} fields; expected {len(EXPECTED_COLUMNS)}."
                            )
                        writer.writerow(row)
                        row_count += 1

                        # Track the chart date range for the verification below.
                        chart_date = date.fromisoformat(row[1])
                        if earliest_date is None or chart_date < earliest_date:
                            earliest_date = chart_date
                        if latest_date is None or chart_date > latest_date:
                            latest_date = chart_date

    except (OSError, EOFError, csv.Error, UnicodeError, ValueError) as error:
        print(f"ERROR while creating the cleaned dataset: {error}")
        return 1

    earliest_text = earliest_date.isoformat() if earliest_date else "None"
    latest_text = latest_date.isoformat() if latest_date else "None"

    # Re-open the completed CSV to verify the saved file, rather than relying
    # only on the counters collected while reading the archives.
    try:
        verified_row_count = 0
        verified_earliest = None
        verified_latest = None
        with OUTPUT_FILE.open("r", encoding="utf-8", newline="") as output:
            reader = csv.reader(output)
            output_header = next(reader, None)
            if output_header != EXPECTED_COLUMNS:
                raise ValueError("The output file does not have the expected header.")

            for row in reader:
                if len(row) != len(EXPECTED_COLUMNS):
                    raise ValueError("The output file contains a malformed row.")
                verified_row_count += 1
                chart_date = date.fromisoformat(row[1])
                if verified_earliest is None or chart_date < verified_earliest:
                    verified_earliest = chart_date
                if verified_latest is None or chart_date > verified_latest:
                    verified_latest = chart_date
    except (OSError, csv.Error, UnicodeError, ValueError) as error:
        print(f"ERROR while verifying the cleaned dataset: {error}")
        return 1

    verified_earliest_text = verified_earliest.isoformat() if verified_earliest else "None"
    verified_latest_text = verified_latest.isoformat() if verified_latest else "None"
    rows_ok = verified_row_count == EXPECTED_ROW_COUNT
    dates_ok = (
        verified_earliest_text == EXPECTED_EARLIEST_DATE
        and verified_latest_text == EXPECTED_LATEST_DATE
    )

    print("Source archives used:")
    for archive_path in SOURCE_ARCHIVES:
        print(f"  {archive_path}")
    print(f"Output file: {OUTPUT_FILE}")
    print(
        f"Output rows: {verified_row_count:,} / {EXPECTED_ROW_COUNT:,} expected "
        f"({'PASS' if rows_ok else 'FAIL'})"
    )
    print(
        f"week_end date range: {verified_earliest_text} to {verified_latest_text} "
        f"({'PASS' if dates_ok else 'FAIL'})"
    )

    if not rows_ok or not dates_ok or row_count != verified_row_count:
        print("Overall result: FAIL")
        return 1

    print("Overall result: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
