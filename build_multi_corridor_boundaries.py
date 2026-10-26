
from pathlib import Path
import requests
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape

BASE = Path(__file__).parent
DATA_DIR = BASE / "data" / "corridors"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Search extents: south, west, north, east.
# These are retrieval areas, not final corridor boundaries.
CORRIDORS = {
    "wilshire_boulevard": (34.050, -118.350, 34.075, -118.275),
    "olympic_boulevard": (34.035, -118.350, 34.060, -118.275),
    "vermont_avenue": (34.040, -118.305, 34.085, -118.285),
    "larchmont_boulevard": (34.060, -118.335, 34.085, -118.305),
}

URL = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

for name, (south, west, north, east) in CORRIDORS.items():
    print(f"\nFetching official road geometry for {name}...")

    params = {
        "where": "1=1",
        "outFields": "OBJECTID,STNAME,STSFX,ADRF,ADRT",
        "returnGeometry": "true",
        "geometry": f"{west},{south},{east},{north}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outSR": 4326,
        "f": "geojson",
        "resultRecordCount": 2000,
    }

    try:
        response = requests.get(URL, params=params, timeout=90)
        response.raise_for_status()
        payload = response.json()
        features = payload.get("features", [])

        # Keep only features whose street name matches the corridor.
        matched = []
        keyword = {
            "wilshire_boulevard": "WILSHIRE",
            "olympic_boulevard": "OLYMPIC",
            "vermont_avenue": "VERMONT",
            "larchmont_boulevard": "LARCHMONT",
        }[name]

        for feature in features:
            props = feature.get("properties", {})
            street = str(props.get("STNAME") or "").upper()
            if keyword not in street:
                continue

            geom = feature.get("geometry")
            if geom:
                matched.append({
                    **props,
                    "geometry": shape(geom),
                })

        if not matched:
            print(
                "No matching street segments returned. "
                "Check the service or street-name fields."
            )
            continue

        roads = gpd.GeoDataFrame(matched, geometry="geometry", crs="EPSG:4326")
        output = DATA_DIR / f"{name}_road_segments.geojson"
        roads.to_file(output, driver="GeoJSON")

        print(f"Matching street segments: {len(roads)}")
        print(f"Saved: {output}")

    except Exception as error:
        print(f"FAILED for {name}: {error}")

print("\nRoad geometry retrieval finished.")
print("These are road segments, not validated final corridor boundaries.")
