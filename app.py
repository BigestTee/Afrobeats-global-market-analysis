"""Research dashboard for international Spotify chart performance."""

from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = PROJECT_DIR / "data" / "spotify_top200_cleaned.csv"
REVIEW_FILE = PROJECT_DIR / "data" / "afrobeats_first20_review.csv"
NAV_ITEMS = [
    "Overview",
    "Global Market Performance",
    "Country Comparison",
    "Track & Artist Performance",
    "Afrobeats Artists & Tracks",
    "Growth Opportunities",
    "Data & Methodology",
]
NAVY = "#080D1C"
PANEL = "#121A2E"
ACCENT_PURPLE = "#9B8AFB"
ACCENT_BLUE = "#45B8FF"
ACCENT_TURQUOISE = "#35D6C2"
TEXT = "#F3F6FC"
MUTED = "#A7B3C8"

# Common market codes in the Spotify chart files. Unmapped codes remain in
# metrics and tables; only mapped codes can be placed on the country map.
COUNTRY_NAMES = {
    "ar": "Argentina", "at": "Austria", "au": "Australia", "be": "Belgium",
    "bo": "Bolivia", "br": "Brazil", "ca": "Canada", "ch": "Switzerland",
    "cl": "Chile", "co": "Colombia", "cr": "Costa Rica", "cz": "Czechia",
    "de": "Germany", "dk": "Denmark", "do": "Dominican Republic", "ec": "Ecuador",
    "ee": "Estonia", "es": "Spain", "fi": "Finland", "fr": "France",
    "gb": "United Kingdom", "gr": "Greece", "gt": "Guatemala", "hk": "Hong Kong",
    "hn": "Honduras", "hu": "Hungary", "id": "Indonesia", "ie": "Ireland",
    "il": "Israel", "in": "India", "is": "Iceland", "it": "Italy",
    "jp": "Japan", "kr": "South Korea", "lt": "Lithuania", "lu": "Luxembourg",
    "lv": "Latvia", "mx": "Mexico", "my": "Malaysia", "ng": "Nigeria", "nl": "Netherlands",
    "no": "Norway", "nz": "New Zealand", "pa": "Panama", "pe": "Peru",
    "ph": "Philippines", "pl": "Poland", "pt": "Portugal", "py": "Paraguay",
    "ro": "Romania", "se": "Sweden", "sg": "Singapore", "sk": "Slovakia",
    "th": "Thailand", "tr": "Turkey", "tw": "Taiwan", "ua": "Ukraine",
    "us": "United States", "uy": "Uruguay", "vn": "Vietnam", "za": "South Africa",
}


st.set_page_config(
    page_title="Global Afrobeats Market Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_theme():
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: dark; }}
        .stApp {{ background: radial-gradient(ellipse at 78% 0%, #171638 0%, {NAVY} 46%); color: {TEXT}; }}
        [data-testid="stHeader"] {{ background: rgba(8,13,28,.92); }}
        [data-testid="stSidebar"] {{ background: linear-gradient(180deg, #10152B 0%, #0B1122 100%); border-right: 1px solid #242A49; }}
        [data-testid="stSidebar"] * {{ color: {TEXT}; }}
        .block-container {{ max-width: 1660px; padding: 1.6rem clamp(1rem, 3vw, 2.6rem) 3rem; }}
        h1, h2, h3, h4 {{ color: {TEXT} !important; letter-spacing: -.025em; }}
        h2 {{ margin-top: 1.5rem; }}
        p, label, .stCaption {{ color: {MUTED}; }}
        .hero {{ padding: clamp(1.25rem, 2.5vw, 2rem); border: 1px solid #34345D; border-radius: 22px;
          background: linear-gradient(115deg, rgba(32,37,78,.96) 0%, rgba(17,26,48,.98) 62%, rgba(12,24,43,.98) 100%);
          box-shadow: 0 18px 48px rgba(0,0,0,.2); margin-bottom: 1.1rem; }}
        .hero-top {{ display:flex; align-items:center; justify-content:space-between; gap:1rem; }}
        .hero h1 {{ color: white; margin: 0; font-size: clamp(1.45rem, 3.3vw, 2.45rem); line-height: 1.1; }}
        .hero p {{ color: #C2CBE0; margin: .5rem 0 0; font-size: 1rem; }}
        .hero-mark {{ color: {ACCENT_TURQUOISE}; font-size: clamp(2rem, 4vw, 3.4rem); filter: drop-shadow(0 0 18px rgba(53,214,194,.25)); }}
        .hero-meta {{ display:flex; flex-wrap:wrap; gap:.6rem; margin-top:1.3rem; }}
        .meta-pill {{ border:1px solid rgba(135,150,200,.2); background:rgba(7,13,28,.36); border-radius:11px; padding:.55rem .78rem; min-width:145px; }}
        .meta-label {{ display:block; color:#91A0BD; font-size:.62rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }}
        .meta-value {{ display:block; color:#F4F6FC; font-size:.84rem; margin-top:.2rem; font-weight:600; }}
        .eyebrow {{ color: {ACCENT_TURQUOISE}; text-transform: uppercase; letter-spacing: .16em;
          font-size: .7rem; font-weight: 700; margin-bottom: .5rem; }}
        .notice {{ border: 1px solid rgba(155,138,251,.35); border-left: 4px solid {ACCENT_PURPLE};
          background: linear-gradient(90deg, rgba(86,61,150,.2), rgba(18,26,46,.72)); color: #E5E0FF; padding: .9rem 1rem; border-radius: 12px; }}
        [data-testid="stMetric"] {{ background: linear-gradient(145deg, #171F39, #11192D); border: 1px solid #2A3455;
          border-radius: 16px; padding: 1rem 1.1rem; min-height: 120px; height:100%; min-width:0; box-shadow: 0 8px 24px rgba(0,0,0,.12); }}
        [data-testid="stMetricLabel"] {{ color: {MUTED}; font-size:.82rem; white-space:normal; overflow:visible; }}
        [data-testid="stMetricValue"] {{ color: white; font-size:clamp(1.2rem, 1.7vw, 1.65rem); font-weight:700; white-space:normal; overflow-wrap:anywhere; }}
        [data-testid="stMetricDelta"] {{ color:{ACCENT_TURQUOISE}; }}
        div[data-testid="stPlotlyChart"] {{ background: rgba(18,26,46,.75); border: 1px solid #2A3455;
          border-radius: 16px; padding: .45rem; box-shadow: 0 8px 24px rgba(0,0,0,.12); }}
        div[data-testid="stDataFrame"] {{ border: 1px solid #2A3455; border-radius: 14px; overflow:hidden; }}
        [data-testid="stSidebar"] [role="radiogroup"] {{ gap:.35rem; }}
        [data-testid="stSidebar"] [role="radiogroup"] label {{ border:1px solid transparent; border-radius:11px; padding:.45rem .55rem; transition:all .15s ease; }}
        [data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background:rgba(155,138,251,.12); border-color:rgba(155,138,251,.2); }}
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background:linear-gradient(90deg, rgba(155,138,251,.2), rgba(69,184,255,.08)); border-color:rgba(155,138,251,.34); box-shadow:inset 3px 0 {ACCENT_TURQUOISE}; }}
        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {{ color:#FFFFFF; font-weight:650; }}
        [data-baseweb="select"] > div {{ background-color:#141D35; border-color:#303A5D; border-radius:10px; }}
        [data-baseweb="input"] > div {{ background-color:#141D35; border-color:#303A5D; border-radius:10px; }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {{ line-height:1.08; font-size:1.35rem; }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h4 {{ color:#B8C3DC !important; font-size:.82rem; text-transform:uppercase; letter-spacing:.1em; }}
        .section-note {{ color: {MUTED}; font-size: .9rem; }}
        @media (max-width: 700px) {{ .block-container {{ padding-top:1rem; }} .hero {{ border-radius:16px; }} .meta-pill {{ flex:1 1 40%; min-width:125px; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner="Loading Spotify chart observations…")
def load_data(path: str, modified_time: float) -> pd.DataFrame:
    """Load the cleaned chart file and normalize analysis fields."""
    data = pd.read_csv(path, dtype={"cc": "string", "track_id": "string"})
    data["week_end"] = pd.to_datetime(data["week_end"], errors="coerce")
    for column in ("rank", "streams", "appearances", "peak", "prev_rank"):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    for column in ("cc", "track_id", "title", "artists"):
        data[column] = data[column].fillna("").astype(str).str.strip()
    data["market_name"] = data["cc"].str.lower().map(COUNTRY_NAMES).fillna(data["cc"].str.upper())
    data["artist_list"] = data["artists"].apply(split_artists)
    data["year"] = data["week_end"].dt.year
    return data


@st.cache_data(show_spinner="Loading provisional Afrobeats classifications…")
def load_review(path: str, modified_time: float) -> pd.DataFrame:
    """Load review decisions without inferring genre from chart metadata."""
    review = pd.read_csv(path, dtype={"track_id": "string", "classification": "string"})
    for column in ("track_id", "title", "artists", "classification"):
        review[column] = review[column].fillna("").astype(str).str.strip()
    return review.loc[review["classification"].eq("Afrobeats")].copy()


def split_artists(value):
    return [name.strip() for name in re.split(r"\s*[|;/&,]\s*", str(value)) if name.strip()]


def chart_layout(height=390, **kwargs):
    layout = dict(
        template="plotly_dark",
        height=height,
        margin=dict(l=48, r=34, t=48, b=38),
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(family="Inter, Segoe UI, sans-serif", color=TEXT, size=11),
        title_font=dict(size=15, color=TEXT),
        legend=dict(bgcolor="rgba(16,30,48,.65)", font=dict(color=TEXT)),
        xaxis=dict(gridcolor="#2B3554", zerolinecolor="#354265", title_font_color=MUTED),
        yaxis=dict(gridcolor="#2B3554", zerolinecolor="#354265", title_font_color=MUTED),
    )
    layout.update(kwargs)
    return layout


def show_header(section, date_range=None, selected_markets=None, market_options=None):
    if isinstance(date_range, tuple) and len(date_range) == 2:
        period = f"{date_range[0]:%b %d, %Y} – {date_range[1]:%b %d, %Y}"
    elif date_range is not None:
        period = f"Through {date_range:%b %d, %Y}"
    else:
        period = "Dataset coverage"
    if selected_markets is None:
        market_context = "Awaiting data"
    elif market_options and len(selected_markets) == len(market_options):
        market_context = f"All {len(selected_markets):,} markets"
    else:
        market_context = f"{len(selected_markets):,} market(s) selected"
    st.markdown(
        f'<div class="hero"><div class="hero-top"><div><div class="eyebrow">Spotify chart intelligence · Capstone research</div>'
        f'<h1>GLOBAL AFROBEATS MARKET INTELLIGENCE</h1>'
        f'<p>{section} · Identifying international growth opportunities for emerging Afrobeats artists.</p></div>'
        f'<div class="hero-mark">◈</div></div><div class="hero-meta">'
        f'<div class="meta-pill"><span class="meta-label">Reporting period</span><span class="meta-value">{period}</span></div>'
        f'<div class="meta-pill"><span class="meta-label">Active market filter</span><span class="meta-value">{market_context}</span></div>'
        f'<div class="meta-pill"><span class="meta-label">Current view</span><span class="meta-value">{section}</span></div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="notice"><strong>Classification status:</strong> The chart dataset has no genre field. '
        'Afrobeats track-level verification and the proposed analysis are not complete. '
        'Charts below describe the available Spotify Top 200 chart data; they do not identify '
        'Afrobeats tracks or establish growth opportunities.</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    if section != "Overview":
        st.subheader(section)


def metric_row(data):
    markets = data["cc"].replace("", pd.NA).nunique()
    tracks = data.loc[data["track_id"].ne(""), "track_id"].nunique()
    artists = {artist for values in data["artist_list"] for artist in values}
    streams = data["streams"].sum(min_count=1)
    appearances = data["appearances"].sum(min_count=1)
    values = [
        ("Markets covered", f"{markets:,}", "Distinct market codes in the selected observations"),
        ("Chart rows", f"{len(data):,}", "Track × market × chart-week rows"),
        ("Unique tracks", f"{tracks:,}", "Distinct nonblank track IDs"),
        ("Unique artists", f"{len(artists):,}", "Distinct credited artist names"),
        ("Reported streams", format_total(streams), "Sum of supplied stream values; source counting window is unconfirmed"),
        ("Chart appearances", format_total(appearances), "Sum of source appearances field; definition needs confirmation"),
    ]
    for start in range(0, len(values), 3):
        columns = st.columns(3)
        for col, (label, value, help_text) in zip(columns, values[start:start + 3]):
            col.metric(label, value, help=help_text)


def format_total(value):
    return "—" if pd.isna(value) else f"{value:,.0f}"


def render_market_map(data):
    market_counts = data.groupby(["cc", "market_name"], as_index=False).size().rename(columns={"size": "Observations"})
    market_counts["map_name"] = market_counts["cc"].str.lower().map(COUNTRY_NAMES)
    mapped = market_counts.dropna(subset=["map_name"])
    if mapped.empty:
        st.info("No market codes could be mapped for the geographic view.")
        return
    fig = px.choropleth(
        mapped, locations="map_name", locationmode="country names", color="Observations",
        hover_name="market_name", hover_data={"cc": True, "Observations": ":,"},
        color_continuous_scale=[[0, "#26335B"], [0.52, ACCENT_PURPLE], [1, ACCENT_TURQUOISE]],
        labels={"Observations": "Chart observations"},
        title="Observed chart coverage by market",
    )
    fig.update_geos(bgcolor=PANEL, showframe=False, showcoastlines=False, landcolor="#18283B", lakecolor=PANEL)
    fig.update_layout(**chart_layout(400, coloraxis_colorbar=dict(title="Observations", tickfont_color=TEXT)))
    st.plotly_chart(fig, use_container_width=True, key="market-map-coverage")
    st.caption("Map shows dataset observation counts, not Afrobeats demand or growth. Unmapped market codes remain in the tables and counts.")


def render_market_bars(data, metric="streams", title="Reported streams by market", limit=20):
    if metric == "streams":
        values = data.groupby("market_name", as_index=False)["streams"].sum(min_count=1)
        label = "Reported streams (sum)"
    elif metric == "observations":
        values = data.groupby("market_name", as_index=False).size().rename(columns={"size": "observations"})
        metric, label = "observations", "Chart observations"
    else:
        values = data.groupby("market_name", as_index=False)["appearances"].sum(min_count=1)
        label = "Reported appearances (sum)"
    values = values.dropna(subset=[metric])
    values = values.sort_values([metric, "market_name"], ascending=[False, True])
    if limit is not None:
        values = values.head(limit)
    values = values.sort_values([metric, "market_name"], ascending=[True, False])
    fig = px.bar(values, x=metric, y="market_name", orientation="h", color_discrete_sequence=[ACCENT_BLUE],
                 labels={metric: label, "market_name": "Market"}, title=title,
                 hover_data={metric: ":,"})
    fig.update_traces(texttemplate="%{x:,.0f}", textposition="outside", cliponaxis=False)
    fig.update_layout(
        **chart_layout(max(320, min(560, 13 * len(values) + 100)), margin=dict(l=135, r=105, t=50, b=42)),
        showlegend=False,
    )
    fig.update_xaxes(tickformat=",.0f", automargin=True)
    fig.update_yaxes(title=None, automargin=True)
    st.plotly_chart(fig, use_container_width=True, key=f"market-bars-{metric}")


def render_time_series(data):
    trend = data.dropna(subset=["week_end"]).groupby("week_end", as_index=False).agg(
        streams=("streams", "sum"), observations=("track_id", "size")
    )
    fig = px.line(trend, x="week_end", y="streams", markers=False,
                  labels={"week_end": "Chart week", "streams": "Reported streams (sum)"},
                  title="Reported streaming performance over time")
    fig.update_traces(line_color=ACCENT_TURQUOISE, line_width=2.5)
    fig.update_layout(**chart_layout(330))
    st.plotly_chart(fig, use_container_width=True, key="market-stream-trend")
    st.caption("Each point sums the supplied streams values for all selected track × market rows sharing that chart week. The source streams counting window has not been confirmed.")


def render_track_rankings(data):
    tracks = data[data["title"].ne("")].groupby(["track_id", "title", "artists"], as_index=False).agg(
        streams=("streams", "sum"), chart_weeks=("week_end", "nunique"), best_rank=("rank", "min")
    )
    top = tracks.nlargest(15, "streams").sort_values("streams")
    fig = px.bar(top, x="streams", y="title", orientation="h", color_discrete_sequence=[ACCENT_PURPLE],
                 hover_data={"artists": True, "chart_weeks": True, "best_rank": True, "streams": ":,"},
                 labels={"streams": "Reported streams (sum)", "title": "Track", "artists": "Credited artists",
                         "chart_weeks": "Observed chart weeks", "best_rank": "Best observed rank"},
                 title="Tracks by reported streams")
    fig.update_layout(**chart_layout(max(340, min(450, 20 * len(top) + 100))), showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key="track-stream-rankings")


def render_artist_performance(data):
    records = data[["artist_list", "streams", "week_end", "track_id"]].explode("artist_list").rename(columns={"artist_list": "artist"})
    records = records[records["artist"].notna() & records["artist"].ne("")]
    artists = records.groupby("artist", as_index=False).agg(
        streams=("streams", "sum"), observed_tracks=("track_id", "nunique"), chart_weeks=("week_end", "nunique")
    )
    top = artists.nlargest(15, "streams").sort_values("streams")
    fig = px.bar(top, x="streams", y="artist", orientation="h", color_discrete_sequence=[ACCENT_BLUE],
                 hover_data={"observed_tracks": True, "chart_weeks": True, "streams": ":,"},
                 labels={"streams": "Reported streams (sum)", "artist": "Credited artist",
                         "observed_tracks": "Distinct chart track IDs", "chart_weeks": "Observed chart weeks"},
                 title="Artists by reported chart streams")
    fig.update_layout(**chart_layout(max(340, min(450, 20 * len(top) + 100))), showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key="artist-stream-rankings")
    st.caption("Artist credit strings are split on common separators; collaboration credits can contribute to each listed artist.")


def render_overview(data):
    metric_row(data)
    left, right = st.columns([1.08, 1])
    with left:
        render_market_map(data)
    with right:
        render_market_bars(data, "streams", "Reported streams across markets")
    render_time_series(data)


def render_global(data):
    metric_row(data)
    render_market_map(data)
    st.subheader("Streaming trend")
    render_time_series(data)
    render_market_bars(data, "observations", "Chart observation coverage by market")


def render_country(data):
    metric = st.selectbox("Compare markets by", ["Reported streams", "Chart observations", "Reported appearances"])
    key = {"Reported streams": "streams", "Chart observations": "observations", "Reported appearances": "appearances"}[metric]
    is_global = data["cc"].str.casefold().eq("global") | data["market_name"].str.casefold().eq("global")
    global_data = data.loc[is_global]
    country_data = data.loc[~is_global]
    if country_data.empty:
        st.info("No country-market observations match the current filters. The GLOBAL chart entry is shown separately below.")
    else:
        render_market_bars(country_data, key, f"{metric} by country market", limit=None)
        if key == "observations":
            observations_by_market = country_data.groupby("market_name").size()
            repeated_values = observations_by_market.value_counts()
            common_count = int(repeated_values.index[0])
            markets_at_common_count = int(repeated_values.iloc[0])
            if markets_at_common_count > 1:
                st.caption(
                    f"{markets_at_common_count:,} of {len(observations_by_market):,} country markets have "
                    f"{common_count:,} chart observations under the current filters. Equal bar lengths "
                    "reflect equal track × market × week row counts in the source data."
                )
    summary = country_data.groupby(["market_name", "cc"], as_index=False).agg(
        observations=("track_id", "size"), unique_tracks=("track_id", "nunique"),
        reported_streams=("streams", "sum"), first_chart_week=("week_end", "min"), last_chart_week=("week_end", "max")
    ).sort_values("reported_streams", ascending=False)
    st.dataframe(summary, width="stretch", height="content", hide_index=True, column_config={
        "observations": st.column_config.NumberColumn("Chart observations", format="%,.0f"),
        "unique_tracks": st.column_config.NumberColumn("Unique tracks", format="%,.0f"),
        "reported_streams": st.column_config.NumberColumn("Reported streams", format="%,.0f"),
        "first_chart_week": st.column_config.DateColumn("First chart week"),
        "last_chart_week": st.column_config.DateColumn("Last chart week"),
    })
    if not global_data.empty:
        global_value = len(global_data) if key == "observations" else global_data[key].sum(min_count=1)
        global_col, note_col = st.columns([1, 2])
        with global_col:
            st.metric(f"GLOBAL chart · {metric.lower()}", format_total(global_value))
        with note_col:
            st.caption("GLOBAL is reported separately and excluded from the country chart and country table.")
    st.caption("Country comparisons summarize the available chart data and are not Afrobeats-specific market rankings.")


def render_tracks(data):
    st.markdown("#### Track performance")
    render_track_rankings(data)
    st.markdown("#### Artist performance")
    render_artist_performance(data)
    st.info("These rankings cover all chart records in the selected data. They are not filtered to verified Afrobeats tracks because a complete track-level classification dataset is not available.")


def render_afrobeats(data, reviewed_tracks):
    st.markdown("<div class=\"notice\">Based on the first 20 reviewed candidates. Classifications are provisional and the catalogue is incomplete.</div>", unsafe_allow_html=True)
    if reviewed_tracks.empty:
        st.info("No tracks are currently classified as Afrobeats in the review file.")
        return

    # The review file and chart dataset both identify tracks with `track_id`.
    # Count the chart's track × market × week rows as observed chart appearances.
    chart = data.loc[data["track_id"].isin(reviewed_tracks["track_id"])].copy()
    if chart.empty:
        st.info("No provisionally Afrobeats tracks have chart records in the selected date range and markets.")
        return

    catalog = reviewed_tracks[["track_id", "title", "artists"]].drop_duplicates("track_id")
    chart = chart.merge(catalog, on="track_id", how="inner", suffixes=("_chart", "_review"))
    chart["display_title"] = chart["title_review"].where(chart["title_review"].ne(""), chart["title_chart"])
    chart["credited_artists"] = chart["artists_review"].where(chart["artists_review"].ne(""), chart["artists_chart"])

    tracks = chart.groupby(["track_id", "display_title", "credited_artists"], as_index=False).agg(
        chart_appearances=("track_id", "size"),
        markets=("market_name", lambda values: ", ".join(sorted(set(values.dropna())))),
        best_chart_position=("rank", "min"),
        total_recorded_streams=("streams", lambda values: values.sum(min_count=1)),
    ).sort_values(["chart_appearances", "display_title"], ascending=[False, True])
    tracks = tracks.rename(columns={
        "display_title": "Track",
        "credited_artists": "Credited artists",
        "chart_appearances": "Chart appearances",
        "markets": "Markets appeared",
        "best_chart_position": "Best chart position",
        "total_recorded_streams": "Total recorded streams",
    })
    st.dataframe(tracks, width="stretch", height="content", row_height=44, hide_index=True, column_config={
        "Track": st.column_config.TextColumn(width="medium"),
        "Credited artists": st.column_config.TextColumn(width="medium"),
        "Chart appearances": st.column_config.NumberColumn(width="small", format="%d"),
        "Markets appeared": st.column_config.TextColumn(width="large"),
        "Best chart position": st.column_config.NumberColumn(width="small", format="%d"),
        "Total recorded streams": st.column_config.NumberColumn(width="medium", format="%,.0f"),
    })
    st.caption("Widen columns or scroll horizontally to inspect full market lists and stream totals.")

    artist_rows = chart[["artist_list", "track_id", "week_end", "cc"]].explode("artist_list").rename(columns={"artist_list": "artist"})
    artist_rows = artist_rows[artist_rows["artist"].notna() & artist_rows["artist"].ne("")].drop_duplicates(["artist", "track_id", "week_end", "cc"])
    artist_counts = artist_rows.groupby("artist", as_index=False).size().rename(columns={"size": "Chart appearances"})
    artist_counts = artist_counts.nlargest(15, "Chart appearances").sort_values("Chart appearances")
    track_counts = tracks.rename(columns={"Track": "track", "Chart appearances": "Chart appearances"})
    track_counts = track_counts.nlargest(15, "Chart appearances").sort_values("Chart appearances")
    is_global = chart["cc"].str.casefold().eq("global") | chart["market_name"].str.casefold().eq("global")
    global_chart = chart.loc[is_global]
    country_chart = chart.loc[~is_global]
    market_counts = country_chart.groupby("market_name", as_index=False).size().rename(columns={"size": "Chart appearances"})
    market_counts = market_counts.sort_values("Chart appearances")

    left, right = st.columns(2)
    with left:
        fig = px.bar(artist_counts, x="Chart appearances", y="artist", orientation="h",
                     color_discrete_sequence=[ACCENT_PURPLE], title="Top Afrobeats artists by chart appearances")
        fig.update_layout(**chart_layout(max(300, min(440, 18 * len(artist_counts) + 100))), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="afrobeats-artist-appearances")
    with right:
        fig = px.bar(track_counts, x="Chart appearances", y="track", orientation="h",
                     color_discrete_sequence=[ACCENT_BLUE], title="Top Afrobeats tracks by chart appearances")
        fig.update_layout(**chart_layout(max(300, min(440, 18 * len(track_counts) + 100))), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="afrobeats-track-appearances")

    if not market_counts.empty:
        fig = px.bar(market_counts, x="Chart appearances", y="market_name", orientation="h",
                     color_discrete_sequence=[ACCENT_TURQUOISE], title="Afrobeats track performance by country market",
                     labels={"market_name": "Country market"})
        fig.update_layout(**chart_layout(max(300, min(480, 15 * len(market_counts) + 100))), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="afrobeats-country-appearances")
    else:
        st.info("No country-market chart records are available in the selected filters.")
    st.markdown("#### GLOBAL chart entry (global chart)")
    if global_chart.empty:
        st.info("No GLOBAL chart records are available in the selected filters.")
    else:
        st.metric("Global chart appearances", f"{len(global_chart):,}")
    st.caption("Chart appearances count matched track × market × chart-week records within the active dashboard filters. Stream totals sum the supplied streams values when available.")


def render_track_market_charts(chart, country_chart, reviewed_tracks):
    st.markdown("#### Track appearances across international markets")
    if reviewed_tracks.empty:
        st.info("No provisionally Afrobeats-classified tracks are available to chart.")
        return

    reviewed = reviewed_tracks.drop_duplicates("track_id").to_dict("records")
    for offset in range(0, len(reviewed), 2):
        columns = st.columns(2)
        for column, track in zip(columns, reviewed[offset:offset + 2]):
            with column:
                track_id = track["track_id"]
                track_chart = chart.loc[chart["track_id"].eq(track_id)]
                track_countries = country_chart.loc[country_chart["track_id"].eq(track_id)]
                title = track.get("title") or (track_chart["title"].iloc[0] if not track_chart.empty else track_id)
                artists = track.get("artists") or (track_chart["artists"].iloc[0] if not track_chart.empty else "")
                st.markdown(f"**{title}**  \n{artists}")
                st.caption(f"Total chart appearances: {len(track_chart):,}")

                if track_chart.empty:
                    st.info("No matching chart data for this track under the current date and market filters.")
                    continue
                if track_countries.empty:
                    st.info("No country-chart appearances for this track under the current filters. GLOBAL appearances remain in the separate global chart summary.")
                    continue

                country_counts = track_countries.groupby("market_name", as_index=False).size().rename(
                    columns={"size": "Chart appearances"}
                ).sort_values("Chart appearances", ascending=True)
                fig = px.bar(
                    country_counts, x="Chart appearances", y="market_name", orientation="h",
                    text="Chart appearances", color_discrete_sequence=[ACCENT_BLUE],
                    labels={"Chart appearances": "Chart appearances", "market_name": "Country"},
                )
                fig.update_traces(texttemplate="%{x:.0f}", textposition="outside", cliponaxis=False)
                fig.update_layout(
                    **chart_layout(max(300, min(540, 14 * len(country_counts) + 100))),
                    showlegend=False,
                    title=None,
                )
                fig.update_xaxes(tickmode="linear", dtick=1, range=[0, country_counts["Chart appearances"].max() * 1.25])
                st.plotly_chart(fig, use_container_width=True, key=f"track-market-appearances-{track_id}")


def render_opportunities(data, reviewed_tracks):
    st.warning(
        "PRELIMINARY FINDINGS: Based on six provisionally classified tracks from the first 20 reviewed candidates. "
        "This is not yet a representative Afrobeats market ranking."
    )

    if reviewed_tracks.empty:
        chart = data.iloc[0:0].copy()
    else:
        chart = data.loc[data["track_id"].isin(reviewed_tracks["track_id"])].copy()

    is_global = chart["cc"].str.lower().eq("global") | chart["market_name"].str.lower().eq("global")
    global_chart = chart.loc[is_global]
    country_chart = chart.loc[~is_global]
    artists = {artist for values in chart["artist_list"] for artist in values if artist}
    metrics = st.columns(4)
    metrics[0].metric("Country markets", f"{country_chart['market_name'].nunique():,}")
    metrics[1].metric("Distinct Afrobeats tracks", f"{chart['track_id'].nunique():,}")
    metrics[2].metric("Credited artists", f"{len(artists):,}")
    metrics[3].metric("Total chart appearances", f"{len(chart):,}", help="Includes country-market and GLOBAL chart observations.")

    if chart.empty:
        st.info("No provisionally Afrobeats-classified tracks appear in the current date and market selection.")
    else:
        st.markdown("#### Country market comparison")
        if country_chart.empty:
            st.info("No country-market observations match the current filters; any GLOBAL entry is shown separately below.")
        else:
            market_summary = country_chart.groupby(["cc", "market_name"], as_index=False).agg(
                distinct_tracks=("track_id", "nunique"),
                chart_appearances=("track_id", "size"),
                best_chart_position=("rank", "min"),
                total_streams=("streams", lambda values: values.sum(min_count=1)),
            )
            market_artists = country_chart[["cc", "market_name", "artist_list"]].explode("artist_list")
            market_artists = market_artists[market_artists["artist_list"].notna() & market_artists["artist_list"].ne("")]
            artist_counts = market_artists.groupby(["cc", "market_name"], as_index=False).agg(
                distinct_artists=("artist_list", "nunique")
            )
            market_summary = market_summary.merge(artist_counts, on=["cc", "market_name"], how="left")
            market_summary["distinct_artists"] = market_summary["distinct_artists"].fillna(0).astype(int)
            market_summary = market_summary.sort_values(
                ["chart_appearances", "market_name"], ascending=[False, True]
            )
            display_markets = market_summary.rename(columns={
                "market_name": "Market",
                "distinct_tracks": "Distinct Afrobeats tracks",
                "distinct_artists": "Distinct credited artists",
                "chart_appearances": "Chart appearances",
                "best_chart_position": "Best chart position",
                "total_streams": "Total streams",
            })[["Market", "Distinct Afrobeats tracks", "Distinct credited artists", "Chart appearances", "Best chart position", "Total streams"]]
            st.dataframe(display_markets, width="stretch", height="content", hide_index=True, column_config={
                "Distinct Afrobeats tracks": st.column_config.NumberColumn(format="%d"),
                "Distinct credited artists": st.column_config.NumberColumn(format="%d"),
                "Chart appearances": st.column_config.NumberColumn(format="%d"),
                "Best chart position": st.column_config.NumberColumn(format="%d"),
                "Total streams": st.column_config.NumberColumn(format="%,.0f"),
            })

            appearances_ranked = market_summary.sort_values("chart_appearances")
            appearances_fig = px.bar(
                appearances_ranked, x="chart_appearances", y="market_name", orientation="h",
                color_discrete_sequence=[ACCENT_TURQUOISE], title="Markets ranked by Afrobeats chart appearances",
                labels={"chart_appearances": "Chart appearances", "market_name": "Country market"},
            )
            appearances_fig.update_layout(**chart_layout(max(300, min(520, 16 * len(appearances_ranked) + 100))), showlegend=False)
            st.plotly_chart(appearances_fig, use_container_width=True, key="growth-market-appearances")

            tracks_ranked = market_summary.sort_values("distinct_tracks")
            tracks_fig = px.bar(
                tracks_ranked, x="distinct_tracks", y="market_name", orientation="h",
                color_discrete_sequence=[ACCENT_PURPLE], title="Markets ranked by distinct Afrobeats tracks",
                labels={"distinct_tracks": "Distinct Afrobeats tracks", "market_name": "Country market"},
            )
            tracks_fig.update_layout(**chart_layout(max(300, min(520, 16 * len(tracks_ranked) + 100))), showlegend=False)
            st.plotly_chart(tracks_fig, use_container_width=True, key="growth-distinct-tracks")

        st.markdown("#### GLOBAL chart entry")
        if global_chart.empty:
            st.info("No GLOBAL chart observations match the current filters.")
        else:
            global_summary = pd.DataFrame([{
                "Chart": "GLOBAL (global chart)",
                "Distinct Afrobeats tracks": global_chart["track_id"].nunique(),
                "Distinct credited artists": len({artist for values in global_chart["artist_list"] for artist in values if artist}),
                "Chart appearances": len(global_chart),
                "Best chart position": global_chart["rank"].min(),
                "Total streams": global_chart["streams"].sum(min_count=1),
            }])
            st.dataframe(global_summary, width="stretch", hide_index=True, column_config={
                "Distinct Afrobeats tracks": st.column_config.NumberColumn(format="%d"),
                "Distinct credited artists": st.column_config.NumberColumn(format="%d"),
                "Chart appearances": st.column_config.NumberColumn(format="%d"),
                "Best chart position": st.column_config.NumberColumn(format="%d"),
                "Total streams": st.column_config.NumberColumn(format="%,.0f"),
            })

    render_track_market_charts(chart, country_chart, reviewed_tracks)
    st.caption("These descriptive chart observations do not measure revenue, profitability, audience size, or future growth.")
    st.divider()
    st.markdown("#### General Spotify chart coverage context (not Afrobeats-specific)")
    if data.empty:
        st.info("No general chart observations match the current filters.")
    else:
        render_market_bars(data, "observations", "General chart coverage by market")


def render_methodology(data):
    st.markdown("### Data source and coverage")
    first = data["week_end"].min()
    last = data["week_end"].max()
    st.write(f"This view uses `{DATA_FILE.relative_to(PROJECT_DIR)}`. The loaded records span **{first:%Y-%m-%d} to {last:%Y-%m-%d}** across **{data['cc'].nunique():,} market codes**.")

    st.markdown("### DATA PREPARATION")
    st.markdown(
        "The Spotify Top 200 dataset contains chart records from the yearly Spotify chart archives; the project README identifies the downloaded source as Zenodo. "
        "Each row represents one **track × market × chart week** observation, identified by `track_id`, `cc`, and `week_end`. "
        "The prepared file contains **324,800 observations** across **38 markets**, covering **January 4, 2024 to October 15, 2026**.\n\n"
        "`src/clean_spotify_data.py` combines the three canonical yearly archives while retaining the source columns and rows. "
        "It checks the expected headers and row widths, then reopens the saved file to verify its row count and date range. "
        "The duplicate 2026 archive candidate with a `(1)` filename suffix is excluded. "
        "`src/inspect_spotify_data.py` scans the archives and summarizes row counts, dates, distinct track IDs, and markets. "
        "Rows are not collapsed across chart weeks or markets because those repeated observations are the dataset's intended structure."
    )

    st.markdown("### AFROBEATS CLASSIFICATION")
    st.markdown(
        "Classification is performed at the **track level** using track-specific evidence recorded in the review file and assessed against the project codebook. "
        "The three labels mean:\n\n"
        "- **Afrobeats** — track-specific evidence supports the study's Afrobeats definition.\n"
        "- **Not Afrobeats** — evidence identifies another genre, or Afrobeat alone, without qualifying Afrobeats evidence.\n"
        "- **Uncertain/Unclassified** — evidence is missing, ambiguous, conflicting, or insufficient to decide consistently.\n\n"
        "Artist nationality, name, language, collaborators, or the market where a track charted cannot establish its genre on their own. "
        "The first **20 candidates** have been reviewed; decisions remain **provisional**. The current six Afrobeats tracks are a limited review result, "
        "not a complete or representative Afrobeats catalogue."
    )

    st.markdown("### MARKET ANALYSIS METRICS")
    st.markdown(
        "- **Chart appearances:** number of chart observations for classified tracks in a market.\n"
        "- **Distinct tracks:** number of unique classified track IDs appearing in a market.\n"
        "- **Distinct artists:** number of unique credited artist names represented in a market.\n"
        "- **Best chart position:** the lowest numerical `rank` recorded for the classified tracks in that market.\n"
        "- **Stream totals:** sum of the supplied `streams` values for those chart observations; the source counting scope and methodology still require confirmation."
    )

    st.markdown("### RESEARCH LIMITATIONS")
    st.markdown(
        "- The current classification sample is limited to the first 20 reviewed candidates, including six provisional Afrobeats decisions.\n"
        "- Historical data coverage and source comparability remain under assessment.\n"
        "- Spotify chart presence does not equal total listening demand.\n"
        "- Chart appearances do not directly measure revenue, profitability, or audience size.\n"
        "- Market opportunity conclusions remain preliminary and should not be inferred from chart appearances alone."
    )

    st.markdown("### Interpretation notes")
    st.markdown(
        "- Each row is treated as a track × market × chart-week observation.\n"
        "- Market codes, field meanings, and chart semantics follow the current project data dictionary and may require further confirmation.\n"
        "- Reported stream totals are sums of the supplied `streams` field; its counting window and methodology require confirmation.\n"
        "- `appearances` is a source field with an unresolved counting scope. Its totals are shown descriptively.\n"
        "- Track and artist rankings are calculated from chart observations and are not genre classifications.\n"
        "- The 200-track Afrobeats classification target and historical source comparability are not complete."
    )
    st.markdown("### Project documentation")
    st.markdown("- `data/spotify_data_dictionary.txt` — field descriptions and interpretation questions\n- `data/afrobeats_classification_codebook.txt` — provisional track-level classification rules\n- `data/data_inspection.txt` and `data/spotify_data_summary.txt` — source archive inspection and combined coverage summaries")

    st.markdown("### RESEARCH REPRODUCIBILITY")
    st.markdown(
        "**Data and documentation**\n\n"
        "- `data/spotify_top200_cleaned.csv` — chart observations used by the dashboard.\n"
        "- `data/data_inspection.txt` and `data/spotify_data_summary.txt` — inspected source archive counts, date ranges, track counts, and market coverage.\n"
        "- `data/spotify_data_dictionary.txt` — chart fields and known interpretation limits.\n"
        "- `data/afrobeats_first20_review.csv` — track IDs, reviewed evidence, provisional classifications, rationales, and adjudication notes for the first 20 candidates.\n"
        "- `data/afrobeats_classification_codebook.txt` — the draft classification rules and provisional evidence standard.\n"
        "- `data/afrobeats_artist_discovery_list.txt`, `data/afrobeats_candidate_pool.csv`, `data/afrobeats_candidate_matches.csv`, and `data/afrobeats_screening_shortlist.csv` — discovery inputs and unverified candidates or possible matches used to guide manual review.\n"
        "- `data/afrobeats_screening_shortlist_README.md` — explains how the shortlist was selected and why its candidates are not genre findings.\n\n"
        "**Scripts and dashboard**\n\n"
        "- `src/inspect_spotify_data.py` — inspects yearly source archives and summarizes their coverage.\n"
        "- `src/clean_spotify_data.py` — combines the selected yearly archives and validates the saved output.\n"
        "- `src/build_afrobeats_candidate_pool.py` and `src/create_afrobeats_screening_shortlist.py` — identify and prioritize candidates for review; they do not assign genre.\n"
        "- `src/match_afrobeats_candidates.py` — searches for candidate title and artist-credit matches in the chart dataset.\n"
        "- `src/create_classification_pilot.py` — creates a reproducible random pilot sample of unique tracks with a fixed seed; it leaves classifications blank.\n"
        "- `app.py` — renders the dashboard and its filtered descriptive comparisons."
    )
    st.markdown("### Filters")
    st.caption(f"Current selection: {len(data):,} chart observations from {data['week_end'].min():%Y-%m-%d} through {data['week_end'].max():%Y-%m-%d}.")


def main():
    apply_theme()
    st.sidebar.markdown('<div class="eyebrow">Research workspace</div>', unsafe_allow_html=True)
    st.sidebar.markdown("## GLOBAL AFROBEATS\n## MARKET INTELLIGENCE")
    st.sidebar.caption("◈  Spotify chart research · Capstone project")
    st.sidebar.divider()
    nav_icons = {
        "Overview": "⌂",
        "Global Market Performance": "◉",
        "Country Comparison": "▦",
        "Track & Artist Performance": "♫",
        "Afrobeats Artists & Tracks": "♪",
        "Growth Opportunities": "✦",
        "Data & Methodology": "ⓘ",
    }
    section = st.sidebar.radio(
        "Navigate", NAV_ITEMS,
        format_func=lambda item: f"{nav_icons[item]}   {item}",
        label_visibility="collapsed",
    )

    if not DATA_FILE.exists():
        show_header(section)
        st.error(f"The cleaned Spotify dataset was not found at `{DATA_FILE.relative_to(PROJECT_DIR)}`.")
        st.stop()
    data = load_data(str(DATA_FILE), DATA_FILE.stat().st_mtime)
    if data.empty:
        show_header(section)
        st.warning("The cleaned Spotify dataset contains no observations.")
        st.stop()

    if REVIEW_FILE.exists():
        reviewed_tracks = load_review(str(REVIEW_FILE), REVIEW_FILE.stat().st_mtime)
    else:
        reviewed_tracks = pd.DataFrame(columns=["track_id", "title", "artists", "classification"])

    min_date = data["week_end"].min().date()
    max_date = data["week_end"].max().date()
    st.sidebar.markdown("#### Refine view")
    date_range = st.sidebar.date_input("Chart date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    market_options = sorted(data["market_name"].dropna().unique())
    selected_markets = st.sidebar.multiselect("Markets", market_options, default=market_options)
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = map(pd.Timestamp, date_range)
        filtered = data[data["week_end"].between(start_date, end_date)]
    else:
        filtered = data
    filtered = filtered[filtered["market_name"].isin(selected_markets)]
    st.sidebar.caption("All charts and metrics use this selection.")

    show_header(section, date_range, selected_markets, market_options)
    if filtered.empty and section != "Growth Opportunities":
        st.info("No observations match these filters. Expand the date range or select one or more markets.")
        return
    if section == "Overview":
        render_overview(filtered)
    elif section == "Global Market Performance":
        render_global(filtered)
    elif section == "Country Comparison":
        render_country(filtered)
    elif section == "Track & Artist Performance":
        render_tracks(filtered)
    elif section == "Afrobeats Artists & Tracks":
        render_afrobeats(filtered, reviewed_tracks)
    elif section == "Growth Opportunities":
        render_opportunities(filtered, reviewed_tracks)
    else:
        render_methodology(filtered)
    st.caption("GLOBAL AFROBEATS MARKET INTELLIGENCE · Research prototype · Findings pending classification and analysis")


if __name__ == "__main__":
    main()
