import geopandas as gpd
import pandas as pd
from pathlib import Path

root = Path("data")
outdir = root / "final_corridor_boundaries"

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    boundary = gpd.read_file(outdir / f"{name}_boundary.geojson")
    if boundary.crs is None:
        boundary = boundary.set_crs("OGC:CRS84")
    boundary = boundary.to_crs("EPSG:4326")
    polygon = boundary.geometry.union_all()

    df = pd.read_csv(root / "corridors" / f"{name}_businesses.csv")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).copy()

    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326",
    )
    outside = points.loc[~points.geometry.apply(polygon.covers)].copy()

    print(f"\n=== {name.upper()} OUTSIDE SAMPLE ===")
    print(f"Total outside: {len(outside)}")
    cols = [
        c for c in
        ["business_name", "street_address", "latitude", "longitude", "primary_naics_description"]
        if c in outside.columns
    ]
    print(outside[cols].head(10).to_string(index=False))

    outside[cols].to_csv(outdir / f"{name}_outside_final_boundary_sample.csv", index=False)

print("\nSaved outside-business samples in", outdir.resolve())
