
from pathlib import Path
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "data" / "boundary_candidates"
ROAD_DIR = ROOT / "data" / "corridors"
BUSINESS_DIR = ROOT / "data" / "corridors"
OUTPUT_ROADS = BASE / "complete_road_sources"
OUTPUT_BOUNDS = BASE / "complete_road_candidates"

OUTPUT_ROADS.mkdir(parents=True, exist_ok=True)
OUTPUT_BOUNDS.mkdir(parents=True, exist_ok=True)

CRS_METRIC = "EPSG:32611"
WIDTHS = [50, 100, 150]

corridors = [
    "wilshire_boulevard",
    "olympic_boulevard",
    "vermont_avenue",
    "larchmont_boulevard",
]

summary = []

for corridor in corridors:
    print(f"\n=== {corridor.upper()} ===")

    source = BASE / f"{corridor}_official_full_retrieval.geojson"
    business_file = BUSINESS_DIR / f"{corridor}_businesses.csv"

    if not source.exists():
        print("Missing complete official source:", source)
        continue

    if not business_file.exists():
        print("Missing business CSV:", business_file)
        continue

    roads = gpd.read_file(source)

    # Retain only the exact intended street name and suffix.
    expected_name = corridor.replace("_boulevard", "").replace("_avenue", "")
    expected_name = expected_name.replace("_", " ").upper()
    expected_suffix = "AVE" if corridor.endswith("_avenue") else "BLVD"

    roads = roads[
        roads["STNAME"].astype(str).str.upper().eq(expected_name)
        & roads["STSFX"].astype(str).str.upper().eq(expected_suffix)
    ].copy()

    roads = roads[
        roads.geometry.notna() & ~roads.geometry.is_empty
    ].copy()

    if roads.empty:
        print("No matching road geometries after filtering.")
        continue

    # Save the corrected source separately.
    road_output = OUTPUT_ROADS / f"{corridor}_complete_clean.geojson"
    roads.to_file(road_output, driver="GeoJSON")

    roads_m = roads.to_crs(CRS_METRIC)
    road_union = roads_m.geometry.union_all()

    businesses = pd.read_csv(business_file)

    required = {"longitude", "latitude"}
    if not required.issubset(businesses.columns):
        print("Business CSV missing longitude/latitude columns.")
        print("Available columns:", businesses.columns.tolist())
        continue

    businesses["longitude"] = pd.to_numeric(
        businesses["longitude"], errors="coerce"
    )
    businesses["latitude"] = pd.to_numeric(
        businesses["latitude"], errors="coerce"
    )
    businesses = businesses.dropna(
        subset=["longitude", "latitude"]
    ).copy()

    points = gpd.GeoDataFrame(
        businesses,
        geometry=gpd.points_from_xy(
            businesses["longitude"], businesses["latitude"]
        ),
        crs="EPSG:4326",
    ).to_crs(CRS_METRIC)

    distances = points.geometry.distance(road_union)
    total = len(points)

    print("Complete official road features:", len(roads))
    print("Total road length (km):", round(road_union.length / 1000, 3))
    print("Business records with coordinates:", total)
    print("Median business-to-road distance (m):", round(distances.median(), 2))

    for width in WIDTHS:
        polygon = road_union.buffer(width)
        inside = points.geometry.intersects(polygon)
        count = int(inside.sum())

        # Save candidate polygon with a new filename.
        boundary = gpd.GeoDataFrame(
            {
                "corridor": [corridor],
                "buffer_m": [width],
                "road_features": [len(roads)],
                "business_total": [total],
                "business_inside": [count],
                "percent_inside": [
                    round(100 * count / total, 2) if total else 0
                ],
            },
            geometry=[polygon],
            crs=CRS_METRIC,
        ).to_crs("EPSG:4326")

        boundary.to_file(
            OUTPUT_BOUNDS / f"{corridor}_{width}m_complete_candidate.geojson",
            driver="GeoJSON",
        )

        summary.append({
            "corridor": corridor,
            "official_road_features": len(roads),
            "road_length_km": round(road_union.length / 1000, 3),
            "buffer_m": width,
            "business_records_total": total,
            "business_records_inside": count,
            "percent_inside": round(100 * count / total, 2) if total else 0,
            "median_road_distance_m": round(distances.median(), 2),
        })

        print(
            f"{width}m buffer: {count}/{total} "
            f"({100 * count / total:.2f}% inside)"
        )

summary_file = BASE / "complete_road_validation_summary.csv"
pd.DataFrame(summary).to_csv(summary_file, index=False)

print("\nSaved corrected candidate roads to:", OUTPUT_ROADS)
print("Saved corrected candidate boundaries to:", OUTPUT_BOUNDS)
print("Saved summary to:", summary_file)
print("\nRebuild complete. Existing boundaries were not overwritten.")
