import geopandas as gpd
import pandas as pd
from pathlib import Path

root = Path("data")

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    print(f"\n=== {name.upper()} ===")

    csv_path = root / "final_corridor_boundaries" / f"{name}_outside_business_diagnostic.csv"
    df = pd.read_csv(csv_path)

    print("Diagnostic coordinate ranges:")
    print("longitude:", df["longitude"].min(), "to", df["longitude"].max())
    print("latitude :", df["latitude"].min(), "to", df["latitude"].max())

    for path in [
        root / "final_corridor_boundaries" / f"{name}_boundary.geojson",
        root / "boundary_candidates" / "complete_road_sources" / f"{name}_complete_clean.geojson",
    ]:
        gdf = gpd.read_file(path)
        print("\nFile:", path)
        print("CRS:", gdf.crs)
        print("Bounds:", gdf.total_bounds)
