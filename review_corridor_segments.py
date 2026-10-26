
from pathlib import Path
import pandas as pd
import folium

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data" / "validation"

files = sorted(DATA_DIR.glob("*_road_validation.csv"))

corridors = {}

for file in files:
    df = pd.read_csv(file)

    if "corridor" not in df.columns:
        df["corridor"] = file.stem.replace(
            "_road_validation", ""
        )

    for col in ["latitude", "longitude", "road_distance_m"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["latitude", "longitude"])
    df = df.drop_duplicates(["latitude", "longitude"])

    corridors[df["corridor"].iloc[0]] = df

if not corridors:
    raise RuntimeError("No corridor data found.")

print("Available corridors:")
names = sorted(corridors.keys())

for i, name in enumerate(names, start=1):
    print(f"{i}. {name}")

choice = input("\nEnter corridor number to inspect: ").strip()

if not choice.isdigit() or not (1 <= int(choice) <= len(names)):
    raise ValueError("Enter a valid corridor number.")

name = names[int(choice) - 1]
df = corridors[name]

center = [df["latitude"].mean(), df["longitude"].mean()]
m = folium.Map(location=center, zoom_start=14)

for _, row in df.iterrows():
    distance = row.get("road_distance_m", None)

    if pd.isna(distance):
        color = "gray"
    elif distance <= 25:
        color = "green"
    elif distance <= 50:
        color = "orange"
    else:
        color = "red"

    folium.CircleMarker(
        [row["latitude"], row["longitude"]],
        radius=5,
        color=color,
        fill=True,
        fill_opacity=0.8,
        tooltip=str(row.get("street_address", "Business location")),
        popup=(
            f"Business: {row.get('business_name', 'Unknown')}<br>"
            f"Address: {row.get('street_address', 'Unknown')}<br>"
            f"Distance to matching road: {distance} m"
        )
    ).add_to(m)

m.fit_bounds([
    [df["latitude"].min(), df["longitude"].min()],
    [df["latitude"].max(), df["longitude"].max()]
])

output = DATA_DIR / f"{name}_segment_review.html"
m.save(str(output))

print(f"\nMap saved: {output}")
print("Green <=25 m | Orange 25–50 m | Red >50 m")
