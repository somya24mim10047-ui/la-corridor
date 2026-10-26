
import requests
import pandas as pd
from shapely.geometry import Point, shape
from shapely.ops import transform
from pyproj import Transformer

ROAD_API = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

project = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
).transform

cases = [
    ("VERMONT", "ELENA L GARCIA", 34.0761, -118.3031),
    ("OLYMPIC", "SJ INVESTMENT 2020 LLC", 34.0487, -118.3362),
    ("OLYMPIC", "LOS ANGELES HIGH SCHOOL ALUMNI ASSOCIATION",
     34.0551, -118.3328),
    ("WESTERN", "NIPONG NAEPONG CMP INC", 34.0663, -118.3107),
]

for road_name, business, lat, lon in cases:
    print(f"\n{'=' * 65}")
    print(f"Business: {business}")
    print(f"Coordinates: {lat}, {lon}")
    print(f"Requested street: {road_name}")

    params = {
        "where": f"STNAME LIKE '%{road_name}%'",
        "outFields": (
            "OBJECTID,STNAME,STSFX,SFXDIR,STNAME_A,"
            "ADRF,ADRT,ADLF,ADLT"
        ),
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }

    response = requests.get(ROAD_API, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        print("API ERROR:", data["error"])
        continue

    features = data.get("features", [])
    print("Returned road features:", len(features))

    point = transform(project, Point(lon, lat))
    candidates = []

    for feature in features:
        geometry_data = feature.get("geometry")
        if not geometry_data:
            continue

        road = transform(project, shape(geometry_data))
        distance = point.distance(road)
        attrs = feature.get("properties", {})

        candidates.append({
            "distance_m": round(distance, 2),
            "OBJECTID": attrs.get("OBJECTID"),
            "STNAME": attrs.get("STNAME"),
            "STSFX": attrs.get("STSFX"),
            "SFXDIR": attrs.get("SFXDIR"),
            "STNAME_A": attrs.get("STNAME_A"),
            "ADRF": attrs.get("ADRF"),
            "ADRT": attrs.get("ADRT"),
            "ADLF": attrs.get("ADLF"),
            "ADLT": attrs.get("ADLT"),
        })

    if not candidates:
        print("No usable road geometries returned.")
        continue

    nearest = pd.DataFrame(candidates).sort_values("distance_m")
    print(nearest.head(5).to_string(index=False))
