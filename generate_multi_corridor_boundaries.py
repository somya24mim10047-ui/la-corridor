
from pathlib import Path
import geopandas as gpd
import pandas as pd

BASE = Path(__file__).parent
DATA_DIR = BASE / "data" / "corridors"
OUT_DIR = BASE / "data" / "boundary_candidates"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CORRIDORS = [
    "wilshire_boulevard",
    "olympic_boulevard",
    "vermont_avenue",
    "larchmont_boulevard",
]

WIDTHS_M = [50, 100, 150]
CRS_METRIC = "EPSG:32611"
results = []

for name in CORRIDORS:
    road_file = DATA_DIR / f"{name}_road_segments.geojson"
    business_file = DATA_DIR / f"{name}_businesses.csv"

    print(f"\nProcessing {name}...")

    if not road_file.exists():
        print(f"SKIPPED: road geometry not found: {road_file}")
        continue

    if not business_file.exists():
        print(f"SKIPPED: business data not found: {business_file}")
        continue

    roads = gpd.read_file(road_file)
    businesses = pd.read_csv(business_file)

    if roads.empty:
        print("SKIPPED: road geometry is empty.")
        continue

    businesses = businesses.dropna(
        subset=["longitude", "latitude"]
    ).copy()

    if businesses.empty:
        print("SKIPPED: no businesses with coordinates.")
        continue

    # Project to metres before measuring or buffering.
    roads_m = roads.to_crs(CRS_METRIC)
    points = gpd.GeoDataFrame(
        businesses,
        geometry=gpd.points_from_xy(
            businesses["longitude"], businesses["latitude"]
        ),
        crs="EPSG:4326",
    ).to_crs(CRS_METRIC)

    # Dissolve overlapping road segments before buffering.
    road_geometry = roads_m.geometry.union_all()

    print(f"Road segments: {len(roads_m)}")
    print(f"Connected components: {len(roads_m)}")
    print(f"Total source-segment length: "
          f"{roads_m.geometry.length.sum() / 1000:.2f} km")

    for width in WIDTHS_M:
        candidate = road_geometry.buffer(width)

        inside = points.geometry.intersects(candidate)
        count = int(inside.sum())

        boundary = gpd.GeoDataFrame(
            [{
                "corridor": name,
                "buffer_each_side_m": width,
                "businesses_inside": count,
                "businesses_total": len(points),
                "percentage_inside": round(
                    count / len(points) * 100, 2
                ),
                "geometry": candidate,
            }],
            geometry="geometry",
            crs=CRS_METRIC,
        ).to_crs("EPSG:4326")

        output = OUT_DIR / f"{name}_{width}m_candidate.geojson"
        boundary.to_file(output, driver="GeoJSON")

        results.append({
            "corridor": name,
            "buffer_each_side_m": width,
            "businesses_inside": count,
            "businesses_total": len(points),
            "percentage_inside": round(
                count / len(points) * 100, 2
            ),
            "road_segments": len(roads_m),
            "source_length_km": round(
                roads_m.geometry.length.sum() / 1000, 2
            ),
        })

        print(
            f"{width} m: {count}/{len(points)} businesses "
            f"inside ({count / len(points) * 100:.1f}%)"
        )
        print(f"Saved candidate: {output.name}")

if results:
    report = pd.DataFrame(results)
    report_file = OUT_DIR / "boundary_candidate_summary.csv"
    report.to_csv(report_file, index=False)

    print("\n=== BOUNDARY CANDIDATE SUMMARY ===")
    print(report.to_string(index=False))
    print(f"\nSaved report: {report_file}")
else:
    print("\nNo candidates generated. Review the input files.")
