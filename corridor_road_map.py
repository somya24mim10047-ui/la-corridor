

import requests
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. LOAD BUSINESS DATA
# ==========================================

print("Loading business data...")

df = pd.read_csv("western_avenue_businesses.csv")

required_columns = {"latitude", "longitude"}

if not required_columns.issubset(df.columns):
    raise ValueError(
        "CSV must contain latitude and longitude columns."
    )

df = df.dropna(subset=["latitude", "longitude"])

print("Business locations loaded:", len(df))


# ==========================================
# 2. DEFINE STUDY AREA
# ==========================================

south = 34.0615
north = 34.0690
west = -118.3125
east = -118.3060

# Proposed endpoints:
# Start: Western Avenue and Wilshire Boulevard
# End: Western Avenue and West 3rd Street

start_lat = 34.062100
start_lon = -118.308881

end_lat = 34.068419
end_lon = -118.309011


# ==========================================
# 3. DOWNLOAD WESTERN AVENUE ROAD GEOMETRY
# ==========================================

print("\nRequesting Western Avenue road geometry...")

query = f"""
[out:json][timeout:60];
way["highway"]["name"~"Western Avenue|North Western Avenue|S Western Avenue",i]
({south},{west},{north},{east});
out geom;
"""

servers = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

headers = {
    "User-Agent": "LA-Corridor-Research/1.0",
    "Accept": "application/json",
}

roads = []

for url in servers:
    print("\nTrying server:", url)

    try:
        response = requests.post(
            url,
            data={"data": query},
            headers=headers,
            timeout=90
        )

        print("HTTP status:", response.status_code)

        if response.status_code != 200:
            print("Server response:", response.text[:400])
            continue

        result = response.json()
        roads = result.get("elements", [])

        if roads:
            print("Road features retrieved:", len(roads))
            break

        print("No matching road features found at this server.")

    except (requests.RequestException, ValueError) as error:
        print("Request failed:", error)

if not roads:
    raise SystemExit(
        "\nCould not retrieve road geometry. "
        "Check your internet connection or try again later."
    )


# ==========================================
# 4. CREATE THE MAP
# ==========================================

print("\nCreating corridor map...")

fig, ax = plt.subplots(figsize=(10, 12))

# Draw road geometry
for index, road in enumerate(roads):
    points = road.get("geometry", [])

    if not points:
        continue

    road_lons = [point["lon"] for point in points]
    road_lats = [point["lat"] for point in points]

    ax.plot(
        road_lons,
        road_lats,
        color="black",
        linewidth=2,
        label="Western Avenue road"
        if index == 0 else None,
        zorder=2
    )

# Draw business locations
ax.scatter(
    df["longitude"],
    df["latitude"],
    s=18,
    alpha=0.65,
    color="royalblue",
    label="Business locations",
    zorder=3
)

# Draw proposed endpoints
ax.scatter(
    [start_lon, end_lon],
    [start_lat, end_lat],
    color="red",
    marker="X",
    s=130,
    label="Proposed endpoints",
    zorder=5
)

# Label start and end
ax.annotate(
    "Start: Wilshire Boulevard",
    (start_lon, start_lat),
    xytext=(8, -18),
    textcoords="offset points",
    fontsize=9
)

ax.annotate(
    "End: West 3rd Street",
    (end_lon, end_lat),
    xytext=(8, 8),
    textcoords="offset points",
    fontsize=9
)

# Labels and formatting
ax.set_title(
    "Western Avenue Corridor Study\n"
    "Los Angeles, California",
    fontsize=14
)

ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")

ax.grid(True, alpha=0.25)
ax.legend()
ax.set_aspect("equal", adjustable="datalim")

plt.tight_layout()

# Save image
output_file = "western_avenue_corridor_map.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("\nMap saved successfully:", output_file)
print("Business points plotted:", len(df))
print("Road features retrieved:", len(roads))
print("\nNext: open the PNG and verify that the road and endpoint markers align.")
