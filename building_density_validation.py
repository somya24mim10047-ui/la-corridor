

import json
import requests
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# =========================================================
# 1. PROJECT PATHS AND SETTINGS
# =========================================================

folder = Path(__file__).resolve().parent

boundary_path = folder / "western_avenue_final_boundary.geojson"
csv_path = folder / "western_avenue_building_density.csv"
map_path = folder / "western_avenue_building_density.png"

# Alternate City of Los Angeles Landbase service
base_url = (
    "https://maps.lacity.org/lahub/rest/services/"
    "Landbase_Information/MapServer/9"
)

query_url = f"{base_url}/query"

# =========================================================
# 2. LOAD THE EXISTING CORRIDOR BOUNDARY
# =========================================================

print("Loading Western Avenue corridor boundary...")

if not boundary_path.exists():
    raise FileNotFoundError(
        f"Boundary file not found: {boundary_path}"
    )

boundary = gpd.read_file(boundary_path)

if boundary.empty:
    raise ValueError("The corridor boundary file is empty.")

if boundary.crs is None:
    raise ValueError(
        "The boundary has no CRS. Check its GeoJSON metadata."
    )

boundary = boundary.to_crs("EPSG:4326")
corridor = boundary.geometry.union_all()

minx, miny, maxx, maxy = boundary.total_bounds

# =========================================================
# 3. CHECK THE ALTERNATE SERVICE METADATA
# =========================================================

print("Checking the alternate LA building-footprint layer...")

metadata_response = requests.get(
    base_url,
    params={"f": "json"},
    timeout=60
)
metadata_response.raise_for_status()

metadata = metadata_response.json()

if "error" in metadata:
    raise RuntimeError(
        f"Layer metadata error: {metadata['error']}"
    )

print("Layer name:", metadata.get("name"))
print("Geometry type:", metadata.get("geometryType"))

fields = {
    field["name"]: field
    for field in metadata.get("fields", [])
}

# Inspect the actual category field rather than assuming
# the alternate layer uses the same schema as the old layer.
print("Available fields:", list(fields.keys()))

category_field = None

for candidate in ["CODE", "CODE_NUM"]:
    if candidate in fields:
        category_field = candidate
        break

if category_field is None:
    raise RuntimeError(
        "Could not find CODE or CODE_NUM in layer metadata. "
        "Inspect the layer fields before calculating density."
    )

print("Category field:", category_field)

# =========================================================
# 4. REQUEST FEATURES INTERSECTING THE CORRIDOR
# =========================================================

print("Requesting building IDs from the alternate LA service...")

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

id_result = response.json()

if "error" in id_result:
    raise RuntimeError(
        f"Feature ID query failed: {id_result['error']}"
    )

object_ids = id_result.get("objectIds") or []

print("Feature IDs returned:", len(object_ids))

if not object_ids:
    raise RuntimeError(
        "No feature IDs returned for the corridor area."
    )

# =========================================================
# 5. DOWNLOAD FEATURES IN BATCHES
# =========================================================

print("Downloading feature geometries...")

features = []
batch_size = 100

out_fields = ",".join(
    name for name in [
        "OBJECTID",
        category_field,
        "HEIGHT",
        "BLD_ID"
    ]
    if name in fields
)

for start in range(0, len(object_ids), batch_size):
    batch = object_ids[start:start + batch_size]

    params = {
        "objectIds": ",".join(map(str, batch)),
        "outFields": out_fields or "*",
        "returnGeometry": "true",
        "outSR": 4326,
        "f": "geojson"
    }

    batch_response = requests.get(
        query_url,
        params=params,
        timeout=90
    )
    batch_response.raise_for_status()

    batch_data = batch_response.json()

    if "error" in batch_data:
        raise RuntimeError(
            f"Feature download failed: {batch_data['error']}"
        )

    if "features" not in batch_data:
        raise RuntimeError(
            "The server did not return GeoJSON features."
        )

    features.extend(batch_data["features"])

    print(
        f"Downloaded {min(start + batch_size, len(object_ids))}"
        f" of {len(object_ids)} features..."
    )

if not features:
    raise RuntimeError("No building geometries were downloaded.")

buildings = gpd.GeoDataFrame.from_features(
    features,
    crs="EPSG:4326"
)

if category_field not in buildings.columns:
    raise RuntimeError(
        f"Downloaded data is missing {category_field}."
    )

# =========================================================
# 6. INSPECT CATEGORIES AND EXCLUDE COURTYARDS
# =========================================================

print("\nFeature categories returned by the service:")
print(buildings[category_field].value_counts(dropna=False).to_string())

# Category values can differ between services.
# Exclude only categories explicitly identified as courtyards.
category_values = (
    buildings[category_field]
    .astype("string")
    .str.strip()
    .str.lower()
)

courtyard_mask = category_values.str.contains(
    "courtyard",
    na=False
)

# Some services encode categories numerically.
# For CODE_NUM, the known old-layer convention is:
# 1 = building, 2 = courtyard.
if category_field == "CODE_NUM":
    courtyard_mask = (
        pd.to_numeric(buildings[category_field], errors="coerce") == 2
    )

buildings = buildings.loc[~courtyard_mask].copy()

# Drop missing and empty geometries.
buildings = buildings[
    buildings.geometry.notna()
    & ~buildings.geometry.is_empty
].copy()

# Keep polygons that actually intersect the corridor.
buildings = buildings[
    buildings.geometry.intersects(corridor)
].copy()

if buildings.empty:
    raise RuntimeError(
        "No usable polygon features remain after filtering. "
        "Review the printed category values before proceeding."
    )

# =========================================================
# 7. CALCULATE AREA IN A PROJECTED CRS
# =========================================================

print("\nCalculating building footprint coverage...")

# UTM Zone 11N is suitable for Los Angeles area calculations.
boundary_m = boundary.to_crs("EPSG:32611")
buildings_m = buildings.to_crs("EPSG:32611")

corridor_m = boundary_m.geometry.union_all()
corridor_area_m2 = corridor_m.area
corridor_area_km2 = corridor_area_m2 / 1_000_000

# Clip each polygon to the corridor before calculating area.
buildings_m["inside_geometry"] = (
    buildings_m.geometry.intersection(corridor_m)
)

buildings_m["inside_area_m2"] = (
    buildings_m["inside_geometry"].area
)

# Remove polygons with no positive area inside the corridor.
buildings_m = buildings_m[
    buildings_m["inside_area_m2"] > 0
].copy()

building_count = len(buildings_m)
total_footprint_area_m2 = buildings_m["inside_area_m2"].sum()

buildings_per_km2 = (
    building_count / corridor_area_km2
    if corridor_area_km2 > 0 else 0
)

footprint_coverage_pct = (
    100 * total_footprint_area_m2 / corridor_area_m2
    if corridor_area_m2 > 0 else 0
)

# =========================================================
# 8. SAVE THE SUMMARY CSV
# =========================================================

summary = pd.DataFrame([{
    "corridor_area_km2": corridor_area_km2,
    "building_count_intersecting_corridor": building_count,
    "buildings_per_km2": buildings_per_km2,
    "building_footprint_area_m2": total_footprint_area_m2,
    "footprint_coverage_percent": footprint_coverage_pct,
    "data_source": (
        "City of Los Angeles Landbase_Information MapServer Layer 9"
    ),
    "category_field": category_field
}])

summary.to_csv(csv_path, index=False)

# =========================================================
# 9. CREATE THE BUILDING-DENSITY MAP
# =========================================================

print("Creating the building-density map...")

fig, ax = plt.subplots(figsize=(10, 9))

# Plot footprints clipped to the boundary.
footprints = gpd.GeoDataFrame(
    geometry=buildings_m["inside_geometry"],
    crs=buildings_m.crs
)

if not footprints.empty:
    footprints.plot(
        ax=ax,
        color="steelblue",
        edgecolor="white",
        linewidth=0.25
    )

boundary_m.boundary.plot(
    ax=ax,
    color="red",
    linewidth=2
)

ax.set_title(
    "Western Avenue Corridor: Building Footprints\n"
    "Wilshire Boulevard to West 3rd Street"
)
ax.set_xlabel("Easting (metres)")
ax.set_ylabel("Northing (metres)")
ax.set_aspect("equal")
ax.grid(alpha=0.2)

plt.tight_layout()
plt.savefig(
    map_path,
    dpi=200,
    bbox_inches="tight"
)
plt.close()

# =========================================================
# 10. DISPLAY FINAL RESULTS
# =========================================================

print("\n" + "=" * 55)
print("WESTERN AVENUE BUILDING DENSITY RESULTS")
print("=" * 55)

print(f"Corridor area:              {corridor_area_km2:.6f} km²")
print(f"Building footprints:        {building_count}")
print(f"Buildings per km²:          {buildings_per_km2:.2f}")
print(f"Footprint area:             {total_footprint_area_m2:.2f} m²")
print(f"Footprint coverage:         {footprint_coverage_pct:.2f}%")
print(f"Category field:             {category_field}")

print("\nSaved files:")
print(csv_path)
print(map_path)

print("\nNote: Review the printed category values to ensure")
print("the alternate service's building/courtyard coding")
print("is understood before presenting the final figures.")
