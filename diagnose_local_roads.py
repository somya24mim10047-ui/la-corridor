
from pathlib import Path

import requests
import pandas as pd
from shapely.geometry import Point, shape, box
from shapely.ops import transform
from pyproj import Transformer

ROAD_API = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

PROJECT = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
).transform

CASES = [
    ("VERMONT", "ELENA L GARCIA", 34.0761, -118.3031),
    ("OLYMPIC", "SJ INVESTMENT 2020 LLC", 34.0487, -118.3362),
    (
        "OLYMPIC",
        "LOS ANGELES HIGH SCHOOL ALUMNI ASSOCIATION",
        34.0551,
        -118.3328,
    ),
    ("WESTERN", "NIPONG NAEPONG CMP INC", 34.0663, -118.3107),
]


def inspect_point(expected_road, business, lat, lon):
    print("\n" + "=" * 75)
    print(f"Business: {business}")
    print(f"Expected road: {expected_road}")
    print(f"Coordinates: {lat}, {lon}")

    # Search a small local area around the business.
    # 0.005 degrees is roughly 500 metres in this area.
    extent = box(
        lon - 0.005,
        lat - 0.005,
        lon + 0.005,
        lat + 0.005,
    )

    params = {
        "where": "1=1",
        "geometry": (
            f"{extent.bounds[0]},{extent.bounds[1]},"
            f"{extent.bounds[2]},{extent.bounds[3]}"
        ),
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": (
            "OBJECTID,STNAME,STSFX,SFXDIR,STNAME_A,"
            "ADRF,ADRT,ADLF,ADLT"
        ),
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }

    try:
        response = requests.get(
            ROAD_API,
            params=params,
            timeout=60,
            headers={"User-Agent": "LA-Corridor-Research/1.0"},
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        print("Request failed:", exc)
        return

    if "error" in data:
        print("API error:", data["error"])
        return

    features = data.get("features", [])
    print("Local road features returned:", len(features))
    print("Transfer limit exceeded:", data.get("exceededTransferLimit", False))

    point = transform(PROJECT, Point(lon, lat))
    candidates = []

    for feature in features:
        geometry_data = feature.get("geometry")
        if not geometry_data:
            continue

        geom = shape(geometry_data)
        if geom.geom_type not in ("LineString", "MultiLineString"):
            continue

        road = transform(PROJECT, geom)
        attrs = feature.get("properties", {})

        candidates.append({
            "distance_m": round(point.distance(road), 2),
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
        print("No nearby road lines found.")
        return

    nearest = pd.DataFrame(candidates).sort_values("distance_m")
    print("\nNearest local road segments:")
    print(nearest.head(10).to_string(index=False))

    matching = nearest[
        nearest["STNAME"].fillna("").str.contains(
            expected_road, case=False, regex=False
        )
    ]

    print(f"\nNearest {expected_road} segment:")
    if matching.empty:
        print("No matching named segment in the local search area.")
    else:
        print(matching.head(3).to_string(index=False))


def main():
    for case in CASES:
        inspect_point(*case)


if __name__ == "__main__":
    main()
