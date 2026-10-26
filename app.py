
import html
import json
from pathlib import Path

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from folium.plugins import FastMarkerCluster


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="LA Corridor Intelligence",
    page_icon="🗺️",
    layout="wide",
)

BASE = Path(__file__).parent
CLUSTER_DIR = BASE / "data" / "clustered"
BOUNDARY_DIR = BASE / "data" / "final_corridor_boundaries"

CORRIDORS = {
    "Western Avenue": "western_avenue",
    "Wilshire Boulevard": "wilshire_boulevard",
    "Olympic Boulevard": "olympic_boulevard",
    "Vermont Avenue": "vermont_avenue",
    "Larchmont Boulevard": "larchmont_boulevard",
}

CLUSTER_COLORS = [
    "#2563EB", "#DC2626", "#16A34A", "#9333EA", "#EA580C",
    "#0891B2", "#CA8A04", "#DB2777", "#4B5563", "#65A30D",
]

BOUNDARY_COLOR = "#111827"

CATEGORY_COLUMNS = [
    "primary_naics_description",
    "business_category",
    "category",
    "industry",
    "naics_description",
    "business_type",
]

NAME_COLUMNS = [
    "business_name", "name", "business", "company_name"
]


# ============================================================
# 2. FILE PATH HELPERS
# ============================================================

def csv_path_for(slug):
    return CLUSTER_DIR / f"{slug}_sensitivity.csv"


def boundary_path_for(slug):
    return BOUNDARY_DIR / f"{slug}_boundary.geojson"


def get_file_modified_time(path):
    if not path.exists():
        return 0
    return path.stat().st_mtime_ns


# ============================================================
# 3. LOAD DATA
# ============================================================

@st.cache_data(show_spinner=False)
def load_corridor_csv(path_string, modified_time):
    path = Path(path_string)

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_boundary(path_string, modified_time):
    path = Path(path_string)

    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return None


# ============================================================
# 4. COLUMN DETECTION AND DATA CLEANING
# ============================================================

def find_column(df, possible_names):
    """Find a column without depending on capitalization."""

    lookup = {
        str(col).lower().strip(): col
        for col in df.columns
    }

    for name in possible_names:
        found = lookup.get(name.lower().strip())
        if found is not None:
            return found

    return None


def get_coordinate_columns(df):
    latitude_col = find_column(df, ["latitude", "lat"])
    longitude_col = find_column(df, ["longitude", "lon", "lng"])
    return latitude_col, longitude_col


def clean_map_data(df, cluster_col, show_noise=True):
    if df.empty:
        return pd.DataFrame()

    latitude_col, longitude_col = get_coordinate_columns(df)

    if latitude_col is None or longitude_col is None:
        return pd.DataFrame()

    if cluster_col not in df.columns:
        return pd.DataFrame()

    result = df.copy()

    result[latitude_col] = pd.to_numeric(
        result[latitude_col], errors="coerce"
    )
    result[longitude_col] = pd.to_numeric(
        result[longitude_col], errors="coerce"
    )
    result[cluster_col] = pd.to_numeric(
        result[cluster_col], errors="coerce"
    )

    result = result.dropna(
        subset=[latitude_col, longitude_col, cluster_col]
    )

    result = result[
        result[latitude_col].between(-90, 90)
        & result[longitude_col].between(-180, 180)
    ]

    if not show_noise:
        result = result[result[cluster_col] != -1]

    result = result.rename(
        columns={
            latitude_col: "latitude",
            longitude_col: "longitude",
        }
    )

    return result


def cluster_color(cluster_value):
    try:
        cluster_number = int(float(cluster_value))
    except (TypeError, ValueError):
        return "#6B7280"

    if cluster_number == -1:
        return "#9CA3AF"

    return CLUSTER_COLORS[
        cluster_number % len(CLUSTER_COLORS)
    ]


def clean_category_values(series):
    """Standardize category values for meaningful comparisons."""

    values = series.astype("string").str.strip()

    missing_values = [
        "", "nan", "none", "null", "n/a", "unknown"
    ]

    values = values.mask(
        values.str.lower().isin(missing_values),
        "Unknown / missing",
    )

    return values.fillna("Unknown / missing")


# ============================================================
# 5. FAST INTERACTIVE MAP WITH BOUNDARY
# ============================================================

@st.cache_data(show_spinner=False, max_entries=40)
def build_corridor_map(
    slug,
    corridor_name,
    eps,
    show_noise,
    csv_modified_time,
    boundary_modified_time,
):
    data_path = csv_path_for(slug)
    boundary_path = boundary_path_for(slug)

    raw_df = load_corridor_csv(
        str(data_path), csv_modified_time
    )

    cluster_col = f"cluster_{eps}m"

    map_df = clean_map_data(
        raw_df, cluster_col, show_noise
    )

    if map_df.empty:
        return None, (
            f"No valid map records found for {corridor_name}. "
            f"Expected column: {cluster_col}."
        )

    boundary_data = load_boundary(
        str(boundary_path), boundary_modified_time
    )

    street_map = folium.Map(
        location=[
            map_df["latitude"].mean(),
            map_df["longitude"].mean(),
        ],
        zoom_start=14,
        tiles="OpenStreetMap",
        prefer_canvas=True,
        control_scale=True,
    )

    # Draw the boundary polygon.
    if boundary_data is not None:
        boundary_layer = folium.GeoJson(
            boundary_data,
            name="Validated corridor boundary",
            style_function=lambda feature: {
                "color": BOUNDARY_COLOR,
                "weight": 4,
                "opacity": 1.0,
                "fillColor": "#FDE68A",
                "fillOpacity": 0.12,
            },
            highlight_function=lambda feature: {
                "color": "#F59E0B",
                "weight": 5,
                "fillOpacity": 0.20,
            },
            tooltip=f"{corridor_name} — validated boundary",
        )

        boundary_layer.add_to(street_map)

        try:
            bounds = boundary_layer.get_bounds()
            if bounds and len(bounds) == 2:
                street_map.fit_bounds(
                    bounds, padding=(20, 20)
                )
        except (ValueError, TypeError, IndexError):
            pass

    name_col = find_column(map_df, NAME_COLUMNS)
    address_col = find_column(
        map_df, ["street_address", "address", "full_address"]
    )
    category_col = find_column(map_df, CATEGORY_COLUMNS)

    marker_data = []

    for _, row in map_df.iterrows():
        cluster_number = int(row[cluster_col])

        business_name = (
            str(row[name_col])
            if name_col and pd.notna(row[name_col])
            else "Unknown business"
        )

        address = (
            str(row[address_col])
            if address_col and pd.notna(row[address_col])
            else "Address unavailable"
        )

        category = (
            str(row[category_col])
            if category_col and pd.notna(row[category_col])
            else "Category unavailable"
        )

        marker_data.append([
            float(row["latitude"]),
            float(row["longitude"]),
            cluster_color(cluster_number),
            html.escape(business_name),
            html.escape(address),
            html.escape(category),
            str(cluster_number),
        ])

    if marker_data:
        marker_callback = """
        function(row) {
            var marker = L.circleMarker(
                [row[0], row[1]],
                {
                    radius: 4,
                    color: row[2],
                    fillColor: row[2],
                    fillOpacity: 0.85,
                    weight: 1
                }
            );

            var popupContent =
                '<b>' + row[3] + '</b><br>' +
                'Address: ' + row[4] + '<br>' +
                'Category: ' + row[5] + '<br>' +
                'DBSCAN cluster: ' + row[6];

            marker.bindPopup(popupContent);
            return marker;
        }
        """

        FastMarkerCluster(
            data=marker_data,
            callback=marker_callback,
            name="Businesses by DBSCAN cluster",
            options={"chunkedLoading": True},
        ).add_to(street_map)

    folium.LayerControl(collapsed=False).add_to(street_map)

    return street_map.get_root().render(), None


# ============================================================
# 6. BUSINESS CATEGORY COMPARISON ACROSS ALL CORRIDORS
# ============================================================

@st.cache_data(show_spinner=False)
def load_category_comparison(file_signature):
    """
    Read each corridor CSV and count its business categories.

    file_signature contains the current file paths and modification
    times, so a changed CSV can refresh the comparison.
    """

    frames = []
    errors = []

    for corridor_name, slug in CORRIDORS.items():
        path = csv_path_for(slug)

        if not path.exists():
            errors.append(f"{corridor_name}: CSV file not found")
            continue

        raw_df = load_corridor_csv(
            str(path), get_file_modified_time(path)
        )

        if raw_df.empty:
            errors.append(f"{corridor_name}: CSV is empty or unreadable")
            continue

        category_col = find_column(raw_df, CATEGORY_COLUMNS)

        if category_col is None:
            errors.append(
                f"{corridor_name}: no business-category column found"
            )
            continue

        categories = clean_category_values(raw_df[category_col])

        corridor_frame = pd.DataFrame({
            "Corridor": corridor_name,
            "Business Category": categories,
        })

        frames.append(corridor_frame)

    if not frames:
        return pd.DataFrame(), errors

    all_categories = pd.concat(frames, ignore_index=True)

    comparison = (
        all_categories
        .groupby(
            ["Corridor", "Business Category"],
            as_index=False,
        )
        .size()
        .rename(columns={"size": "Business Count"})
    )

    return comparison, errors


# ============================================================
# 7. SIDEBAR CONTROLS
# ============================================================

st.sidebar.title("🗺️ Corridor Controls")
st.sidebar.caption("Los Angeles Corridor Intelligence")

corridor = st.sidebar.selectbox(
    "Select a corridor",
    list(CORRIDORS.keys()),
)

eps = st.sidebar.selectbox(
    "DBSCAN distance (epsilon)",
    [25, 40, 60],
    index=1,
    format_func=lambda value: f"{value} metres",
)

show_noise = st.sidebar.checkbox(
    "Show noise / unclustered businesses",
    value=True,
)

st.sidebar.divider()
st.sidebar.markdown("**Map legend**")
st.sidebar.markdown(
    "- **Black outline:** corridor boundary\n"
    "- **Colored points:** DBSCAN clusters\n"
    "- **Gray points:** noise (cluster -1)"
)

slug = CORRIDORS[corridor]
data_path = csv_path_for(slug)
boundary_path = boundary_path_for(slug)


# ============================================================
# 8. LOAD SELECTED CORRIDOR
# ============================================================

st.title("LA Corridor Intelligence Dashboard")
st.caption(
    "Explore validated corridor boundaries, business locations, "
    "DBSCAN clusters, and business-category patterns."
)

if not data_path.exists():
    st.error(f"Cluster data file not found: {data_path}")
    st.stop()

if not boundary_path.exists():
    st.warning(
        f"Boundary file not found: {boundary_path}. "
        "The map can still display business locations."
    )

with st.spinner(f"Loading {corridor}..."):
    raw_df = load_corridor_csv(
        str(data_path),
        get_file_modified_time(data_path),
    )

    cluster_col = f"cluster_{eps}m"
    map_df = clean_map_data(raw_df, cluster_col, show_noise)

if raw_df.empty:
    st.error("The CSV file is empty or could not be loaded.")
    st.stop()

if cluster_col not in raw_df.columns:
    st.error(
        f"Column '{cluster_col}' was not found in the selected CSV."
    )
    st.write("Available columns:", list(raw_df.columns))
    st.stop()

if map_df.empty:
    st.error(
        "No valid records are available for these map settings. "
        "Check the latitude, longitude, and cluster columns."
    )
    st.stop()


# ============================================================
# 9. SUMMARY METRICS
# ============================================================

all_valid_locations = clean_map_data(
    raw_df, cluster_col, True
)

cluster_values = pd.to_numeric(
    all_valid_locations[cluster_col], errors="coerce"
).dropna()

non_noise_clusters = sorted(
    int(value)
    for value in cluster_values.unique()
    if value != -1
)

noise_count = int((cluster_values == -1).sum())

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total records", f"{len(raw_df):,}")
col2.metric("Valid map locations", f"{len(all_valid_locations):,}")
col3.metric("DBSCAN clusters", len(non_noise_clusters))
col4.metric("Noise records", f"{noise_count:,}")

st.divider()


# ============================================================
# 10. INTERACTIVE MAP
# ============================================================

st.subheader(f"{corridor} — {eps} m DBSCAN clusters")

st.caption(
    "The polygon outlines the corridor boundary. "
    "Click a point to inspect its business details."
)

with st.spinner("Preparing interactive map..."):
    map_html, map_error = build_corridor_map(
        slug,
        corridor,
        eps,
        show_noise,
        get_file_modified_time(data_path),
        get_file_modified_time(boundary_path),
    )

if map_error:
    st.warning(map_error)

if map_html:
    components.html(
        map_html,
        height=620,
        scrolling=False,
    )


# ============================================================
# 11. DBSCAN CLUSTER SUMMARY AND CHART
# ============================================================

st.divider()
st.subheader(f"DBSCAN Cluster Analysis — {corridor}")

cluster_summary = (
    map_df.groupby(cluster_col, dropna=False)
    .agg(
        Businesses=("latitude", "size"),
        Mean_Latitude=("latitude", "mean"),
        Mean_Longitude=("longitude", "mean"),
    )
    .reset_index()
    .rename(columns={cluster_col: "Cluster"})
)

cluster_summary["Cluster Type"] = cluster_summary["Cluster"].apply(
    lambda value: "Noise" if value == -1 else "Cluster"
)

cluster_summary = cluster_summary[
    [
        "Cluster",
        "Cluster Type",
        "Businesses",
        "Mean_Latitude",
        "Mean_Longitude",
    ]
]

st.dataframe(
    cluster_summary,
    use_container_width=True,
    hide_index=True,
)

chart_df = cluster_summary.copy()

chart_df["Cluster Label"] = chart_df["Cluster"].apply(
    lambda value: "Noise (-1)" if value == -1 else f"Cluster {value}"
)

cluster_fig = px.bar(
    chart_df,
    x="Cluster Label",
    y="Businesses",
    color="Cluster Type",
    title=f"Business Count by DBSCAN Cluster — {corridor}",
    labels={
        "Cluster Label": "DBSCAN cluster",
        "Businesses": "Number of businesses",
    },
)

cluster_fig.update_layout(
    xaxis_title="DBSCAN cluster",
    yaxis_title="Number of businesses",
    legend_title="Cluster type",
)

st.plotly_chart(cluster_fig, use_container_width=True)


# ============================================================
# 12. BUSINESS CATEGORY COMPARISON ACROSS FIVE CORRIDORS
# ============================================================

st.divider()
st.header("Business Category Comparison Across Corridors")

st.write(
    "This section compares business types using the original records "
    "from all five corridor CSV files. It is independent of the "
    "selected map epsilon setting."
)

file_signature = tuple(
    (
        str(csv_path_for(slug)),
        get_file_modified_time(csv_path_for(slug)),
    )
    for slug in CORRIDORS.values()
)

with st.spinner("Comparing business categories across all corridors..."):
    category_comparison, category_errors = load_category_comparison(
        file_signature
    )

if category_errors:
    with st.expander("Category comparison data warnings"):
        for message in category_errors:
            st.warning(message)

if category_comparison.empty:
    st.warning(
        "The category comparison could not be generated. "
        "Check that the corridor CSV files contain a business-category "
        "column, such as primary_naics_description."
    )
else:
    # Top categories are selected by total count across all corridors.
    category_totals = (
        category_comparison
        .groupby("Business Category", as_index=False)["Business Count"]
        .sum()
        .sort_values("Business Count", ascending=False)
    )

    available_categories = len(category_totals)

    top_n = st.slider(
        "Number of business categories to compare",
        min_value=3,
        max_value=max(3, min(20, available_categories)),
        value=min(10, max(3, available_categories)),
        step=1,
    )

    top_categories = category_totals.head(top_n)[
        "Business Category"
    ].tolist()

    plot_comparison = category_comparison[
        category_comparison["Business Category"].isin(top_categories)
    ].copy()

    # Graph 1: Compare the same categories across every corridor.
    st.subheader("Which business categories are most common in each corridor?")

    category_fig = px.bar(
        plot_comparison,
        x="Corridor",
        y="Business Count",
        color="Business Category",
        barmode="group",
        title=f"Top {len(top_categories)} Business Categories by Corridor",
        labels={
            "Corridor": "Commercial corridor",
            "Business Count": "Number of businesses",
            "Business Category": "Business category",
        },
        category_orders={
            "Corridor": list(CORRIDORS.keys()),
            "Business Category": top_categories,
        },
    )

    category_fig.update_layout(
        xaxis_title="Commercial corridor",
        yaxis_title="Number of businesses",
        legend_title="Business category",
        xaxis_tickangle=-20,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
    )

    st.plotly_chart(category_fig, use_container_width=True)

    # Graph 2: Overall leading categories.
    st.subheader("Most common business categories overall")

    overall_fig = px.bar(
        category_totals.head(top_n).sort_values(
            "Business Count", ascending=True
        ),
        x="Business Count",
        y="Business Category",
        orientation="h",
        title=f"Top {top_n} Categories Across All Five Corridors",
        labels={
            "Business Count": "Total number of businesses",
            "Business Category": "Business category",
        },
    )

    overall_fig.update_layout(
        xaxis_title="Total number of businesses",
        yaxis_title="Business category",
        yaxis={"categoryorder": "total ascending"},
    )

    st.plotly_chart(overall_fig, use_container_width=True)

    # Table: exact counts per corridor and category.
    st.subheader("Business Category Counts")

    category_pivot = (
        plot_comparison
        .pivot_table(
            index="Business Category",
            columns="Corridor",
            values="Business Count",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(columns=list(CORRIDORS.keys()), fill_value=0)
        .reset_index()
    )

    st.dataframe(
        category_pivot,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        label="Download business category comparison CSV",
        data=category_comparison.to_csv(index=False).encode("utf-8"),
        file_name="business_category_comparison_all_corridors.csv",
        mime="text/csv",
        use_container_width=False,
    )


# ============================================================
# 13. BUSINESS DATA TABLE
# ============================================================

st.divider()
st.subheader("Business Records")

with st.expander("View business records", expanded=False):
    st.write(
        f"Showing {len(map_df):,} records for the selected settings."
    )

    st.dataframe(
        map_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 14. DOWNLOAD SELECTED CORRIDOR RESULTS
# ============================================================

st.divider()
st.subheader("Download Results")

download_col1, download_col2 = st.columns(2)

with download_col1:
    st.download_button(
        label="Download selected corridor CSV",
        data=map_df.to_csv(index=False).encode("utf-8"),
        file_name=f"{slug}_cluster_{eps}m.csv",
        mime="text/csv",
        use_container_width=True,
    )

with download_col2:
    st.download_button(
        label="Download cluster summary",
        data=cluster_summary.to_csv(index=False).encode("utf-8"),
        file_name=f"{slug}_cluster_summary_{eps}m.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ============================================================
# 15. CORRIDOR BOUNDARY STATUS
# ============================================================

st.divider()
st.subheader("Boundary File Status")

if boundary_path.exists():
    st.success("Boundary GeoJSON file found.")

    boundary_data = load_boundary(
        str(boundary_path),
        get_file_modified_time(boundary_path),
    )

    feature_count = (
        len(boundary_data.get("features", []))
        if boundary_data else 0
    )

    st.write(f"Boundary features: {feature_count:,}")

    if feature_count > 1:
        st.info(
            "This boundary contains multiple polygon features or parts. "
            "They are displayed together on the map."
        )
else:
    st.error(
        "No boundary GeoJSON was found for this corridor. "
        "Check the filename inside data/final_corridor_boundaries."
    )

st.caption(
    "Important: DBSCAN clusters are based on the selected CSV and "
    "epsilon setting. Business-category counts use the corridor CSV "
    "records and do not independently prove that each business lies "
    "inside its validated boundary."
)
