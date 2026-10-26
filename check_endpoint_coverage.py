import geopandas as gpd
import pandas as pd
from pathlib import Path

root = Path("data")
out_dir = root / "final_corridor_boundaries"

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    road_path = (
        root / "boundary_candidates" /
        "complete_road_sources" /
        f"{name}_complete_clean.geojson"
    )
    boundary_path = out_dir / f"{name}_boundary.geojson"

    roads = gpd.read_file(road_path).to_crs("EPSG:32611")
    boundary = gpd.read_file(boundary_path).to_crs("EPSG:32611")
    polygon = boundary.geometry.union_all()

    records = []
    for i, line in enumerate(roads.geometry):
        if line is None or line.is_empty:
            continue

        coords = list(line.coords)
        for label, xy in [("start", coords[0]), ("end", coords[-1])]:
            point = gpd.GeoSeries(
                [gpd.points_from_xy([xy[0]], [xy[1]])[0]],
                crs="EPSG:32611"
            ).iloc[0]

            records.append({
                "feature_id": i,
                "endpoint": label,
                "x": xy[0],
                "y": xy[1],
                "inside_boundary": polygon.covers(point),
                "distance_to_boundary_m": point.distance(polygon.boundary)
            })

    df = pd.DataFrame(records)
    df = df.sort_values("distance_to_boundary_m", ascending=False)

    print(f"\n=== {name.upper()} ===")
    print("Total road endpoints:", len(df))
    print("Endpoints inside boundary:", int(df["inside_boundary"].sum()))
    print("Endpoints outside boundary:", int((~df["inside_boundary"]).sum()))
    print("\n10 endpoints farthest from boundary:")
    print(df.head(10).to_string(index=False))

    df.to_csv(out_dir / f"{name}_endpoint_coverage.csv", index=False)
    print("Saved endpoint coverage report.")
