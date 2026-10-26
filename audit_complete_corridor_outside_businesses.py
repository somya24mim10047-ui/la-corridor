
from pathlib import Path
import pandas as pd
import geopandas as gpd

BASE = Path(__file__).resolve().parent

SOURCE_DIR = BASE / "data" / "boundary_candidates" / "complete_road_sources"
CANDIDATE_DIR = BASE / "data" / "boundary_candidates" / "complete_road_candidates"
BUSINESS_DIR = BASE / "data" / "corridors"
OUTPUT_DIR = BASE / "data" / "boundary_candidates" / "complete_outside_audit"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CORRIDORS = ["wilshire_boulevard", "olympic_boulevard"]
WIDTHS = [100, 150]

summary = []

for corridor in CORRIDORS:
    road_file = SOURCE_DIR / f"{corridor}_complete_clean.geojson"
    business_file = BUSINESS_DIR / f"{corridor}_businesses.csv"

    if not road_file.exists() or not business_file.exists():
        print(f"Skipping {corridor}: source file missing")
        continue

    roads = gpd.read_file(road_file).to_crs("EPSG:32611")
    road_union = roads.geometry.union_all()

    df = pd.read_csv(business_file)
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df = df.dropna(subset=["longitude", "latitude"]).copy()

    businesses = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    ).to_crs("EPSG:32611")

    businesses["distance_to_road_m"] = (
        businesses.geometry.distance(road_union)
    ).round(2)

    for width in WIDTHS:
        candidate_file = (
            CANDIDATE_DIR
            / f"{corridor}_{width}m_complete_candidate.geojson"
        )

        if not candidate_file.exists():
            print(f"Missing candidate: {candidate_file}")
            continue

        boundary = gpd.read_file(candidate_file).to_crs("EPSG:32611")
        boundary_union = boundary.geometry.union_all()

        outside = businesses.loc[
            ~businesses.geometry.intersects(boundary_union)
        ].copy()

        outside["corridor"] = corridor
        outside["candidate_buffer_m"] = width

        output_file = (
            OUTPUT_DIR / f"{corridor}_outside_{width}m.csv"
        )

        outside.drop(columns="geometry").to_csv(output_file, index=False)

        distances = outside["distance_to_road_m"]

        summary.append({
            "corridor": corridor,
            "buffer_m": width,
            "businesses_outside": len(outside),
            "median_distance_to_road_m": (
                round(distances.median(), 2) if len(outside) else None
            ),
            "minimum_distance_to_road_m": (
                round(distances.min(), 2) if len(outside) else None
            ),
            "maximum_distance_to_road_m": (
                round(distances.max(), 2) if len(outside) else None
            ),
        })

        print(
            f"{corridor} | {width}m buffer | "
            f"{len(outside)} outside | saved {output_file}"
        )

summary_file = OUTPUT_DIR / "outside_audit_summary.csv"
pd.DataFrame(summary).to_csv(summary_file, index=False)

print(f"\nSummary saved to: {summary_file}")
