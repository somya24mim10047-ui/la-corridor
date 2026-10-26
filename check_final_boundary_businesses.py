from pathlib import Path
import geopandas as gpd
import pandas as pd

root = Path("data")
boundary_dir = root / "final_corridor_boundaries"
business_dir = root / "corridors"

corridors = {
    "western_avenue": root / "validation" / "western_avenue_road_validation.csv",
    "larchmont_boulevard": business_dir / "larchmont_boulevard_businesses.csv",
    "olympic_boulevard": business_dir / "olympic_boulevard_businesses.csv",
    "vermont_avenue": business_dir / "vermont_avenue_businesses.csv",
    "wilshire_boulevard": business_dir / "wilshire_boulevard_businesses.csv",
}

results = []

for name, csv_path in corridors.items():
    boundary_path = boundary_dir / f"{name}_boundary.geojson"

    boundary = gpd.read_file(boundary_path)
    df = pd.read_csv(csv_path)

    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).copy()

    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )

    if boundary.crs is None:
        boundary = boundary.set_crs("OGC:CRS84")

    boundary = boundary.to_crs(points.crs)
    polygon = boundary.geometry.union_all()
    inside = points.geometry.apply(polygon.covers)

    total = len(points)
    count_inside = int(inside.sum())

    results.append({
        "corridor": name,
        "business_records": total,
        "inside": count_inside,
        "outside": total - count_inside,
        "inside_percent": round(100 * count_inside / total, 2) if total else 0,
        "boundary_valid": bool(boundary.geometry.is_valid.all()),
        "polygon_parts": sum(
            len(g.geoms) if hasattr(g, "geoms") else 1
            for g in boundary.geometry
        ),
    })

report = pd.DataFrame(results)
out = boundary_dir / "final_boundary_business_check.csv"
report.to_csv(out, index=False)

print("\n=== ALL FIVE CORRIDORS ===")
print(report.to_string(index=False))
print(f"\nSaved: {out.resolve()}")
