
import requests
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from pyproj import Transformer

# Load businesses more than 100 m from the selected road geometry
df = pd.read_csv("western_avenue_business_road_distances.csv")
df = df[df["distance_to_road_m"] > 100]

transformer = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
)

south, west, north, east = 34.0600, -118.3160, 34.0720, -118.3040

query = f"""
[out:json][timeout:60];
way["highway"]["name"~"Western",i]
({south},{west},{north},{east});
out geom;
"""

servers = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

data = None

for url in servers:
    try:
        print(f"\nTrying: {url}")

        response = requests.post(
            url,
            data={"data": query},
            headers={
                "User-Agent": "WesternAvenueCorridorResearch/1.0"
            },
            timeout=90
        )

        response.raise_for_status()
        data = response.json()

        if data.get("elements"):
            print("Road data downloaded successfully!")
            break

        print("No road features returned by this server.")

    except Exception as error:
        print(f"Server failed: {error}")

if not data or not data.get("elements"):
    raise RuntimeError(
        "Could not download road geometry. "
        "Check your internet connection and try again later."
    )

roads = []

for element in data["elements"]:
    coords = [
        transformer.transform(point["lon"], point["lat"])
        for point in element.get("geometry", [])
    ]

    if len(coords) >= 2:
        roads.append(LineString(coords))

fig, ax = plt.subplots(figsize=(10, 8))

for road in roads:
    x, y = road.xy
    ax.plot(x, y, color="black", linewidth=1, alpha=0.65)

for _, business in df.iterrows():
    x, y = transformer.transform(
        business["longitude"], business["latitude"]
    )

    ax.scatter(x, y, color="red", s=80, zorder=5)
    ax.annotate(
        business["business_name"],
        (x, y),
        xytext=(6, 6),
        textcoords="offset points",
        fontsize=8
    )

ax.set_title("Business Locations and Nearby Western Avenue Roads")
ax.set_xlabel("Easting (metres)")
ax.set_ylabel("Northing (metres)")
ax.grid(True, alpha=0.3)
ax.set_aspect("equal", adjustable="datalim")

plt.tight_layout()
plt.savefig("western_avenue_outlier_check.png", dpi=200)
plt.show()

print("\nSaved: western_avenue_outlier_check.png")

