
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union, linemerge

ROOT = Path(__file__).resolve().parent
ROAD_DIR = ROOT / "data" / "corridors"

corridors = [
    "wilshire_boulevard",
    "olympic_boulevard",
    "vermont_avenue",
    "larchmont_boulevard",
]

for corridor in corridors:
    path = ROAD_DIR / f"{corridor}_road_segments_clean.geojson"

    print(f"\n{'=' * 65}")
    print(corridor.upper())

    if not path.exists():
        print("MISSING FILE:", path)
        continue

    roads = gpd.read_file(path)

    if roads.empty:
        print("No road features found.")
        continue

    roads = roads.to_crs("EPSG:32611")
    lines = [
        geom for geom in roads.geometry
        if geom is not None and not geom.is_empty
    ]

    merged = linemerge(unary_union(lines))

    if merged.geom_type == "LineString":
        components = [merged]
    elif merged.geom_type == "MultiLineString":
        components = list(merged.geoms)
    else:
        components = [
            geom for geom in getattr(merged, "geoms", [])
            if geom.geom_type == "LineString"
        ]

    lengths = sorted(
        [line.length for line in components],
        reverse=True
    )

    print("Road features:", len(roads))
    print("Merged line components:", len(components))
    print("Total road length (km):", round(sum(lengths) / 1000, 3))
    print("Longest component lengths (km):")
    for i, length in enumerate(lengths[:15], start=1):
        print(f"  {i}. {length / 1000:.3f}")

    if len(components) > 1:
        distances = []
        for i in range(len(components)):
            for j in range(i + 1, len(components)):
                d = components[i].distance(components[j])
                distances.append((d, i + 1, j + 1))

        distances.sort()
        print("Closest distinct component pairs:")
        for distance, a, b in distances[:10]:
            print(f"  Components {a} and {b}: {distance:.2f} m")
