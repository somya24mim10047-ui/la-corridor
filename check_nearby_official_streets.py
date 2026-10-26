
from pathlib import Path
import requests
import pandas as pd
import geopandas as gpd

BASE = Path(__file__).resolve().parent
AUDIT = BASE / "data" / "boundary_candidates" / "all_corridor_audit"

URL = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

FILES = [
    "wilshire_boulevard_outside_150m.csv",
    "olympic_boulevard_outside_100m.csv",
    "vermont_avenue_outside_100m.csv",
]

def query(params):
    r = requests.get(URL, params=params, timeout=90)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data

for filename in FILES:
    df = pd.read_csv(AUDIT / filename)
    print(f"\n{'=' * 15} {filename} {'=' * 15}")

    for _, business in df.iterrows():
        lon = float(business["longitude"])
        lat = float(business["latitude"])
        radius = 0.015  # roughly 1–1.5 km; diagnostic search only

        params = {
            "geometry": (
                f"{lon-radius},{lat-radius},"
                f"{lon+radius},{lat+radius}"
            ),
            "geometryType": "esriGeometryEnvelope",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "OBJECTID,STNAME,STSFX,ADRF,ADRT",
            "returnGeometry": "true",
            "returnIdsOnly": "true",
            "f": "json",
        }

        result = query(params)
        ids = result.get("objectIds") or []
        features = []

        for start in range(0, len(ids), 100):
            batch = ids[start:start + 100]
            part = query({
                "objectIds": ",".join(map(str, batch)),
                "outFields": "OBJECTID,STNAME,STSFX,ADRF,ADRT",
                "returnGeometry": "true",
                "outSR": 4326,
                "f": "geojson",
            })
            features.extend(part.get("features", []))

        print(f"\nBusiness: {business['business_name']}")
        print(f"Address: {business['street_address']}")
        print(f"Coordinates: {lat}, {lon}")

        if not features:
            print("No nearby official street segments returned.")
            continue

        roads = gpd.GeoDataFrame.from_features(
            features, crs="EPSG:4326"
        )
        roads = roads[roads.geometry.notna()].to_crs("EPSG:32611")

        point = gpd.GeoSeries(
            gpd.points_from_xy([lon], [lat]), crs="EPSG:4326"
        ).to_crs("EPSG:32611").iloc[0]

        roads["distance_m"] = roads.geometry.distance(point)
        roads = roads.sort_values("distance_m").head(5)

        cols = [
            c for c in [
                "STNAME", "STSFX", "ADRF", "ADRT", "distance_m"
            ] if c in roads.columns
        ]
        print(roads[cols].to_string(index=False))

print("\nNearby-street check complete. No project files modified.")
