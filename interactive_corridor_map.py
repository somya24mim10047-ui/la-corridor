
import pandas as pd
import folium
from folium.plugins import Fullscreen

# ----------------------------------------
# 1. LOAD BUSINESS DATA
# ----------------------------------------

print("Loading Western Avenue business data...")

df = pd.read_csv("western_avenue_businesses.csv")

# Handle common column-name variations
df.columns = df.columns.str.strip().str.lower()

# Find coordinate columns
lat_col = next(
    (c for c in ["latitude", "lat"] if c in df.columns), None
)
lon_col = next(
    (c for c in ["longitude", "lon", "lng"] if c in df.columns), None
)

if lat_col is None or lon_col is None:
    raise ValueError(
        f"Latitude/longitude columns not found. Available: {list(df.columns)}"
    )

df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")

df = df.dropna(subset=[lat_col, lon_col]).copy()

# Keep points in the approximate study area
south, north = 34.0615, 34.0690
west, east = -118.3125, -118.3060

df = df[
    df[lat_col].between(south, north)
    & df[lon_col].between(west, east)
].copy()

print("Business records in map window:", len(df))


# ----------------------------------------
# 2. DEFINE PROPOSED ENDPOINTS
# Verify these on the map before finalizing.
# ----------------------------------------

start = (34.062100, -118.308881)
end = (34.068419, -118.309011)

# Center the map between endpoints
center_lat = (start[0] + end[0]) / 2
center_lon = (start[1] + end[1]) / 2


# ----------------------------------------
# 3. CREATE BASE MAP
# ----------------------------------------

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=16,
    tiles="OpenStreetMap",
    control_scale=True
)

Fullscreen(position="topright").add_to(m)


# ----------------------------------------
# LAYER 1: PROPOSED STUDY AREA
# ----------------------------------------

boundary_layer = folium.FeatureGroup(
    name="1. Proposed Study Boundary",
    show=True
)

# This line is a preliminary reference, NOT the actual road geometry.
folium.PolyLine(
    locations=[start, end],
    color="red",
    weight=5,
    opacity=0.9,
    tooltip="Preliminary straight reference line - verify road alignment"
).add_to(boundary_layer)

folium.Marker(
    location=start,
    tooltip="Proposed start: Wilshire Boulevard",
    popup="Start point - verify exact road intersection",
    icon=folium.Icon(color="green", icon="play")
).add_to(boundary_layer)

folium.Marker(
    location=end,
    tooltip="Proposed end: West 3rd Street",
    popup="End point - verify exact road intersection",
    icon=folium.Icon(color="red", icon="stop")
).add_to(boundary_layer)

boundary_layer.add_to(m)


# ----------------------------------------
# LAYER 2: BUSINESS LOCATIONS
# ----------------------------------------

business_layer = folium.FeatureGroup(
    name="2. Business Locations",
    show=True
)

for index, row in df.iterrows():

    # Use available business details for the popup
    details = []

    for column in [
        "business_name",
        "business_name_legal",
        "street_address",
        "address",
        "business_type",
        "industry",
        "naics_description"
    ]:
        if column in df.columns and pd.notna(row[column]):
            details.append(
                f"<b>{column.replace('_', ' ').title()}:</b> "
                f"{row[column]}"
            )

    popup_text = "<br>".join(details) if details else "Business record"

    folium.CircleMarker(
        location=[row[lat_col], row[lon_col]],
        radius=4,
        color="blue",
        fill=True,
        fill_color="dodgerblue",
        fill_opacity=0.7,
        tooltip="Business location",
        popup=folium.Popup(popup_text, max_width=300)
    ).add_to(business_layer)

business_layer.add_to(m)


# ----------------------------------------
# LAYER 3: STUDY ENDPOINTS ONLY
# ----------------------------------------

endpoint_layer = folium.FeatureGroup(
    name="3. Start and End Points",
    show=True
)

folium.Marker(
    location=start,
    tooltip="Start - Western Avenue & Wilshire Boulevard",
    icon=folium.Icon(color="green", icon="flag")
).add_to(endpoint_layer)

folium.Marker(
    location=end,
    tooltip="End - Western Avenue & West 3rd Street",
    icon=folium.Icon(color="red", icon="flag")
).add_to(endpoint_layer)

endpoint_layer.add_to(m)


# ----------------------------------------
# 4. ADD LAYER SWITCHER
# ----------------------------------------

folium.LayerControl(collapsed=False).add_to(m)

# Add a title
title_html = """
<div style="
position: fixed;
top: 10px;
left: 50px;
z-index: 9999;
background: white;
padding: 10px 14px;
border: 1px solid #999;
border-radius: 5px;
font-size: 16px;
font-weight: bold;">
Western Avenue Corridor - Preliminary Research Map
</div>
"""

m.get_root().html.add_child(folium.Element(title_html))

# Save map
output_file = "western_avenue_interactive_map.html"
m.save(output_file)

print("\nInteractive map saved:", output_file)
print("Business points plotted:", len(df))
print("Open the HTML file in your web browser.")
print("Verify endpoints and road alignment before finalizing.")
