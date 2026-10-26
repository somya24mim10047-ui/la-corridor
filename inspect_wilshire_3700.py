
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

road_file = (
    "data/boundary_candidates/complete_road_sources/"
    "wilshire_boulevard_complete_clean.geojson"
)

roads = gpd.read_file(road_file).to_crs("EPSG:32611")

# Coordinates shared by the excluded businesses at 3700 Wilshire Blvd.
point = gpd.GeoSeries(
    [Point(-118.3072, 34.0608)],
    crs="EPSG:4326",
).to_crs("EPSG:32611").iloc[0]

roads["distance_m"] = roads.geometry.distance(point)

print("Nearest road features to 3700 Wilshire Blvd:")
print(
    roads.assign(
        feature_id=roads.index
    )[["feature_id", "distance_m", "geometry"]]
    .sort_values("distance_m")
    .head(10)
    .drop(columns="geometry")
    .to_string(index=False)
)

print("\nNearest road geometries:")
nearest = roads.loc[roads.distance_m.nsmallest(5).index].copy()
print(nearest.to_crs("EPSG:4326").to_string(index=False))
