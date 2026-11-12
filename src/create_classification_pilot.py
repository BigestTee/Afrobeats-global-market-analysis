"""Create a reproducible, unclassified track sample for the Afrobeats pilot."""

import csv
import random
from pathlib import Path


# Find the project folder from this script's location.
PROJECT_FOLDER = Path(__file__).resolve().parent.parent

# Define the input and output CSV paths.
INPUT_FILE = PROJECT_FOLDER / "data" / "spotify_top200_cleaned.csv"
OUTPUT_FILE = PROJECT_FOLDER / "data" / "afrobeats_classification_pilot.csv"

# A fixed seed makes the selected pilot tracks reproducible.
RANDOM_SEED = 42
PILOT_SIZE = 20


def main():
    """Read unique tracks, select a pilot sample, and save it."""
    tracks_by_id = {}

    # Read the cleaned chart file and keep the first title and artist values
    # encountered for each nonblank track_id.
    with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as input_file:
        reader = csv.DictReader(input_file)

        for row in reader:
            track_id = (row.get("track_id") or "").strip()

            # Rows without a track_id cannot be uniquely identified as tracks.
            if not track_id:
                continue

            # Keeping the first occurrence avoids repeating tracks that appear
            # in multiple markets or chart weeks.
            if track_id not in tracks_by_id:
                tracks_by_id[track_id] = {
                    "track_id": track_id,
                    "title": row.get("title") or "",
                    "artists": row.get("artists") or "",
                    "classification": "",
                }

    # Convert the unique track records to a list and choose up to 20.
    unique_tracks = list(tracks_by_id.values())
    selected_count = min(PILOT_SIZE, len(unique_tracks))
    pilot_tracks = random.Random(RANDOM_SEED).sample(
        unique_tracks, selected_count
    )

    # Write only the requested columns. Classification stays blank for every
    # track; no genre is inferred or assigned.
    fieldnames = ["track_id", "title", "artists", "classification"]
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(pilot_tracks)

    # Report the unique-track count, selected count, and output location.
    print(f"Unique tracks found: {len(unique_tracks):,}")
    print(f"Tracks selected: {selected_count}")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
