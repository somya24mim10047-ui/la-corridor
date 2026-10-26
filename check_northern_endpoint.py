
import requests
import geopandas as gpd
from shapely.geometry import Point

SERVICE_URL = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

# Current northern endpoint of the saved centerline.
centerline = gpd.read_file(
    "western_avenue_centerline.geojson"
).to_crs("EPSG:32611")

line = centerline.geometry.iloc[0]
endpoint = line.interpolate(line.length)

endpoint_wgs84 = gpd.GeoSeries(
    [endpoint],
    crs="EPSG:32611",
).to_crs("EPSG:4326").iloc[0]

print("Current centerline endpoint:")
print(f"Longitude: {endpoint_wgs84.x:.8f}")
print(f"Latitude:  {endpoint_wgs84.y:.8f}")

# Search the official road network near the endpoint.
params = {
    "where": "1=1",
    "geometry": (
        f"{endpoint_wgs84.x - 0.001},"
        f"{endpoint_wgs84.y - 0.001},"
        f"{endpoint_wgs84.x + 0.001},"
        f"{endpoint_wgs84.y + 0.001}"
    ),
    "geometryType": "esriGeometryEnvelope",
    "inSR": 4326,
    "spatialRel": "esriSpatialRelIntersects",
    "outFields": "OBJECTID,STNAME,STSFX,ADRF,ADRT,INT_ID_FROM,INT_ID_TO",
    "returnGeometry": "false",
    "f": "json",
}

response = requests.get(
    SERVICE_URL,
    params=params,
    timeout=60,
)
response.raise_for_status()

data = response.json()

if "error" in data:
    raise RuntimeError(data["error"])

features = data.get("features", [])

if not features:
    print("No road records found near the endpoint.")
else:
    print("\nOfficial road records near the endpoint:")
    for feature in features:
        print(feature["attributes"])
