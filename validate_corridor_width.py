

import requests
import pandas as pd
import matplotlib.pyplot as plt

from shapely.geometry import Point, box, shape
from shapely.ops import unary_union, transform
from pyproj import Transformer

# ==========================================
# 1. SETTINGS
# ==========================================

CSV_FILE = "western_avenue_businesses.csv"

START_LAT, START_LON = 34.062100, -118.308881
END_LAT, END_LON = 34.068419, -118.309011

SOUTH = min(START_LAT, END_LAT) - 0.0015
NORTH = max(START_LAT, END_LAT) + 0.0015
WEST = min(START_LON, END_LON) - 0.0020
EAST = max(START_LON, END_LON) + 0.0020

WIDTHS = [50, 100, 200]

project = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
).transform

# Official City of Los Angeles street centerline service
SERVICE_URL = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

# ==========================================
# 2. DOWNLOAD OFFICIAL ROAD GEOMETRY
# ==========================================

print("Requesting official LA street centerline data...")

params = {
    "where": "UPPER(STNAME) LIKE '%WESTERN%'",
    "outFields": "OBJECTID,STNAME,STSFX,SFXDIR",
    "returnGeometry": "true",
    "geometry": f"{WEST},{SOUTH},{EAST},{NORTH}",
    "geometryType": "esriGeometryEnvelope",
    "inSR": 4326,
    "spatialRel": "esriSpatialRelIntersects",
    "outSR": 4326,
    "f": "geojson",
}

response = requests.get(
    SERVICE_URL,
    params=params,
    timeout=90
)
response.raise_for_status()

result = response.json()

if result.get("error"):
    raise RuntimeError(f"GIS service error: {result['error']}")

features = result.get("features", [])

if not features:
    raise RuntimeError(
        "No matching street features returned. "
        "Check the GIS service or query fields."
    )

print("Features returned:", len(features))

# Keep only features identified as Western Avenue
road_lines = []

for feature in features:
    properties = feature.get("properties", {})
    street_name = str(properties.get("STNAME", "")).upper()
    suffix = str(properties.get("STSFX", "")).upper()

    if "WESTERN" not in street_name:
        continue

    # Include common street-suffix spellings
    if suffix and suffix not in ["AVE", "AV", "AVENUE"]:
        continue

    geometry = feature.get("geometry")

    if geometry:
        road_lines.append(shape(geometry))

if not road_lines:
    raise RuntimeError(
        "No Western Avenue features remained after filtering. "
        "Inspect the returned STNAME and STSFX field values."
    )

# Restrict road features to the study rectangle
study_rectangle = box(WEST, SOUTH, EAST, NORTH)

road_geometry = unary_union(road_lines).intersection(
    study_rectangle
)

road_metric = transform(project, road_geometry)

if road_metric.is_empty:
    raise RuntimeError("Road geometry is empty after clipping.")

print("Road geometry type:", road_metric.geom_type)

# ==========================================
# 3. LOAD BUSINESSES AND CALCULATE DISTANCES
# ==========================================

df = pd.read_csv(CSV_FILE)

required = ["business_name", "latitude", "longitude"]
missing = [c for c in required if c not in df.columns]

if missing:
    raise ValueError(f"Missing CSV columns: {missing}")

df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
df = df.dropna(subset=["latitude", "longitude"]).copy()

distances = []

for _, row in df.iterrows():
    point = Point(row["longitude"], row["latitude"])
    point_metric = transform(project, point)
    distances.append(road_metric.distance(point_metric))

df["distance_to_road_m"] = distances

# ==========================================
# 4. COMPARE CANDIDATE WIDTHS
# ==========================================

summary = []

for width in WIDTHS:
    included = df["distance_to_road_m"] <= width

    summary.append({
        "width_each_side_m": width,
        "total_width_m": width * 2,
        "business_records_included": int(included.sum()),
        "records_outside": int((~included).sum()),
        "percentage_included": round(
            included.mean() * 100, 2
        ),
    })

summary_df = pd.DataFrame(summary)

print("\nCORRIDOR WIDTH COMPARISON")
print(summary_df.to_string(index=False))

summary_df.to_csv(
    "western_avenue_width_comparison.csv",
    index=False
)

df.to_csv(
    "western_avenue_business_road_distances.csv",
    index=False
)

# Print businesses outside the 100 m buffer
outside = df[df["distance_to_road_m"] > 100]

print("\nBUSINESSES MORE THAN 100 m FROM RETURNED ROAD GEOMETRY")
columns = [
    "business_name",
    "street_address",
    "longitude",
    "latitude",
    "distance_to_road_m",
]

columns = [c for c in columns if c in outside.columns]
print(outside[columns].to_string(index=False))

# ==========================================
# 5. PLOT ROAD, BUSINESSES AND ENDPOINTS
# ==========================================

fig, ax = plt.subplots(figsize=(10, 9))

def draw_lines(geometry, axis):
    if geometry.geom_type == "LineString":
        x, y = geometry.xy
        axis.plot(x, y, color="black", linewidth=2)
    elif hasattr(geometry, "geoms"):
        for part in geometry.geoms:
            draw_lines(part, axis)

draw_lines(road_geometry, ax)

ax.scatter(
    df["longitude"],
    df["latitude"],
    s=12,
    color="royalblue",
    alpha=0.55,
    label="Businesses"
)

ax.scatter(
    [START_LON, END_LON],
    [START_LAT, END_LAT],
    color="red",
    marker="X",
    s=110,
    label="Proposed endpoints"
)

ax.set_title("Western Avenue: Official Street Centerline Check")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.grid(alpha=0.25)
ax.legend()
ax.set_aspect("equal", adjustable="datalim")

plt.tight_layout()
plt.savefig(
    "western_avenue_official_road_check.png",
    dpi=250,
    bbox_inches="tight"
)
plt.close()

# ==========================================
# 6. DISTANCE DISTRIBUTION
# ==========================================

plt.figure(figsize=(10, 6))

plt.hist(
    df["distance_to_road_m"],
    bins=25,
    edgecolor="black"
)

for width in WIDTHS:
    plt.axvline(
        width,
        linestyle="--",
        label=f"{width} m on each side"
    )

plt.title("Business Distance from Returned Western Avenue Geometry")
plt.xlabel("Distance to nearest returned road segment (m)")
plt.ylabel("Business records")
plt.legend()
plt.tight_layout()

plt.savefig(
    "western_avenue_distance_distribution.png",
    dpi=250,
    bbox_inches="tight"
)
plt.close()

print("\nCreated:")
print("- western_avenue_width_comparison.csv")
print("- western_avenue_business_road_distances.csv")
print("- western_avenue_official_road_check.png")
print("- western_avenue_distance_distribution.png")

print(
    "\nIMPORTANT: This query selects Western-named streets "
    "inside a rectangle. It does not yet guarantee that every "
    "line belongs to the exact endpoint-to-endpoint stretch."
)
