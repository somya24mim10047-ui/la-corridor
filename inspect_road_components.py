

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.ops import linemerge

BASE = Path(__file__).resolve().parent
ROAD_DIR = BASE / "data" / "corridors"
OUTPUT_DIR = BASE / "data" / "boundary_candidates"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CORRIDORS = {
    "wilshire_boulevard": "wilshire_boulevard_businesses.csv",
    "olympic_boulevard": "olympic_boulevard_businesses.csv",
    "vermont_avenue": "vermont_avenue_businesses.csv",
    "larchmont_boulevard": "larchmont_boulevard_businesses.csv",
    "western_avenue": "western_avenue_businesses.csv",
}

PROJECTED_CRS = "EPSG:32611"
records = []

for corridor, business_file in CORRIDORS.items():
    if corridor == "western_avenue":
        road_file = BASE / "western_avenue_centerline.geojson"
        business_path = BASE / business_file
    else:
        road_file = ROAD_DIR / f"{corridor}_road_segments.geojson"
        business_path = ROAD_DIR / business_file

    if not road_file.exists():
        print(f"SKIP {corridor}: road file not found: {road_file}")
        continue

    if not business_path.exists():
        print(f"SKIP {corridor}: business file not found: {business_path}")
        continue

    roads = gpd.read_file(road_file)
    businesses = pd.read_csv(business_path)

    required = {"longitude", "latitude"}
    if not required.issubset(businesses.columns):
        print(f"SKIP {corridor}: longitude/latitude columns missing")
        continue

    businesses["longitude"] = pd.to_numeric(
        businesses["longitude"], errors="coerce"
    )
    businesses["latitude"] = pd.to_numeric(
        businesses["latitude"], errors="coerce"
    )
    businesses = businesses.dropna(
        subset=["longitude", "latitude"]
    )

    if roads.crs is None:
        roads = roads.set_crs("EPSG:4326")

    roads = roads.to_crs(PROJECTED_CRS)

    points = gpd.GeoDataFrame(
        businesses,
        geometry=gpd.points_from_xy(
            businesses["longitude"], businesses["latitude"]
        ),
        crs="EPSG:4326",
    ).to_crs(PROJECTED_CRS)

    merged = roads.geometry.union_all()

    # Merge only when multiple line parts exist.
    if merged.geom_type == "MultiLineString":
        merged = linemerge(merged)

    if merged.geom_type == "LineString":
        components = [merged]
    elif merged.geom_type == "MultiLineString":
        components = list(merged.geoms)
    else:
        components = [
            geom for geom in getattr(merged, "geoms", [])
            if geom.geom_type == "LineString"
        ]

    print(f"\n--- {corridor.upper()} ---")
    print(f"Business records with coordinates: {len(points)}")
    print(f"Road components found: {len(components)}")

    for index, line in enumerate(
        sorted(components, key=lambda geom: geom.length, reverse=True),
        start=1,
    ):
        distances = points.geometry.distance(line)
        count_50 = int((distances <= 50).sum())
        count_150 = int((distances <= 150).sum())

        bounds = gpd.GeoSeries(
            [line], crs=PROJECTED_CRS
        ).to_crs("EPSG:4326").total_bounds

        row = {
            "corridor": corridor,
            "component_id": index,
            "length_m": round(line.length, 1),
            "businesses_within_50m": count_50,
            "businesses_within_150m": count_150,
            "min_longitude": round(bounds[0], 6),
            "min_latitude": round(bounds[1], 6),
            "max_longitude": round(bounds[2], 6),
            "max_latitude": round(bounds[3], 6),
        }
        records.append(row)

        print(
            f"Component {index}: length={row['length_m']} m | "
            f"within 50m={count_50} | within 150m={count_150}"
        )

report = pd.DataFrame(records)
report_path = OUTPUT_DIR / "road_component_inspection.csv"
report.to_csv(report_path, index=False)

print(f"\nTotal component records: {len(report)}")
print(f"Saved report: {report_path}")


