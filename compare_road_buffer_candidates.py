import geopandas as gpd
import pandas as pd
from pathlib import Path

root = Path("data")
out_dir = root / "final_corridor_boundaries"
out_dir.mkdir(parents=True, exist_ok=True)

results = []

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    print(f"\n=== {name.upper()} ===")

    boundary = gpd.read_file(
        out_dir / f"{name}_boundary.geojson"
    ).to_crs("EPSG:32611")

    roads = gpd.read_file(
        root / "boundary_candidates" /
        "complete_road_sources" /
        f"{name}_complete_clean.geojson"
    ).to_crs("EPSG:32611")

    df = pd.read_csv(root / "corridors" / f"{name}_businesses.csv")

    # Original business CSV coordinates are expected to be longitude/latitude.
    print(
        "Original coordinate ranges:",
        "longitude", df["longitude"].min(), "to", df["longitude"].max(),
        "| latitude", df["latitude"].min(), "to", df["latitude"].max()
    )

    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326"
    ).to_crs("EPSG:32611")

    current_polygon = boundary.geometry.union_all()
    road_geometry = roads.geometry.union_all()

    current_inside = points.geometry.map(current_polygon.covers)
    distance = points.geometry.distance(road_geometry)

    print("Total businesses:", len(points))
    print("Inside current boundary:", int(current_inside.sum()))
    print("Outside current boundary:", int((~current_inside).sum()))

    for buffer_m in [25, 50, 100]:
        candidate = road_geometry.buffer(buffer_m)
        candidate_inside = points.geometry.map(candidate.covers)

        results.append({
            "corridor": name,
            "method": f"complete_road_buffer_{buffer_m}m",
            "buffer_m": buffer_m,
            "businesses_inside": int(candidate_inside.sum()),
            "businesses_outside": int((~candidate_inside).sum()),
            "current_boundary_inside": int(current_inside.sum()),
            "outside_current_but_inside_candidate": int(
                ((~current_inside) & candidate_inside).sum()
            ),
            "candidate_polygon_parts": len(
                gpd.GeoSeries([candidate], crs="EPSG:32611")
                .explode(index_parts=False)
            )
        })

        print(
            f"{buffer_m} m buffer:",
            f"inside={int(candidate_inside.sum())},",
            f"outside={int((~candidate_inside).sum())},",
            f"recovered from current exclusions="
            f"{int(((~current_inside) & candidate_inside).sum())}"
        )

report = pd.DataFrame(results)
path = out_dir / "road_buffer_candidate_comparison.csv"
report.to_csv(path, index=False)
print("\nSaved comparison:", path)
print("\nNo final boundary files were changed.")
