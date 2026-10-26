
import requests
import geopandas as gpd
from shapely.geometry import Point

URL = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

params = {
    "where": "OBJECTID IN (137008,141603)",
    "outFields": "OBJECTID,STNAME,STSFX,ADRF,ADRT,INT_ID_FROM,INT_ID_TO",
    "returnGeometry": "true",
    "outSR": 4326,
    "f": "geojson",
}

response = requests.get(URL, params=params, timeout=60)
response.raise_for_status()

features = response.json().get("features", [])
if len(features) != 2:
    raise RuntimeError(f"Expected 2 road segments; received {len(features)}.")

roads = gpd.GeoDataFrame.from_features(
    features, crs="EPSG:4326"
).to_crs("EPSG:32611")

print("\nCORRIDOR ENDPOINT CHECK")
print("=======================")

for _, row in roads.sort_values("OBJECTID").iterrows():
    geom = row.geometry
    coords = list(geom.coords)

    print(f"\nOBJECTID: {int(row['OBJECTID'])}")
    print(f"Street: {row['STNAME']} {row['STSFX']}")
    print(f"Intersection IDs: {row['INT_ID_FROM']} -> {row['INT_ID_TO']}")
    print(f"Address range: {row['ADRF']} - {row['ADRT']}")

    for label, coord in [
        ("First geometry endpoint", coords[0]),
        ("Last geometry endpoint", coords[-1]),
    ]:
        point = gpd.GeoSeries(
            [Point(coord)], crs="EPSG:32611"
        ).to_crs("EPSG:4326").iloc[0]

        print(
            f"{label}: longitude={point.x:.6f}, "
            f"latitude={point.y:.6f}"
        )

print("\nUse these coordinates to verify the intended intersections.")
