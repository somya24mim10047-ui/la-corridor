import geopandas as gpd
import pandas as pd
from pathlib import Path

root = Path("data")
candidate_dir = root / "final_corridor_boundaries" / "selection_candidates"

choices = {
    "olympic_boulevard": 50,
    "wilshire_boulevard": 100,
}

for name, buffer_m in choices.items():
    print(f"\n=== {name.upper()} — {buffer_m} m ===")

    csv_path = root / "corridors" / f"{name}_businesses.csv"
    candidate_path = candidate_dir / f"{name}_{buffer_m}m_candidate.geojson"

    df = pd.read_csv(csv_path)
    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326"
    ).to_crs("EPSG:32611")

    polygon = gpd.read_file(candidate_path).to_crs("EPSG:32611").geometry.union_all()
    inside = points.geometry.map(polygon.covers)

    excluded = df.loc[~inside].copy()
    excluded["road_distance_m"] = points.loc[~inside].geometry.distance(
        polygon.boundary
    ).to_numpy()

    output = candidate_dir / f"{name}_excluded_business_review.csv"
    excluded.sort_values("road_distance_m").to_csv(output, index=False)

    print("Total businesses:", len(df))
    print("Included:", int(inside.sum()))
    print("Excluded:", int((~inside).sum()))
    print("Saved excluded-business review:", output)
    print("\nClosest 10 excluded businesses:")
    print(excluded.sort_values("road_distance_m").head(10).to_string(index=False))
