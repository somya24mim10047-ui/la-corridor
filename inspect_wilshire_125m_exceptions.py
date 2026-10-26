import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path

business_file = Path("data/corridors/wilshire_boulevard_businesses.csv")
candidate_file = Path(
    "data/boundary_candidates/complete_road_candidates/"
    "wilshire_boulevard_125m_complete_candidate.geojson"
)
output_dir = Path("data/boundary_candidates/all_corridor_audit")

businesses = pd.read_csv(business_file)
businesses = businesses.dropna(subset=["longitude", "latitude"]).copy()

points = gpd.GeoDataFrame(
    businesses,
    geometry=[
        Point(x, y)
        for x, y in zip(businesses["longitude"], businesses["latitude"])
    ],
    crs="EPSG:4326",
).to_crs(epsg=32611)

candidate = gpd.read_file(candidate_file).to_crs(epsg=32611)
buffer_geometry = candidate.geometry.union_all()

outside = points.loc[~points.geometry.intersects(buffer_geometry)].copy()
outside["road_distance_m"] = outside.geometry.distance(
    buffer_geometry.boundary
)

# Use the original road centerline to calculate distance, not the buffer edge.
roads = gpd.read_file(
    "data/boundary_candidates/complete_road_sources/"
    "wilshire_boulevard_complete_clean.geojson"
).to_crs(epsg=32611)

outside["road_distance_m"] = outside.geometry.apply(
    lambda point: roads.geometry.distance(point).min()
)

outside.drop(columns="geometry").to_csv(
    output_dir / "wilshire_boulevard_outside_125m.csv",
    index=False,
)

print("Businesses outside 125m:", len(outside))
print("\nDistance range:")
print(outside["road_distance_m"].describe().round(2).to_string())

print("\nMost frequent addresses:")
print(
    outside.groupby("street_address")
    .agg(
        records=("business_name", "size"),
        median_distance_m=("road_distance_m", "median"),
    )
    .sort_values("records", ascending=False)
    .head(15)
    .round(2)
    .to_string()
)

print("\nSaved:", (output_dir / "wilshire_boulevard_outside_125m.csv").resolve())
