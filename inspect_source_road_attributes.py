
from pathlib import Path
import geopandas as gpd

base = Path(__file__).resolve().parent
folder = base / "data" / "corridors"

corridors = [
    "wilshire_boulevard",
    "olympic_boulevard",
    "vermont_avenue",
    "larchmont_boulevard",
]

for corridor in corridors:
    path = folder / f"{corridor}_road_segments.geojson"

    print(f"\n{'=' * 65}")
    print(corridor.upper())

    if not path.exists():
        print(f"File missing: {path}")
        continue

    roads = gpd.read_file(path)
    print("Feature count:", len(roads))
    print("Available fields:", list(roads.columns))

    fields = [
        col for col in
        ["STNAME", "STSFX", "ADRF", "ADRT", "OBJECTID"]
        if col in roads.columns
    ]

    if fields:
        print(roads[fields].to_string(index=False))
    else:
        print(roads.drop(columns="geometry").head(10).to_string(index=False))
