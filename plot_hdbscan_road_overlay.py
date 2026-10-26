
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import shape
from pyproj import Transformer
import hdbscan

# 1. Load unique business locations
df = pd.read_csv("western_avenue_unique_location_clusters.csv")
df = df.dropna(subset=["longitude", "latitude"]).copy()

# 2. Convert coordinates to metres for clustering
transformer = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:32611",
    always_xy=True
)

x, y = transformer.transform(
    df["longitude"].to_numpy(),
    df["latitude"].to_numpy()
)
points = np.column_stack((x, y))

# 3. Run HDBSCAN
model = hdbscan.HDBSCAN(
    min_cluster_size=4,
    min_samples=4,
    metric="euclidean"
)
df["hdbscan_cluster"] = model.fit_predict(points)

# 4. Load the Western Avenue centerline
with open("western_avenue_centerline.geojson", encoding="utf-8") as f:
    road_data = json.load(f)

geometry_type = road_data.get("type")

if geometry_type == "FeatureCollection":
    roads = [
        shape(feature["geometry"])
        for feature in road_data["features"]
        if feature.get("geometry")
    ]
elif geometry_type == "Feature":
    roads = [shape(road_data["geometry"])]
else:
    roads = [shape(road_data)]

# 5. Plot the centerline and clusters
fig, ax = plt.subplots(figsize=(11, 9))

for road in roads:
    if road.geom_type == "LineString":
        rx, ry = road.xy
        ax.plot(rx, ry, color="black", linewidth=2.5,
                label="Western Avenue centerline")
    elif road.geom_type == "MultiLineString":
        for line in road.geoms:
            rx, ry = line.xy
            ax.plot(rx, ry, color="black", linewidth=2.5)

for cluster in sorted(df["hdbscan_cluster"].unique()):
    group = df[df["hdbscan_cluster"] == cluster]
    label = "Noise" if cluster == -1 else f"Cluster {cluster}"

    ax.scatter(
        group["longitude"],
        group["latitude"],
        s=48,
        alpha=0.8,
        label=label
    )

ax.set_title("Western Avenue: HDBSCAN Clusters and Road Centerline")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.grid(True, alpha=0.25)
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout()

plt.savefig(
    "western_avenue_hdbscan_road_overlay.png",
    dpi=200,
    bbox_inches="tight"
)
plt.show()

df.to_csv("western_avenue_hdbscan_unique_clusters.csv", index=False)

print("Saved: western_avenue_hdbscan_road_overlay.png")
print("Saved: western_avenue_hdbscan_unique_clusters.csv")
