
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data" / "validation"

files = sorted(DATA_DIR.glob("*_road_validation.csv"))

rows = []

for file in files:
    df = pd.read_csv(file)

    if "corridor" not in df.columns:
        df["corridor"] = file.stem.replace(
            "_road_validation", ""
        )

    for col in ["latitude", "longitude"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["latitude", "longitude"])

    unique = df.drop_duplicates(["latitude", "longitude"])

    rows.append({
        "corridor": df["corridor"].iloc[0],
        "business_records": len(df),
        "unique_locations": len(unique),
        "south_latitude": unique["latitude"].min(),
        "north_latitude": unique["latitude"].max(),
        "west_longitude": unique["longitude"].min(),
        "east_longitude": unique["longitude"].max(),
    })

result = pd.DataFrame(rows).sort_values("corridor")

output = DATA_DIR / "corridor_coordinate_extents.csv"
result.to_csv(output, index=False)

print("\n=== CORRIDOR COORDINATE EXTENTS ===")
print(result.to_string(index=False))
print(f"\nSaved to: {output}")
print(
    "\nThese are dataset extents, not approved corridor boundaries. "
    "Inspect the map and confirm the intended street segment before filtering."
)
