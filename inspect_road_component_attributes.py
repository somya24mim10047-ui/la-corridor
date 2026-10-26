
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union, linemerge

ROOT = Path(__file__).resolve().parent
ROAD_DIR = ROOT / "data" / "corridors"
OUT_DIR = ROOT / "data" / "boundary_candidates"
OUT_DIR.mkdir(parents=True, exist_ok=True)

for corridor in ["wilshire_boulevard", "olympic_boulevard"]:
    path = ROAD_DIR / f"{corridor}_road_segments_clean.geojson"
    roads = gpd.read_file(path).to_crs("EPSG:32611")

    lines = [
        geom for geom in roads.geometry
        if geom is not None and not geom.is_empty
    ]
    merged = linemerge(unary_union(lines))
    components = (
        [merged] if merged.geom_type == "LineString"
        else [g for g in merged.geoms if g.geom_type == "LineString"]
    )

    rows = []
    for i, line in enumerate(components, start=1):
        midpoint = line.interpolate(0.5, normalized=True)
        rows.append({
            "corridor": corridor,
            "component_id": i,
            "length_m": round(line.length, 2),
            "midpoint_x": round(midpoint.x, 2),
            "midpoint_y": round(midpoint.y, 2),
            "min_x": round(line.bounds[0], 2),
            "min_y": round(line.bounds[1], 2),
            "max_x": round(line.bounds[2], 2),
            "max_y": round(line.bounds[3], 2),
        })

    result = pd.DataFrame(rows)
    output = OUT_DIR / f"{corridor}_component_inventory.csv"
    result.to_csv(output, index=False)

    print(f"\n=== {corridor.upper()} ===")
    print(result.to_string(index=False))
    print("Saved:", output)

print("\nComponent inventory complete.")
