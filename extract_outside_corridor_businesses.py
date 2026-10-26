
from pathlib import Path
import pandas as pd
import geopandas as gpd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "corridors"
BOUNDARY_DIR = ROOT / "data" / "boundary_candidates"
OUTPUT_DIR = BOUNDARY_DIR / "outside_businesses"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CORRIDORS = [
    "wilshire_boulevard",
    "olympic_boulevard",
    "vermont_avenue",
    "larchmont_boulevard",
]

CRS_METRIC = "EPSG:32611"
summary = []

for corridor in CORRIDORS:
    csv_path = DATA_DIR / f"{corridor}_businesses.csv"
    boundary_path = BOUNDARY_DIR / f"{corridor}_100m_clean_candidate.geojson"

    if not csv_path.exists() or not boundary_path.exists():
        print(f"SKIPPED {corridor}: required file missing")
        continue

    df = pd.read_csv(csv_path)
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df = df.dropna(subset=["longitude", "latitude"]).copy()

    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    ).to_crs(CRS_METRIC)

    boundary = gpd.read_file(boundary_path).to_crs(CRS_METRIC)
    polygon = boundary.geometry.union_all()

    inside = points.geometry.intersects(polygon)
    outside = points.loc[~inside].copy()

    if not outside.empty:
        outside["distance_to_boundary_m"] = (
            outside.geometry.distance(polygon.boundary)
        )
        outside["corridor"] = corridor
        outside = outside.drop(columns="geometry")
        outside.to_csv(
            OUTPUT_DIR / f"{corridor}_outside_100m.csv",
            index=False,
        )

    summary.append({
        "corridor": corridor,
        "business_records": len(points),
        "inside_100m": int(inside.sum()),
        "outside_100m": int((~inside).sum()),
        "outside_percent": round((~inside).mean() * 100, 2),
    })

    print(
        f"{corridor}: {len(outside)} outside records "
        f"({(~inside).mean() * 100:.2f}%)"
    )

pd.DataFrame(summary).to_csv(
    OUTPUT_DIR / "outside_business_summary.csv",
    index=False,
)

print(f"\nReports saved to: {OUTPUT_DIR}")
