
import geopandas as gpd
import requests
from shapely.geometry import Point

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

roads = gpd.GeoDataFrame.from_features(
    response.json()["features"], crs="EPSG:4326"
).to_crs("EPSG:32611")

start = gpd.GeoSeries(
    [Point(-118.308881, 34.062100)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

end = gpd.GeoSeries(
    [Point(-118.309011, 34.068419)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

name_col = next(
    (c for c in roads.columns
     if "STNAME" in c.upper() or "STREET" in c.upper()),
    None
)

if name_col is None:
    print("Street-name field not found.")
    print("Available fields:", list(roads.columns))
    raise SystemExit

western = roads[
    roads[name_col].astype(str).str.contains(
        "WESTERN", case=False, na=False
    )
]

print("Available fields:", list(roads.columns))
print("\nNEARBY WESTERN AVENUE RECORDS")

for idx, row in western.iterrows():
    geom = row.geometry
    if geom is None or geom.is_empty:
        continue

    d_start = geom.distance(start)
    d_end = geom.distance(end)

    if min(d_start, d_end) < 100:
        print(f"\nRecord index: {idx}")
        print(f"Distance to start: {d_start:.1f} m")
        print(f"Distance to end: {d_end:.1f} m")
        print(f"Geometry type: {geom.geom_type}")
        print(f"Length: {geom.length:.1f} m")

        for col in western.columns:
            if col != "geometry":
                print(f"{col}: {row[col]}")

        print("First coordinate:", list(geom.coords)[0]
              if geom.geom_type == "LineString" else "Multipart")
        print("Last coordinate:", list(geom.coords)[-1]
              if geom.geom_type == "LineString" else "Multipart")
