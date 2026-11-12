"""Create a manually reviewable shortlist from unverified track candidates.

Artist credit order and title feature wording are discovery signals only.
Neither signal verifies a track's genre or its billing status. This utility
preserves candidate records and never assigns an Afrobeats classification.
"""

import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_DIR / "data" / "afrobeats_candidate_pool.csv"
DISCOVERY_FILE = PROJECT_DIR / "data" / "afrobeats_artist_discovery_list.txt"
OUTPUT_FILE = PROJECT_DIR / "data" / "afrobeats_screening_shortlist.csv"
README_FILE = PROJECT_DIR / "data" / "afrobeats_screening_shortlist_README.md"
SHORTLIST_LIMIT = 250
FEATURE_MARKER = re.compile(r"\b(?:feat(?:uring)?\.?|ft\.?|with)\b", re.IGNORECASE)
ARTIST_SEPARATOR = re.compile(r"\s*[|;]\s*")
COVERAGE_TIERS = ("Higher chart coverage", "Moderate chart coverage", "Lower chart coverage")


def normalize_name(value):
    """Normalize names for exact, punctuation-insensitive matching."""
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def load_discovery_artists(path):
    """Return canonical discovery names and their normalized aliases."""
    artists = {}
    with path.open("r", encoding="utf-8-sig") as source:
        for raw_line in source:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                line = line.partition(":")[2].strip()
            names = [name.strip() for name in line.split("|") if name.strip()]
            if not names:
                continue
            canonical_key = normalize_name(names[0])
            if not canonical_key:
                continue
            entry = artists.setdefault(canonical_key, {"name": names[0], "aliases": set()})
            entry["aliases"].update(normalize_name(name) for name in names if normalize_name(name))
    return list(artists.values())


def artist_credits(value):
    return [name.strip() for name in ARTIST_SEPARATOR.split(value or "") if name.strip()]


def matching_positions(credits, discovery_artists):
    """Return credited-artist positions matching any discovery name or alias."""
    positions = []
    for index, credit in enumerate(credits):
        normalized_credit = normalize_name(credit)
        if normalized_credit and any(normalized_credit in artist["aliases"] for artist in discovery_artists):
            positions.append(index)
    return positions


def parse_count(value):
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def priority_group(row, discovery_artists):
    credits = artist_credits(row.get("artists", ""))
    positions = matching_positions(credits, discovery_artists)
    title_has_feature_marker = bool(FEATURE_MARKER.search(row.get("title", "")))

    # Credit order is only a screening proxy. A second-position credit is not
    # assumed to be a co-lead, and explicit title markers increase billing
    # review priority rather than establish a role.
    if positions and min(positions) == 0:
        return (1 if title_has_feature_marker else 0), positions, title_has_feature_marker
    if positions and min(positions) == 1:
        return (3 if title_has_feature_marker else 2), positions, title_has_feature_marker
    if positions and title_has_feature_marker:
        return 4, positions, title_has_feature_marker
    if positions:
        return 5, positions, title_has_feature_marker
    return 6, positions, title_has_feature_marker


def assign_coverage_tiers(rows):
    """Split records into three chart-coverage bands for stratified screening."""
    ordered = sorted(
        rows,
        key=lambda row: (
            parse_count(row.get("distinct_markets")),
            parse_count(row.get("total_chart_observations")),
            row.get("track_id", ""),
        ),
        reverse=True,
    )
    tier_by_row = {}
    band_size = max(1, (len(ordered) + 2) // 3)
    for index, row in enumerate(ordered):
        band_index = min(index // band_size, 2)
        tier_by_row[id(row)] = COVERAGE_TIERS[band_index]
    return tier_by_row


def screening_reason(group, positions, has_marker, tier):
    if group == 0:
        signal = "First-credit discovery signal; no title feature marker; verify billing manually"
    elif group == 1:
        signal = "First-credit discovery signal with title feature marker; verify billing manually"
    elif group == 2:
        signal = "Second-credit discovery signal; possible co-lead or collaborator; verify billing manually"
    elif group == 3:
        signal = "Second-credit discovery signal with title feature marker; verify billing manually"
    elif group == 4:
        signal = "Feature-collaboration discovery signal: title feature marker and artist appears after first two credits"
    elif group == 5:
        signal = "Later-credit discovery signal: artist appears after first two credits"
    else:
        signal = "Candidate retained for review; no current discovery-list credit match"
    return f"{signal}. Coverage stratum: {tier}. Signals guide screening only; they do not verify genre."


def select_shortlist(rows, discovery_artists, limit=SHORTLIST_LIMIT):
    """Prioritize likely lead/co-lead signals while sampling all coverage bands."""
    coverage_tier_by_row = assign_coverage_tiers(rows)
    groups = defaultdict(lambda: defaultdict(list))

    for row in rows:
        group, positions, has_marker = priority_group(row, discovery_artists)
        tier = coverage_tier_by_row[id(row)]
        row["_screen_group"] = group
        row["_matched_positions"] = positions
        row["_has_feature_marker"] = has_marker
        row["_coverage_tier"] = tier
        groups[group][tier].append(row)

    for tier_rows in groups.values():
        for tier in COVERAGE_TIERS:
            tier_rows[tier].sort(
                key=lambda row: (
                    parse_count(row.get("distinct_markets")),
                    parse_count(row.get("total_chart_observations")),
                    row.get("track_id", ""),
                ),
                reverse=True,
            )

    selected = []
    for group in sorted(groups):
        tier_rows = groups[group]
        indexes = {tier: 0 for tier in COVERAGE_TIERS}
        # Rotate through higher, moderate, and lower coverage so that coverage
        # helps prioritize, but does not become a popularity-only cutoff.
        while len(selected) < limit:
            found_any = False
            for tier in COVERAGE_TIERS:
                index = indexes[tier]
                if index < len(tier_rows[tier]):
                    row = tier_rows[tier][index]
                    indexes[tier] += 1
                    row["screening_priority"] = screening_reason(
                        row["_screen_group"],
                        row["_matched_positions"],
                        row["_has_feature_marker"],
                        row["_coverage_tier"],
                    )
                    selected.append(row)
                    found_any = True
                    if len(selected) >= limit:
                        break
            if not found_any:
                break

    return selected


def main():
    for required_path in (INPUT_FILE, DISCOVERY_FILE):
        if not required_path.exists():
            raise FileNotFoundError(f"Required input not found: {required_path}")

    discovery_artists = load_discovery_artists(DISCOVERY_FILE)
    with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError("Candidate pool has no CSV header.")
        original_fields = list(reader.fieldnames)
        rows = list(reader)

    selected = select_shortlist(rows, discovery_artists)
    review_fields = [
        "lead_artist_review",
        "genre_evidence_url",
        "genre_evidence_quote",
        "classification",
        "reviewer_notes",
        "screening_priority",
    ]
    output_fields = original_fields + [field for field in review_fields if field not in original_fields]

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=output_fields)
        writer.writeheader()
        for row in selected:
            output_row = {field: row.get(field, "") for field in original_fields}
            output_row.update({
                "lead_artist_review": "",
                "genre_evidence_url": "",
                "genre_evidence_quote": "",
                "classification": "Uncertain/Unclassified",
                "reviewer_notes": "",
                "screening_priority": row["screening_priority"],
            })
            writer.writerow(output_row)

    README_FILE.write_text(
        "# Afrobeats screening shortlist\n\n"
        "`afrobeats_screening_shortlist.csv` is a manually reviewable screening "
        "shortlist drawn from `afrobeats_candidate_pool.csv`. It is not a verified "
        "Afrobeats dataset, a complete catalogue, or a set of genre findings.\n\n"
        "The shortlist prioritizes candidate records whose credited artists match "
        "the discovery list in the first or second credit position. Artist credit "
        "order and title markers such as `feat.` or `with` are discovery signals "
        "only. They do not establish billing roles or verify a track's genre. "
        "Coverage bands are sampled within priority groups so lower-coverage "
        "candidates can remain available for screening.\n\n"
        "Each Spotify track ID remains a separate record. Review fields are left "
        "blank except `classification`, initialized as `Uncertain/Unclassified`. "
        "Apply the project classification codebook and record track-specific "
        "evidence before changing a classification.\n",
        encoding="utf-8",
    )

    print(f"Shortlisted tracks: {len(selected):,}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"README note: {README_FILE}")
    print("First 20 shortlisted records:")
    for row in selected[:20]:
        print(
            f"{row.get('track_id', '')} | {row.get('title', '')} | "
            f"{row.get('artists', '')} | markets={row.get('distinct_markets', '')} | "
            f"observations={row.get('total_chart_observations', '')} | "
            f"{row['screening_priority']}"
        )


if __name__ == "__main__":
    main()
