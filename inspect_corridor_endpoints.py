import geopandas as gpd
from pathlib import Path

root = Path("data")

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    path = (
        root / "boundary_candidates" /
        "complete_road_sources" /
        f"{name}_complete_clean.geojson"
    )

    roads = gpd.read_file(path).to_crs("EPSG:4326")

    endpoints = []
    for i, line in enumerate(roads.geometry):
        if line is None or line.is_empty:
            continue
        coords = list(line.coords)
        endpoints.append((i, "start", coords[0][0], coords[0][1]))
        endpoints.append((i, "end", coords[-1][0], coords[-1][1]))

    print(f"\n=== {name.upper()} ===")
    print("First 10 endpoints:")
    for item in endpoints[:10]:
        print(item)

    print("Last 10 endpoints:")
    for item in endpoints[-10:]:
        print(item)
