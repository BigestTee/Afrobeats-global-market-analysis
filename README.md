# Music Industry Analytics Dashboard

A GenData capstone project exploring this research question:

> **What factors influence the popularity of songs, and how do these patterns differ across music genres and over time?**

## Dataset

The project uses Spotify chart dataset files downloaded from [Zenodo](https://zenodo.org/). The inspected chart-week coverage is **2024-01-04 to 2026-10-15**, with **324,800 chart records** across the 2024, 2025, and 2026 files. A file-by-file inspection, including sizes, fields, date ranges, row counts, and first five rows, is available in [`data/data_inspection.txt`](data/data_inspection.txt).

The available fields are:

`cc`, `week_end`, `rank`, `prev_rank`, `peak`, `appearances`, `streams`, `entry_status`, `track_id`, `title`, `artists`, `artist_uris`, and `release_date`.

**Current limitation:** The chart data has no genre column. Afrobeats classification therefore needs a documented, reproducible method before genre-based comparisons are made. The method should record its genre definition, classification sources, handling of collaborations and multiple genres, and review decisions.

## Current progress

- Built a beginner-friendly Streamlit dashboard prototype with KPI cards, top-song and genre charts, a danceability scatter plot, release trend, and sidebar filters.
- The prototype currently uses clearly labeled illustrative demo data; it is not populated with the Zenodo chart data.
- Inspected the three yearly compressed CSV files directly without extracting them or loading each entire file into memory.
- Kept the inspection report in `data/`. No raw chart archives or duplicate 2026 archive are included in the project files.

## Next steps

1. Document and apply a consistent Afrobeats classification method, including sources and any manual decisions.
2. Clean and validate the chart records, including country and chart-week handling.
3. Decide how to measure popularity for the research question (for example, rank, streams, or a clearly defined combination).
4. Replace the dashboard demo dataset with a reproducible analysis dataset and update the charts to match the research scope.
5. Compare patterns across time and the classified genre groups, then document limitations and findings.

## Run the prototype locally

1. Install dependencies: `python -m pip install -r requirements.txt`
2. Start Streamlit: `streamlit run app.py`
3. Open the local address printed by Streamlit.

The current dashboard remains a visual prototype with demo records until the data preparation and classification steps are complete.
