
import requests
import geopandas as gpd
from shapely.geometry import Point

url = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

# Search a small area around the intended Wilshire endpoint.
lon, lat = -118.308881, 34.062100

params = {
    "where": "1=1",
    "outFields": "OBJECTID,STNAME,STSFX,ADRF,ADRT,INT_ID_FROM,INT_ID_TO",
    "returnGeometry": "true",
    "geometry": f"{lon-0.0015},{lat-0.0015},{lon+0.0015},{lat+0.0015}",
    "geometryType": "esriGeometryEnvelope",
    "inSR": 4326,
    "spatialRel": "esriSpatialRelIntersects",
    "outSR": 4326,
    "f": "geojson",
    "resultRecordCount": 2000,
}

response = requests.get(url, params=params, timeout=60)
response.raise_for_status()
features = response.json().get("features", [])

if not features:
    raise RuntimeError("No nearby roads returned from the official service.")

roads = gpd.GeoDataFrame.from_features(
    features, crs="EPSG:4326"
).to_crs("EPSG:32611")

target = gpd.GeoSeries(
    [Point(lon, lat)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

roads["distance_m"] = roads.geometry.distance(target)
roads = roads.sort_values("distance_m")

print("\nNEARBY OFFICIAL ROADS")
print("=====================")

for _, row in roads.head(25).iterrows():
    name = str(row.get("STNAME", ""))
    suffix = str(row.get("STSFX", ""))
    full_name = f"{name} {suffix}".strip()

    print(
        f"{row['distance_m']:6.1f} m | "
        f"{full_name:30} | "
        f"addresses {row.get('ADRF')}–{row.get('ADRT')} | "
        f"intersections {row.get('INT_ID_FROM')} -> "
        f"{row.get('INT_ID_TO')}"
    )
