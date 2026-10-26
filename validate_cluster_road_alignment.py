
import json
import pandas as pd
import matplotlib.pyplot as plt

# Load the updated DBSCAN results
df = pd.read_csv("western_avenue_clustered.csv")

# Load the existing Western Avenue centerline
with open("western_avenue_centerline.geojson", "r", encoding="utf-8") as f:
    geojson = json.load(f)

fig, ax = plt.subplots(figsize=(12, 9))

# Draw the road centerline from GeoJSON
def draw_geometry(geometry):
    geometry_type = geometry["type"]
    coordinates = geometry["coordinates"]

    if geometry_type == "LineString":
        lines = [coordinates]
    elif geometry_type == "MultiLineString":
        lines = coordinates
    else:
        print("Skipping unsupported geometry:", geometry_type)
        return

    for line in lines:
        if not line:
            continue

        # GeoJSON coordinates are [longitude, latitude]
        lons = [point[0] for point in line]
        lats = [point[1] for point in line]

        ax.plot(
            lons, lats,
            color="black",
            linewidth=3,
            label="Western Avenue centerline"
        )

# Support both FeatureCollection and single Feature GeoJSON
if geojson["type"] == "FeatureCollection":
    features = geojson.get("features", [])
elif geojson["type"] == "Feature":
    features = [geojson]
else:
    features = [{"geometry": geojson}]

for feature in features:
    geometry = feature.get("geometry")
    if geometry:
        draw_geometry(geometry)

# Plot each business cluster
for cluster_id in sorted(df["cluster"].unique()):
    group = df[df["cluster"] == cluster_id]

    if cluster_id == -1:
        ax.scatter(
            group["longitude"], group["latitude"],
            color="black", marker="x", s=80,
            label="Noise (-1)", zorder=3
        )
    else:
        ax.scatter(
            group["longitude"], group["latitude"],
            s=35, alpha=0.8,
            label=f"Cluster {cluster_id}", zorder=2
        )

ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("Western Avenue: DBSCAN Clusters and Road Centerline")
ax.grid(True, alpha=0.3)
ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
plt.tight_layout()

plt.savefig(
    "western_avenue_cluster_road_validation.png",
    dpi=200,
    bbox_inches="tight"
)

print("Businesses plotted:", len(df))
print("Clusters:", df.loc[df["cluster"] != -1, "cluster"].nunique())
print("Noise points:", (df["cluster"] == -1).sum())
print("Saved: western_avenue_cluster_road_validation.png")

plt.show()
