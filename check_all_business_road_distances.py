import geopandas as gpd
import pandas as pd
from pathlib import Path

base = Path(".")
road_dir = base / "data/boundary_candidates/complete_road_sources"
data_dir = base / "data/corridors"

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    print("\n" + "=" * 65)
    print(name.upper())
    print("=" * 65)

    df = pd.read_csv(data_dir / f"{name}_businesses.csv")
    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326"
    ).to_crs("EPSG:32611")

    roads = gpd.read_file(
        road_dir / f"{name}_complete_clean.geojson"
    ).to_crs("EPSG:32611")

    road_union = roads.geometry.union_all()
    points["road_distance_m"] = points.geometry.distance(road_union)

    print("Businesses:", len(points))
    print("Road features:", len(roads))
    print("Road bounds:", roads.total_bounds.round(1).tolist())
    print("\nBusiness distance distribution (metres):")
    print(points.road_distance_m.describe().round(1).to_string())

    print("\nBusinesses farther than 100 m from supplied road:")
    cols = [
        "business_name", "street_address",
        "latitude", "longitude", "road_distance_m"
    ]
    print(
        points.loc[points.road_distance_m > 100, cols]
        .sort_values("road_distance_m")
        .head(15)
        .to_string(index=False)
    )
