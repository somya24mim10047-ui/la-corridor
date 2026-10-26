
import geopandas as gpd
import requests
from shapely.geometry import Point

# Load the saved boundary
boundary_gdf = gpd.read_file("western_avenue_final_boundary.geojson")
boundary = boundary_gdf.to_crs("EPSG:32611").geometry.union_all()

# Query the official LA road centerline service
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
    "resultRecordCount": 2000,
}

response = requests.get(url, params=params, timeout=60)
response.raise_for_status()
data = response.json()

roads = gpd.GeoDataFrame.from_features(
    data["features"], crs="EPSG:4326"
).to_crs("EPSG:32611")

print("Available fields:", list(roads.columns))

# Find the street-name field
name_col = next(
    (c for c in roads.columns
     if "STNAME" in c.upper() or "STREET" in c.upper()),
    None
)

if name_col is None:
    print("Could not identify the street-name field.")
    raise SystemExit

western = roads[
    roads[name_col].astype(str).str.contains(
        "WESTERN", case=False, na=False
    )
].copy()

# Convert the two endpoints to metres
start = gpd.GeoSeries(
    [Point(-118.308881, 34.062100)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

end = gpd.GeoSeries(
    [Point(-118.309011, 34.068419)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

print("\nWESTERN AVENUE SEGMENT DETAILS")
print("--------------------------------")

for idx, row in western.iterrows():
    geom = row.geometry

    if geom is None or geom.is_empty:
        continue

    length_m = geom.length
    start_distance = geom.distance(start)
    end_distance = geom.distance(end)
    inside_m = geom.intersection(boundary).length

    # Print only segments near the endpoints or overlapping the boundary
    if (
        start_distance < 250
        or end_distance < 250
        or inside_m > 0
    ):
        print(
            f"Feature {idx}: "
            f"length={length_m:.1f} m, "
            f"start_distance={start_distance:.1f} m, "
            f"end_distance={end_distance:.1f} m, "
            f"inside_boundary={inside_m:.1f} m"
        )

print("\nNumber of Western Avenue features:", len(western))
print("Saved boundary area (sq km):",
      round(boundary.area / 1_000_000, 4))
