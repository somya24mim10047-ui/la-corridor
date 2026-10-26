
from pathlib import Path

import geopandas as gpd
import pandas as pd

BASE = Path(__file__).resolve().parent
ROAD_DIR = BASE / "data" / "corridors"
OUTPUT_DIR = BASE / "data" / "boundary_candidates"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIG = {
    "wilshire_boulevard": {
        "business_file": "wilshire_boulevard_businesses.csv",
        "street": "WILSHIRE",
        "suffix": "BLVD",
    },
    "olympic_boulevard": {
        "business_file": "olympic_boulevard_businesses.csv",
        "street": "OLYMPIC",
        "suffix": "BLVD",
    },
    "vermont_avenue": {
        "business_file": "vermont_avenue_businesses.csv",
        "street": "VERMONT",
        "suffix": "AVE",
    },
    "larchmont_boulevard": {
        "business_file": "larchmont_boulevard_businesses.csv",
        "street": "LARCHMONT",
        "suffix": "BLVD",
    },
}

METRIC_CRS = "EPSG:32611"
results = []

for corridor, config in CONFIG.items():
    print(f"\n--- {corridor.upper()} ---")

    road_path = ROAD_DIR / f"{corridor}_road_segments.geojson"
    business_path = ROAD_DIR / config["business_file"]

    if not road_path.exists() or not business_path.exists():
        print("SKIPPED: road or business file is missing.")
        continue

    roads = gpd.read_file(road_path)

    if not {"STNAME", "STSFX"}.issubset(roads.columns):
        print("SKIPPED: official street-name fields are missing.")
        continue

    # Retain only the exact intended street name and suffix.
    mask = (
        roads["STNAME"].astype(str).str.strip().str.upper()
        .eq(config["street"])
        & roads["STSFX"].astype(str).str.strip().str.upper()
        .eq(config["suffix"])
    )

    clean_roads = roads.loc[mask].copy()
    clean_roads = clean_roads[
        clean_roads.geometry.notna()
        & ~clean_roads.geometry.is_empty
    ]

    if clean_roads.empty:
        print("SKIPPED: no matching road features.")
        continue

    if clean_roads.crs is None:
        clean_roads = clean_roads.set_crs("EPSG:4326")

    clean_roads = clean_roads.to_crs(METRIC_CRS)
    road_union = clean_roads.geometry.union_all()

    # Save cleaned road features in geographic coordinates.
    clean_roads.to_crs("EPSG:4326").to_file(
        ROAD_DIR / f"{corridor}_road_segments_clean.geojson",
        driver="GeoJSON",
    )

    businesses = pd.read_csv(business_path)

    for col in ["longitude", "latitude"]:
        businesses[col] = pd.to_numeric(
            businesses[col], errors="coerce"
        )

    businesses = businesses.dropna(
        subset=["longitude", "latitude"]
    )

    points = gpd.GeoDataFrame(
        businesses,
        geometry=gpd.points_from_xy(
            businesses["longitude"], businesses["latitude"]
        ),
        crs="EPSG:4326",
    ).to_crs(METRIC_CRS)

    distances = points.geometry.distance(road_union)
    print(f"Officially named road features retained: {len(clean_roads)}")
    print(f"Business records with coordinates: {len(points)}")
    print(f"Combined road length: {road_union.length / 1000:.2f} km")
    print(f"Median business-to-road distance: {distances.median():.1f} m")

    # Build candidates in metres using the projected CRS.
    for width in [50, 100, 150]:
        polygon = road_union.buffer(width)

        inside = points.geometry.intersects(polygon)
        count = int(inside.sum())
        percentage = 100 * count / len(points) if len(points) else 0

        candidate = gpd.GeoDataFrame(
            {
                "corridor": [corridor],
                "buffer_m": [width],
                "business_records_inside": [count],
                "business_records_total": [len(points)],
                "percent_inside": [round(percentage, 2)],
            },
            geometry=[polygon],
            crs=METRIC_CRS,
        ).to_crs("EPSG:4326")

        candidate.to_file(
            OUTPUT_DIR
            / f"{corridor}_{width}m_clean_candidate.geojson",
            driver="GeoJSON",
        )

        results.append({
            "corridor": corridor,
            "official_road_features": len(clean_roads),
            "road_length_km": round(road_union.length / 1000, 3),
            "buffer_m": width,
            "business_records_total": len(points),
            "business_records_inside": count,
            "percent_inside": round(percentage, 2),
            "median_road_distance_m": round(
                float(distances.median()), 2
            ),
        })

        print(
            f"{width} m candidate: {count}/{len(points)} "
            f"business records inside ({percentage:.2f}%)"
        )

summary = pd.DataFrame(results)
summary_path = OUTPUT_DIR / "clean_corridor_validation_summary.csv"
summary.to_csv(summary_path, index=False)

print(f"\nSaved validation summary: {summary_path}")
print("\n=== VALIDATION SUMMARY ===")
if not summary.empty:
    print(summary.to_string(index=False))
