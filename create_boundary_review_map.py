
from pathlib import Path
import pandas as pd
import folium

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data" / "validation"

files = sorted(DATA_DIR.glob("*_road_validation.csv"))

if not files:
    raise FileNotFoundError("No road-validation files found.")

frames = []

for file in files:
    df = pd.read_csv(file)

    # Western Avenue and the other datasets use different schemas.
    if "corridor" not in df.columns:
        df["corridor"] = file.stem.replace(
            "_road_validation", ""
        )

    for col in ["latitude", "longitude", "road_distance_m"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=["latitude", "longitude", "road_distance_m"]
    )

    frames.append(df)

data = pd.concat(frames, ignore_index=True)

# Center the map on the available business locations.
center = [
    data["latitude"].mean(),
    data["longitude"].mean()
]

m = folium.Map( location=center,
    zoom_start=13,
    tiles="CartoDB positron")

def marker_color(distance):
    if distance <= 25:
        return "green"
    elif distance <= 50:
        return "orange"
    return "red"

for corridor, group in data.groupby("corridor"):
    layer = folium.FeatureGroup(
        name=corridor.replace("_", " ").title(),
        show=True
    )

    # Display one marker per distinct coordinate per corridor.
    locations = group.drop_duplicates(
        subset=["latitude", "longitude"]
    )

    for _, row in locations.iterrows():
        address = str(row.get("street_address", "Address unavailable"))
        business = str(row.get("business_name", "Business"))
        distance = row["road_distance_m"]

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=5,
            color=marker_color(distance),
            fill=True,
            fill_opacity=0.75,
            popup=(
                f"<b>{business}</b><br>"
                f"Corridor: {corridor}<br>"
                f"Address: {address}<br>"
                f"Distance to matching road: {distance:.1f} m"
            ),
            tooltip=f"{corridor}: {distance:.1f} m"
        ).add_to(layer)

    layer.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

# Fit the map to all available business locations.
bounds = [
    [data["latitude"].min(), data["longitude"].min()],
    [data["latitude"].max(), data["longitude"].max()]
]
m.fit_bounds(bounds)

output = DATA_DIR / "corridor_boundary_review_map.html"
m.save(str(output))

print("Map saved:", output)
print("Unique coordinate markers by corridor:")
print(
    data.groupby("corridor")
    .apply(
        lambda g: g[["latitude", "longitude"]]
        .drop_duplicates()
        .shape[0],
        include_groups=False
    ).to_string()
)
print("\nLegend: Green <= 25 m | Orange 25-50 m | Red > 50 m")
print("Note: Markers show business locations, not final boundaries.")
