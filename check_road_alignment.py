
import geopandas as gpd
import requests
from shapely.geometry import LineString
from shapely.ops import substring

# Load the saved corridor boundary
boundary_gdf = gpd.read_file("western_avenue_final_boundary.geojson")

if boundary_gdf.empty:
    raise ValueError("The saved boundary file is empty.")

boundary = boundary_gdf.to_crs("EPSG:32611").geometry.union_all()

# Official City of Los Angeles road centerline service
url = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

params = {
    "where": "1=1",
    "outFields": "*",
    "returnGeometry": "true",
    "f": "geojson",
    "geometry": "-118.33,34.05,-118.29,34.08",
    "geometryType": "esriGeometryEnvelope",
    "spatialRel": "esriSpatialRelIntersects",
    "inSR": "4326",
    "outSR": "4326",
}

response = requests.get(url, params=params, timeout=60)
response.raise_for_status()

data = response.json()
roads_gdf = gpd.GeoDataFrame.from_features(
    data["features"], crs="EPSG:4326"
)

if roads_gdf.empty:
    raise ValueError("No road features were returned.")

roads_gdf = roads_gdf.to_crs("EPSG:32611")

# Keep features identified as Western Avenue
name_columns = [
    c for c in roads_gdf.columns
    if "STNAME" in c.upper() or "STREET" in c.upper()
]

if name_columns:
    col = name_columns[0]
    mask = roads_gdf[col].astype(str).str.contains(
        "WESTERN", case=False, na=False
    )
    western_roads = roads_gdf[mask].copy()
else:
    western_roads = roads_gdf.copy()
    print("Warning: Street-name field not found; checking all returned roads.")

print("\nROAD ALIGNMENT VERIFICATION")
print("---------------------------")
print("Road features returned:", len(roads_gdf))
print("Western Avenue candidates:", len(western_roads))
print("Saved boundary valid:", boundary.is_valid)
print("Saved boundary area (sq km):", round(boundary.area / 1_000_000, 4))

if western_roads.empty:
    print("No Western Avenue features identified. Inspect road field names.")
    print("Available columns:", list(roads_gdf.columns))
    raise SystemExit

# Measure the fraction of each road feature that lies inside the boundary.
for idx, row in western_roads.iterrows():
    geom = row.geometry

    if geom is None or geom.is_empty:
        continue

    if geom.geom_type == "MultiLineString":
        parts = list(geom.geoms)
    elif geom.geom_type == "LineString":
        parts = [geom]
    else:
        continue

    total_length = sum(part.length for part in parts)
    inside_length = sum(
        part.intersection(boundary).length for part in parts
    )

    if total_length > 0 and inside_length > 0:
        print(
            f"Feature {idx}: "
            f"{inside_length:.1f} m inside / "
            f"{total_length:.1f} m total "
            f"({inside_length / total_length * 100:.1f}%)"
        )

print("\nInterpretation:")
print("- Road overlap confirms that road geometry intersects the boundary.")
print("- Overlap alone does not prove the entire selected stretch is correct.")
print("- Compare the reported features and lengths with the intended 701 m segment.")
