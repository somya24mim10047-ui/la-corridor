
from pathlib import Path
import time
import requests
import pandas as pd

from shapely.geometry import LineString, MultiLineString, Point, shape
from shapely.ops import unary_union, transform
from pyproj import Transformer

BASE = Path(__file__).parent
INPUT_DIR = BASE / "data" / "corridors"
OUTPUT_DIR = BASE / "data" / "validation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Official City of Los Angeles street centerline service
ROAD_API = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

CORRIDORS = {
    "western_avenue": {
        "road_name": "WESTERN",
        "file": BASE / "western_avenue_businesses.csv",
    },
    "wilshire_boulevard": {
        "road_name": "WILSHIRE",
        "file": INPUT_DIR / "wilshire_boulevard_businesses.csv",
    },
    "olympic_boulevard": {
        "road_name": "OLYMPIC",
        "file": INPUT_DIR / "olympic_boulevard_businesses.csv",
    },
    "vermont_avenue": {
        "road_name": "VERMONT",
        "file": INPUT_DIR / "vermont_avenue_businesses.csv",
    },
    "larchmont_boulevard": {
        "road_name": "LARCHMONT",
        "file": INPUT_DIR / "larchmont_boulevard_businesses.csv",
    },
}

# Geographic coordinates -> metres in the Los Angeles area
project = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
).transform


def fetch_road_geometry(road_name):
    params = {
        "where": f"STNAME LIKE '%{road_name}%'",
        "outFields": "STNAME,STSFX,SFXDIR",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }

    response = requests.get(
        ROAD_API,
        params=params,
        timeout=60,
        headers={"User-Agent": "LA-Corridor-Research/1.0"},
    )
    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    features = data.get("features", [])
    lines = []

    for feature in features:
        geometry_data = feature.get("geometry")

        if not geometry_data:
            continue

        geom = shape(geometry_data)

        if geom.geom_type == "LineString":
            lines.append(transform(project, geom))

        elif geom.geom_type == "MultiLineString":
            lines.append(transform(project, geom))

        elif geom.geom_type == "GeometryCollection":
            for part in geom.geoms:
                if part.geom_type in (
                    "LineString", "MultiLineString"
                ):
                    lines.append(transform(project, part))

    if not lines:
        raise RuntimeError(
            f"No road lines found for {road_name}. "
            "Check the road name or GIS service."
        )

    print(f"Road features retrieved: {len(lines)}")
    return unary_union(lines)


def validate_corridor(corridor, config):
    print(f"\nValidating {corridor}...")

    file = config["file"]

    if not file.exists():
        print(f"Skipped: missing file {file}")
        return None

    df = pd.read_csv(file)

    required = {"latitude", "longitude"}
    if not required.issubset(df.columns):
        print("Skipped: latitude/longitude columns missing.")
        return None

    df["latitude"] = pd.to_numeric(
        df["latitude"], errors="coerce"
    )
    df["longitude"] = pd.to_numeric(
        df["longitude"], errors="coerce"
    )

    df = df.dropna(
        subset=["latitude", "longitude"]
    ).copy()

    df = df[
        df["latitude"].between(-90, 90)
        & df["longitude"].between(-180, 180)
    ].copy()

    if df.empty:
        print("Skipped: no valid coordinates.")
        return None

    road = fetch_road_geometry(config["road_name"])

    # Measure each business point's distance to the named road.
    points = [
        transform(project, Point(lon, lat))
        for lon, lat in zip(df["longitude"], df["latitude"])
    ]

    df["road_distance_m"] = [
        point.distance(road) for point in points
    ]
    df["within_25m"] = df["road_distance_m"] <= 25
    df["within_50m"] = df["road_distance_m"] <= 50

    unique = df.drop_duplicates(
        subset=["latitude", "longitude"]
    )

    output = OUTPUT_DIR / f"{corridor}_road_validation.csv"
    df.to_csv(output, index=False)

    result = {
        "corridor": corridor,
        "business_records": len(df),
        "unique_locations": len(unique),
        "median_road_distance_m": round(
            float(df["road_distance_m"].median()), 2
        ),
        "unique_locations_within_25m": int(
            (unique["road_distance_m"] <= 25).sum()
        ),
        "unique_locations_within_50m": int(
            (unique["road_distance_m"] <= 50).sum()
        ),
        "road_source": "City of Los Angeles street centerlines",
    }

    print(
        "Median road distance:",
        result["median_road_distance_m"], "m"
    )
    print(
        "Unique locations within 25 m:",
        result["unique_locations_within_25m"],
        "/", len(unique)
    )
    print(
        "Unique locations within 50 m:",
        result["unique_locations_within_50m"],
        "/", len(unique)
    )
    print("Saved:", output)

    return result


def main():
    results = []

    for corridor, config in CORRIDORS.items():
        try:
            result = validate_corridor(corridor, config)

            if result is not None:
                results.append(result)

        except Exception as error:
            print(f"FAILED {corridor}: {error}")

        time.sleep(1)

    if not results:
        print(
            "\nNo corridors validated. Check the GIS service "
            "or network connection."
        )
        return

    summary = pd.DataFrame(results)
    summary_path = OUTPUT_DIR / "road_alignment_summary.csv"
    summary.to_csv(summary_path, index=False)

    print("\n=== ROAD ALIGNMENT SUMMARY ===")
    print(summary.to_string(index=False))
    print("\nSaved:", summary_path)


if __name__ == "__main__":
    main()

