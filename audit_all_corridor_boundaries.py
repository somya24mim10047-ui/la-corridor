
from pathlib import Path
import pandas as pd
import geopandas as gpd

BASE = Path(__file__).resolve().parent
ROAD_DIR = BASE / "data" / "boundary_candidates" / "complete_road_sources"
BUSINESS_DIR = BASE / "data" / "corridors"
OUT_DIR = BASE / "data" / "boundary_candidates" / "all_corridor_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CORRIDORS = {
    "wilshire_boulevard": "wilshire_boulevard_businesses.csv",
    "olympic_boulevard": "olympic_boulevard_businesses.csv",
    "vermont_avenue": "vermont_avenue_businesses.csv",
    "larchmont_boulevard": "larchmont_boulevard_businesses.csv",
}

WIDTHS = [50, 100, 150]
summary = []

for corridor, business_filename in CORRIDORS.items():
    road_file = ROAD_DIR / f"{corridor}_complete_clean.geojson"
    business_file = BUSINESS_DIR / business_filename

    if not road_file.exists() or not business_file.exists():
        print(f"SKIP {corridor}: required file missing")
        continue

    roads = gpd.read_file(road_file).to_crs("EPSG:32611")
    df = pd.read_csv(business_file)

    df = df.dropna(subset=["longitude", "latitude"]).copy()
    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326",
    ).to_crs("EPSG:32611")

    road_union = roads.geometry.union_all()
    points["road_distance_m"] = points.geometry.distance(road_union)

    print(f"\n=== {corridor.upper()} ===")
    print(f"Road features: {len(roads)}")
    print(f"Road length (km): {roads.geometry.length.sum() / 1000:.3f}")
    print(f"Business records with coordinates: {len(points)}")
    print(f"Median distance to road (m): {points['road_distance_m'].median():.2f}")

    for width in WIDTHS:
        outside = points[points["road_distance_m"] > width].copy()
        inside_count = len(points) - len(outside)

        summary.append({
            "corridor": corridor,
            "buffer_m": width,
            "business_records": len(points),
            "inside_count": inside_count,
            "inside_pct": round(inside_count / len(points) * 100, 2),
            "outside_count": len(outside),
            "median_road_distance_m": round(
                points["road_distance_m"].median(), 2
            ),
        })

        if width in [100, 150]:
            outside_file = OUT_DIR / f"{corridor}_outside_{width}m.csv"
            outside.drop(columns="geometry").to_csv(
                outside_file, index=False
            )
            print(
                f"{width}m: {inside_count}/{len(points)} inside "
                f"({inside_count / len(points) * 100:.2f}%), "
                f"{len(outside)} outside"
            )
            print(f"Saved exceptions: {outside_file}")

summary_df = pd.DataFrame(summary)
summary_file = OUT_DIR / "all_corridor_boundary_audit_summary.csv"
summary_df.to_csv(summary_file, index=False)

print(f"\nSummary saved: {summary_file}")
print(summary_df.to_string(index=False))
