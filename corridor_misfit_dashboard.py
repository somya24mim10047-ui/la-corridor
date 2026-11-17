from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="LA Corridor Intelligence",
    page_icon="🏙️",
    layout="wide"
)

BASE = Path("data/corridor_misfit")
OUT = Path("outputs/stage4_visualizations")

st.title("🏙️ LA Corridor Intelligence")
st.caption(
    "Commercial–Community Alignment Intelligence | "
    "Corridor Misfit Detector"
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    comparison = pd.read_csv(BASE / "corridor_comparison.csv")
    categories = pd.read_csv(BASE / "business_category_distribution.csv")
    scores = pd.read_csv(BASE / "category_misfit_scores.csv")
    diagnostics = pd.read_csv(BASE / "corridor_misfit_diagnostics.csv")
    sensitivity = pd.read_csv(BASE / "sensitivity_stability_by_corridor.csv")

    return comparison, categories, scores, diagnostics, sensitivity


try:
    comparison, categories, scores, diagnostics, sensitivity = load_data()
except Exception as e:
    st.error(f"Unable to load project datasets: {e}")
    st.stop()

corridors = comparison["corridor"].tolist()

service_order = [
    "Healthcare",
    "Grocery",
    "Education",
    "Pharmacy",
    "Social Assistance"
]

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("Dashboard Controls")

selected_corridor = st.sidebar.selectbox(
    "Select LA Corridor",
    corridors
)

st.sidebar.markdown("---")
st.sidebar.caption("Analysis covers five selected LA corridors.")

st.sidebar.markdown(
    """
    **Navigation**
    - Overview
    - Business Profile
    - Essential Services
    - Misfit Analysis
    - Community Pressure
    - Sensitivity Analysis
    - Data & Methodology
    """
)

# --------------------------------------------------
# FILTER SELECTED CORRIDOR
# --------------------------------------------------

row = comparison[
    comparison["corridor"] == selected_corridor
].iloc[0]

corridor_categories = categories[
    categories["corridor"] == selected_corridor
].copy()

corridor_scores = scores[
    scores["corridor"] == selected_corridor
].copy()

corridor_diagnostic = diagnostics[
    diagnostics["corridor"] == selected_corridor
].iloc[0]

corridor_sensitivity = sensitivity[
    sensitivity["corridor"] == selected_corridor
].iloc[0]

# --------------------------------------------------
# OVERVIEW
# --------------------------------------------------

st.header("1. Corridor Overview")

st.subheader(selected_corridor)

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Business Records",
    f"{int(row['business_record_count']):,}"
)

c2.metric(
    "Unique Business Accounts",
    f"{int(row['unique_business_accounts']):,}"
)

c3.metric(
    "Classification Coverage",
    f"{row['classification_coverage_pct']:.2f}%"
)

c4.metric(
    "Everyday Services",
    f"{int(row['everyday_service_businesses']):,}"
)

st.info(
    "This dashboard compares business composition and service "
    "representation with community-level socioeconomic indicators. "
    "Results are exploratory screening signals, not proof of inadequate access."
)

# --------------------------------------------------
# BUSINESS PROFILE
# --------------------------------------------------

st.divider()
st.header("2. Business Profile")

left, right = st.columns(2)

with left:
    st.metric(
        "Everyday Service Share",
        f"{row['everyday_service_share_pct']:.2f}%"
    )

    st.metric(
        "Businesses per 1,000 Residents",
        f"{row['businesses_per_1000_residents']:.2f}"
    )

    st.metric(
        "Everyday Services per 1,000 Residents",
        f"{row['everyday_services_per_1000_residents']:.2f}"
    )

with right:
    top_categories = (
        corridor_categories
        .sort_values("business_count", ascending=False)
        .head(10)
        .sort_values("business_count")
    )

    fig = px.bar(
        top_categories,
        x="business_count",
        y="business_category",
        orientation="h",
        title="Top 10 Business Categories",
        labels={
            "business_count": "Business Records",
            "business_category": "Category"
        },
        text="business_count"
    )

    fig.update_layout(height=430)
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# BUSINESS COMPOSITION COMPARISON
# --------------------------------------------------

st.subheader("Business Composition Across Corridors")

top_all = (
    categories.groupby("business_category")["business_count"]
    .sum()
    .nlargest(10)
    .index
)

composition = categories[
    categories["business_category"].isin(top_all)
]

fig = px.bar(
    composition,
    x="business_category",
    y="business_count",
    color="corridor",
    barmode="group",
    title="Top Business Categories Across Five Corridors"
)

fig.update_layout(
    xaxis_title="Business Category",
    yaxis_title="Business Records",
    xaxis_tickangle=-35
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# ESSENTIAL SERVICES
# --------------------------------------------------

st.divider()
st.header("3. Essential Service Representation")

st.write(
    "Representation index: 100 represents the pooled five-corridor "
    "benchmark. Values below 100 indicate below-benchmark representation."
)

service_display = corridor_scores.set_index(
    "service_category"
).reindex(service_order).reset_index()

fig = px.bar(
    service_display,
    x="service_category",
    y="service_representation_index",
    color="service_representation_index",
    color_continuous_scale="RdYlGn",
    range_color=[0, 200],
    text="service_representation_index",
    title=f"Essential Services – {selected_corridor}"
)

fig.add_hline(
    y=100,
    line_dash="dash",
    line_color="black",
    annotation_text="Pooled benchmark = 100"
)

fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
fig.update_layout(
    xaxis_title="Essential Service",
    yaxis_title="Representation Index",
    coloraxis_showscale=False
)

st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    service_display[
        [
            "service_category",
            "service_business_count",
            "service_representation_index",
            "below_benchmark_service_flag"
        ]
    ],
    hide_index=True,
    use_container_width=True
)

# --------------------------------------------------
# MISFIT ANALYSIS
# --------------------------------------------------

st.divider()
st.header("4. Category-Level Misfit Analysis")

st.write(
    "The category misfit score combines the service gap score "
    "and community pressure score. It does not represent an overall "
    "corridor score."
)

fig = px.bar(
    service_display,
    x="service_category",
    y="category_misfit_score",
    color="category_misfit_score",
    color_continuous_scale="YlOrRd",
    range_color=[0, 100],
    text="category_misfit_score",
    title=f"Potential Misfit Signals – {selected_corridor}"
)

fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
fig.update_layout(
    xaxis_title="Service Category",
    yaxis_title="Category Misfit Score",
    coloraxis_showscale=False
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Five-Corridor Misfit Heatmap")

heatmap_data = scores.pivot(
    index="corridor",
    columns="service_category",
    values="category_misfit_score"
).reindex(columns=service_order)

fig = px.imshow(
    heatmap_data,
    text_auto=".2f",
    aspect="auto",
    color_continuous_scale="YlOrRd",
    zmin=0,
    zmax=100,
    title="Category Misfit Scores Across All Corridors"
)

fig.update_layout(
    xaxis_title="Essential Service",
    yaxis_title="Corridor"
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# COMMUNITY PRESSURE
# --------------------------------------------------

st.divider()
st.header("5. Community Economic Pressure")

p1, p2, p3 = st.columns(3)

p1.metric(
    "Poverty Rate",
    f"{row['poverty_rate_pct']:.2f}%"
)

p2.metric(
    "Rent Burden 30%+",
    f"{row['rent_burden_30_plus_pct']:.2f}%"
)

p3.metric(
    "Rent Burden 50%+",
    f"{row['rent_burden_50_plus_pct']:.2f}%"
)

pressure_data = comparison[
    [
        "corridor",
        "poverty_rate_pct",
        "rent_burden_30_plus_pct",
        "rent_burden_50_plus_pct"
    ]
].melt(
    id_vars="corridor",
    var_name="indicator",
    value_name="percentage"
)

fig = px.bar(
    pressure_data,
    x="corridor",
    y="percentage",
    color="indicator",
    barmode="group",
    title="Economic Pressure Across Five Corridors",
    labels={
        "corridor": "Corridor",
        "percentage": "Percentage (%)",
        "indicator": "Indicator"
    }
)

st.plotly_chart(fig, use_container_width=True)

# Income and rent
st.subheader("Income and Housing Affordability")

fig = go.Figure()

fig.add_trace(go.Bar(
    x=comparison["corridor"],
    y=comparison["community_proxy_median_household_income_usd"],
    name="Proxy Median Household Income"
))

fig.add_trace(go.Bar(
    x=comparison["corridor"],
    y=comparison["weighted_proxy_median_monthly_gross_rent_usd"],
    name="Monthly Gross Rent"
))

fig.update_layout(
    barmode="group",
    title="Income and Monthly Gross Rent Proxies",
    yaxis_title="USD",
    xaxis_title="Corridor"
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Income and rent are proxy estimates. They should not be interpreted "
    "as individual household affordability measurements."
)

# --------------------------------------------------
# SENSITIVITY ANALYSIS
# --------------------------------------------------

st.divider()
st.header("6. Sensitivity Analysis")

st.metric(
    "Sensitivity Status",
    corridor_sensitivity["sensitivity_status"]
)

s1, s2 = st.columns(2)

s1.metric(
    "Minimum Positive Signals",
    int(corridor_sensitivity["minimum_positive_signals"])
)

s2.metric(
    "Maximum Positive Signals",
    int(corridor_sensitivity["maximum_positive_signals"])
)

fig = go.Figure()

for _, item in sensitivity.iterrows():
    fig.add_trace(go.Scatter(
        x=[
            item["minimum_positive_signals"],
            item["maximum_positive_signals"]
        ],
        y=[item["corridor"], item["corridor"]],
        mode="lines+markers",
        name=item["corridor"],
        line=dict(width=5)
    ))

fig.update_layout(
    title="Sensitivity Range Across Threshold Methods",
    xaxis_title="Number of Positive Misfit Signals",
    yaxis_title="Corridor",
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    sensitivity,
    hide_index=True,
    use_container_width=True
)

# --------------------------------------------------
# CORRIDOR DIAGNOSTICS
# --------------------------------------------------

st.divider()
st.header("7. Corridor Diagnostics")

st.dataframe(
    diagnostics,
    hide_index=True,
    use_container_width=True
)

# --------------------------------------------------
# DATA DOWNLOADS
# --------------------------------------------------

st.divider()
st.header("8. Download Project Data")

download_files = {
    "Corridor Comparison": (comparison, "corridor_comparison.csv"),
    "Business Categories": (categories, "business_category_distribution.csv"),
    "Category Misfit Scores": (scores, "category_misfit_scores.csv"),
    "Corridor Diagnostics": (diagnostics, "corridor_misfit_diagnostics.csv"),
    "Sensitivity Analysis": (sensitivity, "sensitivity_stability_by_corridor.csv")
}

for label, (data, filename) in download_files.items():
    st.download_button(
        label=f"Download {label}",
        data=data.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=filename
    )

# --------------------------------------------------
# METHODOLOGY AND LIMITATIONS
# --------------------------------------------------

st.divider()
st.header("9. Methodology and Limitations")

st.markdown("""
**How to interpret this dashboard**

- Service representation index of 100 means the pooled benchmark.
- A value below 100 indicates below-benchmark service representation.
- Category misfit scores combine service gaps with community pressure.
- A zero category misfit score does not mean there is no service gap.
- No overall corridor composite score or definitive corridor ranking is assigned.

**Important limitations**

1. Only five corridors are compared.
2. Business corridor boundaries and 0.5-mile community buffers are different geographic units.
3. Business counts do not measure service capacity or utilization.
4. Service representation is relative, not proof of service adequacy.
5. Community poverty and rent burden are not service-specific demand measures.
6. Business accounts may overlap between corridors.
7. NAICS classification may not capture every business activity.
8. The analysis does not establish causal relationships.
9. Sensitivity findings for Olympic and Wilshire vary across tested thresholds.
10. Population and business density measures are contextual because their geographic units differ.
""")

limitations_path = BASE / "stage3_limitations_and_interpretation.csv"

if limitations_path.exists():
    with st.expander("View structured limitations register"):
        limitations = pd.read_csv(limitations_path)
        st.dataframe(limitations, hide_index=True, use_container_width=True)

st.caption(
    "LA Corridor Intelligence | Exploratory analytical screening | "
    "No definitive corridor ranking"
)
