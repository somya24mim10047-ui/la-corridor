import geopandas as gpd
import pandas as pd
from pathlib import Path

root = Path("data")
boundary_dir = root / "final_corridor_boundaries"

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    print(f"\n{'='*18} {name.upper()} {'='*18}")

    boundary = gpd.read_file(boundary_dir / f"{name}_boundary.geojson")
    if boundary.crs is None:
        boundary = boundary.set_crs("OGC:CRS84")
    boundary = boundary.to_crs("EPSG:32611")
    polygon = boundary.geometry.union_all()

    df = pd.read_csv(root / "corridors" / f"{name}_businesses.csv")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).copy()

    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326",
    ).to_crs("EPSG:32611")

    inside = points.geometry.apply(polygon.covers)
    print("Businesses inside boundary:", int(inside.sum()))
    print("Businesses outside boundary:", int((~inside).sum()))

    sources = {
        "CLEAN": root / "corridors" / f"{name}_road_segments_clean.geojson",
        "COMPLETE": root / "boundary_candidates" / "complete_road_sources" / f"{name}_complete_clean.geojson",
    }

    for label, path in sources.items():
        roads = gpd.read_file(path)
        if roads.crs is None:
            roads = roads.set_crs("EPSG:4326")
        roads = roads.to_crs("EPSG:32611")
        road_geometry = roads.geometry.union_all()

        distances = points.geometry.distance(road_geometry)
        outside_distances = distances.loc[~inside]

        print(f"\n{label} road source: {len(roads)} features")
        print("All businesses distance (min/median/max):",
              round(distances.min(), 1),
              round(distances.median(), 1),
              round(distances.max(), 1))
        print("Outside businesses within 25m:",
              int((outside_distances <= 25).sum()))
        print("Outside businesses within 50m:",
              int((outside_distances <= 50).sum()))
        print("Outside businesses within 100m:",
              int((outside_distances <= 100).sum()))

        nearest = outside_distances.sort_values().head(5)
        print("Nearest excluded-business distances (m):",
              [round(v, 1) for v in nearest.tolist()])

print("\nComparison complete. No files were changed.")
