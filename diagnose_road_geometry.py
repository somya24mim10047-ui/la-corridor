from pathlib import Path
import geopandas as gpd
import pandas as pd

root = Path("data")

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    print(f"\n{'='*20} {name.upper()} {'='*20}")

    files = {
        "BOUNDARY": root / "final_corridor_boundaries" / f"{name}_boundary.geojson",
        "CLEAN ROADS": root / "corridors" / f"{name}_road_segments_clean.geojson",
        "COMPLETE ROADS": root / "boundary_candidates" / "complete_road_sources" / f"{name}_complete_clean.geojson",
    }

    for label, path in files.items():
        if not path.exists():
            print(f"\n{label}: FILE NOT FOUND")
            continue

        gdf = gpd.read_file(path)
        print(f"\n{label}")
        print("File:", path)
        print("CRS:", gdf.crs)
        print("Geometry types:", gdf.geom_type.value_counts().to_dict())
        print("Bounds:", gdf.total_bounds)
        print("Feature count:", len(gdf))

    csv_path = root / "corridors" / f"{name}_businesses.csv"
    df = pd.read_csv(csv_path)
    print("\nBUSINESSES")
    print("Rows:", len(df))
    print("Longitude range:", df.longitude.min(), df.longitude.max())
    print("Latitude range:", df.latitude.min(), df.latitude.max())
