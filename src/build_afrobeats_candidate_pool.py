"""Build an unverified Afrobeats discovery pool from Spotify chart records.

Artist credits are used only to discover records for later review. This script
does not classify tracks by genre. Each emitted row is explicitly labeled
"Unverified candidate" and requires track-specific evidence and human review.
"""

import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_DIR / "data" / "spotify_top200_cleaned.csv"
DISCOVERY_FILE = PROJECT_DIR / "data" / "afrobeats_artist_discovery_list.txt"
OUTPUT_FILE = PROJECT_DIR / "data" / "afrobeats_candidate_pool.csv"


def normalize_name(value):
    """Normalize names for exact, punctuation-insensitive matching."""
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def read_discovery_artists(path):
    """Read pipe-separated artist names and aliases from the documentation."""
    artists = set()
    with path.open("r", encoding="utf-8-sig") as source:
        for line in source:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                line = line.partition(":")[2].strip()
            for name in line.split("|"):
                normalized = normalize_name(name.strip())
                if normalized:
                    artists.add(normalized)
    return artists


def split_artist_credits(value):
    """Split the source's pipe-delimited artist credits, with common fallbacks."""
    return [part.strip() for part in re.split(r"\s*[|;]\s*", value or "") if part.strip()]


def normalized_title(value):
    return normalize_name(value)


def track_identity(row):
    """Use the requested Spotify identity and descriptive fields together."""
    return tuple((row.get(field) or "").strip() for field in (
        "track_id", "title", "artists", "release_date"
    ))


def discover_candidates():
    discovery_artists = read_discovery_artists(DISCOVERY_FILE)
    tracks = {}

    with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required = {"track_id", "title", "artists", "release_date", "cc", "week_end"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError("Input dataset is missing required columns: " + ", ".join(sorted(missing)))

        for row in reader:
            credits = split_artist_credits(row.get("artists", ""))
            if not any(normalize_name(artist) in discovery_artists for artist in credits):
                continue

            identity = track_identity(row)
            if identity not in tracks:
                tracks[identity] = {
                    "track_id": identity[0],
                    "title": identity[1],
                    "artists": identity[2],
                    "artist_uris": (row.get("artist_uris") or "").strip(),
                    "release_date": identity[3],
                    "total_chart_observations": 0,
                    "markets": set(),
                    "chart_dates": [],
                }

            candidate = tracks[identity]
            candidate["total_chart_observations"] += 1
            market = (row.get("cc") or "").strip()
            if market:
                candidate["markets"].add(market)
            chart_date = (row.get("week_end") or "").strip()
            if chart_date:
                candidate["chart_dates"].append(chart_date)

    title_ids = defaultdict(set)
    for candidate in tracks.values():
        title_key = normalized_title(candidate["title"])
        if title_key and candidate["track_id"]:
            title_ids[title_key].add(candidate["track_id"])

    candidates = []
    for candidate in tracks.values():
        dates = candidate.pop("chart_dates")
        markets = candidate.pop("markets")
        title_key = normalized_title(candidate["title"])
        multi_id_title = len(title_ids.get(title_key, set())) > 1
        candidates.append({
            **candidate,
            "distinct_markets": len(markets),
            "first_chart_date": min(dates) if dates else "",
            "last_chart_date": max(dates) if dates else "",
            "classification_status": "Unverified candidate",
            "classification_evidence": "",
            "reviewer_notes": "",
            "normalized_title": title_key,
            "multiple_ids_same_normalized_title": "Yes" if multi_id_title else "No",
            "version_review_flag": "Manual version review required" if multi_id_title else "",
        })

    candidates.sort(
        key=lambda row: (row["distinct_markets"], row["total_chart_observations"]),
        reverse=True,
    )
    return candidates


def write_candidates(candidates):
    fieldnames = [
        "track_id",
        "title",
        "artists",
        "artist_uris",
        "release_date",
        "total_chart_observations",
        "distinct_markets",
        "first_chart_date",
        "last_chart_date",
        "classification_status",
        "classification_evidence",
        "reviewer_notes",
        "normalized_title",
        "multiple_ids_same_normalized_title",
        "version_review_flag",
    ]
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidates)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Cleaned Spotify dataset not found: {INPUT_FILE}")
    if not DISCOVERY_FILE.exists():
        raise FileNotFoundError(f"Artist discovery list not found: {DISCOVERY_FILE}")

    candidates = discover_candidates()
    write_candidates(candidates)
    print(f"Unique unverified candidate tracks: {len(candidates):,}")
    print(f"Output: {OUTPUT_FILE}")
    print("First 20 candidates:")
    for candidate in candidates[:20]:
        print(
            f"{candidate['distinct_markets']:>2} markets | "
            f"{candidate['total_chart_observations']:>5,} observations | "
            f"{candidate['track_id']} | {candidate['title']} — {candidate['artists']}"
        )


if __name__ == "__main__":
    main()
