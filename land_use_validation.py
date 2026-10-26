
import json
from pathlib import Path

import requests
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# ======================================================
# 1. SETTINGS
# ======================================================

folder = Path(__file__).resolve().parent

boundary_file = folder / "western_avenue_final_boundary.geojson"
csv_file = folder / "western_avenue_land_use_summary.csv"
map_file = folder / "western_avenue_land_use_map.png"
details_file = folder / "western_avenue_land_use_intersections.csv"

service_url = (
    "https://maps.lacity.org/lahub/rest/services/"
    "City_Planning_Department/MapServer/8"
)
query_url = service_url + "/query"

# ======================================================
# 2. LOAD THE EXISTING CORRIDOR BOUNDARY
# ======================================================

print("Loading Western Avenue corridor boundary...")

if not boundary_file.exists():
    raise FileNotFoundError(f"Missing boundary file: {boundary_file}")

boundary = gpd.read_file(boundary_file)

if boundary.empty or boundary.crs is None:
    raise ValueError("Boundary is empty or its CRS is missing.")

boundary = boundary.to_crs("EPSG:4326")
corridor = boundary.geometry.union_all()

minx, miny, maxx, maxy = boundary.total_bounds

# ======================================================
# 3. CHECK THE CITY ZONING LAYER
# ======================================================

print("Checking official LA generalized zoning layer...")

response = requests.get(
    service_url,
    params={"f": "json"},
    timeout=60
)
response.raise_for_status()

metadata = response.json()

if "error" in metadata:
    raise RuntimeError(f"Zoning metadata error: {metadata['error']}")

print("Layer:", metadata.get("name"))

fields = {
    item["name"]: item
    for item in metadata.get("fields", [])
}

print("Available fields:", list(fields.keys()))

# Prefer a descriptive zoning field.
possible_fields = [
    "ZONING_DESCRIPTION",
    "ZONE_CMPLT",
    "ZONE_CLASS",
    "ZONELEGEND"
]

category_field = next(
    (name for name in possible_fields if name in fields),
    None
)

if category_field is None:
    raise RuntimeError(
        "No recognized zoning-description field was found. "
        "Inspect the field list before continuing."
    )

print("Category field:", category_field)

# ======================================================
# 4. FIND ZONING POLYGONS NEAR THE CORRIDOR
# ======================================================

print("Requesting zoning polygon IDs...")

id_params = {
    "where": "1=1",
    "geometry": json.dumps({
        "xmin": minx,
        "ymin": miny,
        "xmax": maxx,
        "ymax": maxy,
        "spatialReference": {"wkid": 4326}
    }),
    "geometryType": "esriGeometryEnvelope",
    "inSR": 4326,
    "spatialRel": "esriSpatialRelIntersects",
    "returnIdsOnly": "true",
    "f": "json"
}

response = requests.get(
    query_url,
    params=id_params,
    timeout=90
)
response.raise_for_status()

id_data = response.json()

if "error" in id_data:
    raise RuntimeError(f"Zoning ID query failed: {id_data['error']}")

object_ids = id_data.get("objectIds") or []

print("Zoning polygons returned:", len(object_ids))

if not object_ids:
    raise RuntimeError(
        "No zoning polygons found. Check the service and corridor extent."
    )

# ======================================================
# 5. DOWNLOAD POLYGONS IN BATCHES
# ======================================================

print("Downloading zoning polygons...")

features = []
batch_size = 100

for start in range(0, len(object_ids), batch_size):
    batch = object_ids[start:start + batch_size]

    params = {
        "objectIds": ",".join(map(str, batch)),
        "outFields": "*",
        "returnGeometry": "true",
        "outSR": 4326,
        "f": "geojson"
    }

    response = requests.get(
        query_url,
        params=params,
        timeout=90
    )
    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(f"Zoning download error: {data['error']}")

    if "features" not in data:
        raise RuntimeError("The service did not return GeoJSON features.")

    features.extend(data["features"])

    print(
        f"Downloaded {min(start + batch_size, len(object_ids))}"
        f" of {len(object_ids)} polygons"
    )

if not features:
    raise RuntimeError("No zoning polygon geometries were downloaded.")

zoning = gpd.GeoDataFrame.from_features(
    features,
    crs="EPSG:4326"
)

if category_field not in zoning.columns:
    raise RuntimeError(
        f"Downloaded features are missing {category_field}."
    )

zoning = zoning[
    zoning.geometry.notna()
    & ~zoning.geometry.is_empty
].copy()

# Keep only polygons that actually intersect the corridor.
zoning = zoning[
    zoning.geometry.intersects(corridor)
].copy()

if zoning.empty:
    raise RuntimeError("No zoning polygons intersect the corridor.")

# ======================================================
# 6. CLIP ZONING POLYGONS TO THE CORRIDOR
# ======================================================

print("Clipping zoning polygons to the corridor...")

boundary_m = boundary.to_crs("EPSG:32611")
zoning_m = zoning.to_crs("EPSG:32611")

corridor_m = boundary_m.geometry.union_all()
corridor_area_m2 = corridor_m.area

zoning_m["inside_geometry"] = (
    zoning_m.geometry.intersection(corridor_m)
)

zoning_m["inside_area_m2"] = (
    zoning_m["inside_geometry"].area
)

zoning_m = zoning_m[
    zoning_m["inside_area_m2"] > 0
].copy()

zoning_m["category"] = (
    zoning_m[category_field]
    .fillna("Unknown / not specified")
    .astype(str)
    .str.strip()
)

if zoning_m.empty:
    raise RuntimeError("No zoning area remains after clipping.")

# ======================================================
# 7. SUMMARIZE AREA BY ZONING CATEGORY
# ======================================================

print("Calculating area by zoning category...")

summary = (
    zoning_m.groupby("category", dropna=False)["inside_area_m2"]
    .sum()
    .reset_index()
    .sort_values("inside_area_m2", ascending=False)
)

summary["area_km2"] = summary["inside_area_m2"] / 1_000_000

summary["percent_of_corridor"] = (
    100 * summary["inside_area_m2"] / corridor_area_m2
)

summary.insert(0, "corridor_area_km2", corridor_area_m2 / 1_000_000)

summary.to_csv(csv_file, index=False)

# Save individual intersecting polygons for inspection.
details = zoning_m[
    ["category", "inside_area_m2"]
].copy()

details["inside_area_km2"] = details["inside_area_m2"] / 1_000_000
details.to_csv(details_file, index=False)

# ======================================================
# 8. DRAW A LAND-USE / ZONING CONTEXT MAP
# ======================================================

print("Creating zoning map...")

plot_data = gpd.GeoDataFrame(
    zoning_m[["category"]].copy(),
    geometry=zoning_m["inside_geometry"],
    crs=zoning_m.crs
)

fig, ax = plt.subplots(figsize=(12, 9))

plot_data.plot(
    ax=ax,
    column="category",
    categorical=True,
    legend=True,
    legend_kwds={
        "title": "Zoning category",
        "loc": "upper left",
        "fontsize": 7
    },
    edgecolor="white",
    linewidth=0.25,
    alpha=0.85
)

boundary_m.boundary.plot(
    ax=ax,
    color="red",
    linewidth=2,
    label="Selected corridor boundary"
)

ax.set_title(
    "Western Avenue Corridor: Generalized Zoning Context\n"
    "Wilshire Boulevard to West 3rd Street"
)
ax.set_xlabel("Easting (metres)")
ax.set_ylabel("Northing (metres)")
ax.set_aspect("equal")
ax.grid(alpha=0.2)

plt.tight_layout()
plt.savefig(map_file, dpi=200, bbox_inches="tight")
plt.close()

# ======================================================
# 9. PRINT THE RESULTS
# ======================================================

print("\n" + "=" * 60)
print("WESTERN AVENUE ZONING SUMMARY")
print("=" * 60)

print(f"Corridor area: {corridor_area_m2 / 1_000_000:.6f} km²")
print(f"Intersecting zoning polygons: {len(zoning_m)}")
print(f"Zoning category field: {category_field}")

print("\nArea by category:")
print(
    summary[
        ["category", "area_km2", "percent_of_corridor"]
    ].to_string(
        index=False,
        formatters={
            "area_km2": "{:.5f}".format,
            "percent_of_corridor": "{:.2f}%".format
        }
    )
)

print("\nSaved files:")
print(csv_file)
print(details_file)
print(map_file)

print(
    "\nIMPORTANT: Zoning indicates permitted or regulated uses. "
    "It is not a direct survey of the actual current use of every property."
)
