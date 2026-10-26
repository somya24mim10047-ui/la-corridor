
import requests
import geopandas as gpd
from shapely.geometry import shape, Point

OBJECTIDS = [124436, 84883, 134991, 141603]

url = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

params = {
    "where": "OBJECTID IN (124436,84883,134991,141603)",
    "outFields": "*",
    "returnGeometry": "true",
    "outSR": 4326,
    "f": "geojson",
}

response = requests.get(url, params=params, timeout=60)
response.raise_for_status()

features = response.json().get("features", [])
if not features:
    raise RuntimeError("No candidate road records were returned.")

roads = gpd.GeoDataFrame.from_features(
    features, crs="EPSG:4326"
).to_crs("EPSG:32611")

start = gpd.GeoSeries(
    [Point(-118.308881, 34.062100)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

end = gpd.GeoSeries(
    [Point(-118.309011, 34.068419)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

print("\nCANDIDATE GEOMETRY CHECK")
print("------------------------")

for _, row in roads.sort_values("OBJECTID").iterrows():
    geom = row.geometry

    print(f"\nOBJECTID: {row['OBJECTID']}")
    print(f"Intersection IDs: {row['INT_ID_FROM']} -> {row['INT_ID_TO']}")
    print(f"Address range: {row['ADRF']} - {row['ADRT']}")
    print(f"Geometry type: {geom.geom_type}")
    print(f"Length: {geom.length:.1f} m")
    print(f"Distance to start endpoint: {geom.distance(start):.1f} m")
    print(f"Distance to end endpoint: {geom.distance(end):.1f} m")

    if geom.geom_type == "LineString":
        coords = list(geom.coords)
        print("First coordinate (metres):", tuple(round(v, 2) for v in coords[0]))
        print("Last coordinate (metres):", tuple(round(v, 2) for v in coords[-1]))

print("\nCompare neighbouring feature endpoints.")
print("Connected intersection IDs should meet at matching coordinates.")
