import geopandas as gpd
from pathlib import Path
from shapely.ops import unary_union

root = Path("data")

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    path = (
        root / "boundary_candidates" /
        "complete_road_sources" /
        f"{name}_complete_clean.geojson"
    )

    roads = gpd.read_file(path).to_crs("EPSG:32611")
    merged = unary_union(list(roads.geometry))

    print(f"\n=== {name.upper()} ===")
    print("Road features:", len(roads))
    print("Total road length (km):", round(roads.geometry.length.sum() / 1000, 2))
    print("Merged geometry type:", merged.geom_type)
    print("Merged components:", len(merged.geoms) if hasattr(merged, "geoms") else 1)
    print("Road bounds (metres):", tuple(round(v, 1) for v in roads.total_bounds))
