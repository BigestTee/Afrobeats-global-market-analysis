
"""Find candidate tracks in the cleaned Spotify chart dataset."""

import csv
import re
from difflib import SequenceMatcher
from pathlib import Path


# Find the project folder from this script's location.
PROJECT_FOLDER = Path(__file__).resolve().parent.parent

# Set the input dataset and output report paths.
INPUT_FILE = PROJECT_FOLDER / "data" / "spotify_top200_cleaned.csv"
OUTPUT_FILE = PROJECT_FOLDER / "data" / "afrobeats_candidate_matches.csv"

# These are search candidates only. The script does not assign genres.
CANDIDATES = [
    ("Calm Down", "Rema"),
    ("Last Last", "Burna Boy"),
    ("Ojuelegba", "Wizkid"),
    ("Buga", "Kizz Daniel, Tekno"),
    ("Commas", "Ayra Starr"),
    ("Love Me JeJe", "Tems"),
    ("Dealer", "Ayo Maff, Fireboy DML"),
    ("Egwu", "Chike, Mohbad"),
    ("OZEBA", "Rema"),
    ("Water", "Tyla"),
]

# A possible match needs a strong title similarity and at least one matching
# candidate artist name in the Spotify artist credits.
POSSIBLE_TITLE_SIMILARITY = 0.88

# These words indicate a version difference. Such a row cannot be exact when
# the candidate does not explicitly request that version.
VERSION_MARKERS = {
    "acoustic",
    "demo",
    "edit",
    "extended",
    "instrumental",
    "live",
    "mix",
    "remaster",
    "remastered",
    "remix",
    "spedup",
    "slowed",
    "version",
}


def normalize_text(text):
    """Lowercase text and remove punctuation, spaces, and other symbols."""
    return re.sub(r"[^a-z0-9]", "", (text or "").casefold())


def split_artist_names(artist_text):
    """Split credited or candidate artists at common list separators."""
    names = re.split(r"[,;|/&]+", artist_text or "")
    return [name.strip() for name in names if name.strip()]


def candidate_artists_in_credits(candidate_artist_text, spotify_artist_text):
    """Return candidate artist names found among Spotify artist credits.

    Names are compared in normalized form, without depending on artist order.
    """
    candidate_names = [
        normalize_text(name)
        for name in split_artist_names(candidate_artist_text)
    ]
    credited_names = {
        normalize_text(name)
        for name in split_artist_names(spotify_artist_text)
    }

    # Ignore empty normalized names and return the matched candidate names.
    return [
        name
        for name in candidate_names
        if name and name in credited_names
    ]


def find_version_markers(title):
    """Find common version words in a track title."""
    normalized_title = normalize_text(title)
    return sorted(
        marker
        for marker in VERSION_MARKERS
        if marker in normalized_title
    )


def load_unique_tracks():
    """Read the chart CSV and keep one source row per nonblank track_id."""
    tracks_by_id = {}

    with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as input_file:
        reader = csv.DictReader(input_file)

        for row in reader:
            track_id = (row.get("track_id") or "").strip()

            # Rows without a track ID cannot be reliably deduplicated.
            if not track_id:
                continue

            # Chart tracks repeat across markets and weeks. Keep the first
            # source row's title, artist credits, and release date.
            if track_id not in tracks_by_id:
                tracks_by_id[track_id] = {
                    "track_id": track_id,
                    "title": row.get("title") or "",
                    "artists": row.get("artists") or "",
                    "release_date": row.get("release_date") or "",
                }

    return list(tracks_by_id.values())


def find_candidate_matches(candidate_title, candidate_artist, tracks):
    """Return exact and possible matches for one candidate."""
    normalized_candidate_title = normalize_text(candidate_title)
    candidate_artist_names = split_artist_names(candidate_artist)
    candidate_has_version = bool(find_version_markers(candidate_title))
    matches = []

    for track in tracks:
        normalized_spotify_title = normalize_text(track["title"])
        matched_artists = candidate_artists_in_credits(
            candidate_artist, track["artists"]
        )

        title_is_exact = normalized_candidate_title == normalized_spotify_title
        every_candidate_artist_matched = (
            len(matched_artists) == len(candidate_artist_names)
        )
        spotify_version_markers = find_version_markers(track["title"])

        # A title and artist match is exact only when all candidate artists
        # are credited. Extra credited artists and different artist order are
        # allowed. A detected alternate version blocks exact status unless
        # the candidate itself explicitly specifies a version.
        if (
            title_is_exact
            and every_candidate_artist_matched
            and (candidate_has_version or not spotify_version_markers)
        ):
            matches.append({
                "track": track,
                "status": "exact",
                "notes": (
                    "Normalized title matches and every candidate artist is "
                    "present in Spotify artist credits; artist order and extra "
                    "credited artists are allowed."
                ),
                "version_review": (
                    "Candidate specifies a version."
                    if candidate_has_version
                    else "No version difference detected."
                ),
            })
            continue

        # Possible matches require a strong title match and at least one
        # candidate artist in the Spotify credits. Keep these separate from
        # exact matches and explain which condition needs review.
        title_similarity = SequenceMatcher(
            None, normalized_candidate_title, normalized_spotify_title
        ).ratio()

        if title_similarity >= POSSIBLE_TITLE_SIMILARITY and matched_artists:
            reasons = [
                f"title similarity is {title_similarity:.2f}, not an exact "
                "normalized title match"
                if not title_is_exact
                else "title matches but not every candidate artist is credited"
            ]

            if len(matched_artists) < len(candidate_artist_names):
                reasons.append(
                    f"{len(matched_artists)} of {len(candidate_artist_names)} "
                    "candidate artist names matched"
                )

            if spotify_version_markers and not candidate_has_version:
                reasons.append(
                    "Spotify title contains possible version marker(s): "
                    + ", ".join(spotify_version_markers)
                )
                version_review = (
                    "Review possible alternate version: "
                    + ", ".join(spotify_version_markers)
                )
            elif candidate_has_version:
                version_review = (
                    "Candidate title includes a version marker; verify it "
                    "matches the Spotify version."
                )
            else:
                version_review = "No common version marker detected."

            matches.append({
                "track": track,
                "status": "possible",
                "notes": "Possible match flagged for manual review: "
                + "; ".join(reasons)
                + ".",
                "version_review": version_review,
            })

    return matches


def main():
    """Search candidates, save the report, and print match counts."""
    tracks = load_unique_tracks()
    results = []
    exact_count = 0
    possible_count = 0
    no_match_count = 0

    for candidate_title, candidate_artist in CANDIDATES:
        matches = find_candidate_matches(
            candidate_title, candidate_artist, tracks
        )

        if not matches:
            no_match_count += 1
            results.append({
                "candidate_title": candidate_title,
                "candidate_artist": candidate_artist,
                "candidate_version": "",
                "match_status": "no match",
                "matching_notes": (
                    "No exact match or possible match meeting the title and "
                    "artist criteria was found."
                ),
                "version_review": "",
                "track_id": "",
                "spotify_title": "",
                "spotify_artists": "",
                "release_date": "",
            })
            continue

        # Count each candidate once, by its strongest match status. The report
        # still includes every exact or possible track match found.
        statuses = {match["status"] for match in matches}
        if "exact" in statuses:
            exact_count += 1
        else:
            possible_count += 1

        for match in matches:
            track = match["track"]
            results.append({
                "candidate_title": candidate_title,
                "candidate_artist": candidate_artist,
                "candidate_version": (
                    "Specified in candidate title."
                    if find_version_markers(candidate_title)
                    else "No specific version specified."
                ),
                "match_status": match["status"],
                "matching_notes": match["notes"],
                "version_review": match["version_review"],
                "track_id": track["track_id"],
                "spotify_title": track["title"],
                "spotify_artists": track["artists"],
                "release_date": track["release_date"],
            })

    # Write candidate details, match notes, version review, and original
    # Spotify metadata. No genre classification field is included.
    fieldnames = [
        "candidate_title",
        "candidate_artist",
        "candidate_version",
        "match_status",
        "matching_notes",
        "version_review",
        "track_id",
        "spotify_title",
        "spotify_artists",
        "release_date",
    ]
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Report candidate counts and the output location.
    print(f"Exact matches: {exact_count}")
    print(f"Possible matches: {possible_count}")
    print(f"No matches: {no_match_count}")
    print(f"Output file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
