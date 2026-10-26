
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union, linemerge, nearest_points

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

    if merged.geom_type == "LineString":
        components = [merged]
    else:
        components = [
            g for g in merged.geoms
            if g.geom_type == "LineString"
        ]

    rows = []

    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            a, b = components[i], components[j]
            distance = a.distance(b)

            if distance <= 250:
                p1, p2 = nearest_points(a, b)
                rows.append({
                    "corridor": corridor,
                    "component_a": i + 1,
                    "component_b": j + 1,
                    "component_a_length_m": round(a.length, 2),
                    "component_b_length_m": round(b.length, 2),
                    "nearest_distance_m": round(distance, 2),
                    "point_a_x": p1.x,
                    "point_a_y": p1.y,
                    "point_b_x": p2.x,
                    "point_b_y": p2.y,
                })

    result = pd.DataFrame(rows).sort_values("nearest_distance_m")
    output = OUT_DIR / f"{corridor}_road_gap_audit.csv"
    result.to_csv(output, index=False)

    print(f"\n=== {corridor.upper()} ===")
    print("Component pairs within 250 m:", len(result))
    print(result.head(15).to_string(index=False))
    print("Saved:", output)

print("\nRoad gap audit complete.")
