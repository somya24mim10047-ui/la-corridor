import geopandas as gpd
import pandas as pd
from pathlib import Path

root = Path("data")
boundary_dir = root / "final_corridor_boundaries"
corridor_dir = root / "corridors"
results = []

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    print(f"\n=== {name.upper()} ===")

    boundary = gpd.read_file(boundary_dir / f"{name}_boundary.geojson")
    roads_path = corridor_dir / f"{name}_road_segments_clean.geojson"
    businesses_path = corridor_dir / f"{name}_businesses.csv"

    roads = gpd.read_file(roads_path)
    df = pd.read_csv(businesses_path)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).copy()

    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326",
    )

    if boundary.crs is None:
        boundary = boundary.set_crs("OGC:CRS84")
    if roads.crs is None:
        roads = roads.set_crs("OGC:CRS84")

    # Use a metric CRS for distances
    boundary_m = boundary.to_crs("EPSG:32611")
    roads_m = roads.to_crs("EPSG:32611")
    points_m = points.to_crs("EPSG:32611")

    polygon = boundary_m.geometry.union_all()
    road_geometry = roads_m.geometry.union_all()

    inside = points_m.geometry.apply(polygon.covers)
    outside = points_m.loc[~inside].copy()
    outside["road_distance_m"] = outside.geometry.distance(road_geometry)

    total = len(outside)
    for threshold in [25, 50, 100]:
        count = int((outside["road_distance_m"] <= threshold).sum())
        results.append({
            "corridor": name,
            "outside_boundary_records": total,
            "within_25m_of_road": int((outside["road_distance_m"] <= 25).sum()),
            "within_50m_of_road": int((outside["road_distance_m"] <= 50).sum()),
            "within_100m_of_road": int((outside["road_distance_m"] <= 100).sum()),
        })
        break

    print("Excluded businesses:", total)
    print("Within 25 m of road:", int((outside.road_distance_m <= 25).sum()))
    print("Within 50 m of road:", int((outside.road_distance_m <= 50).sum()))
    print("Within 100 m of road:", int((outside.road_distance_m <= 100).sum()))
    print("\nFarthest sample:")
    cols = [c for c in ["business_name", "street_address"] if c in outside.columns]
    sample = outside.sort_values("road_distance_m", ascending=False)
    print(sample[cols + ["road_distance_m"]].head(5).to_string(index=False))

    outside.to_crs("EPSG:4326").drop(columns="geometry").assign(
        road_distance_m=outside["road_distance_m"].values
    ).to_csv(
        boundary_dir / f"{name}_outside_road_distance_check.csv",
        index=False
    )

print("\nSaved detailed outside-business road-distance reports.")
