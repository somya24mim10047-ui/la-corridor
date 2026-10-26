
import json
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import shape
from shapely.ops import transform as transform_geometry
from pyproj import Transformer

# Load unique locations and cluster labels
df = pd.read_csv("western_avenue_unique_location_clusters.csv")

# Project coordinates into metres
transformer = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
)

df["x"], df["y"] = transformer.transform(
    df["longitude"].to_numpy(),
    df["latitude"].to_numpy()
)

# Load Western Avenue centerline
with open("western_avenue_centerline.geojson", encoding="utf-8") as f:
    geojson = json.load(f)

features = geojson.get("features", [])
if geojson.get("type") == "Feature":
    features = [geojson]

roads = [
    transform_geometry(
        transformer.transform, shape(feature["geometry"])
    )
    for feature in features
    if feature.get("geometry")
]

if not roads:
    raise ValueError("No road geometry found.")

fig, axes = plt.subplots(1, 2, figsize=(15, 8))

methods = [
    ("dbscan_cluster", "DBSCAN — 40 m"),
    ("hdbscan_cluster", "HDBSCAN")
]

for ax, (column, title) in zip(axes, methods):
    for road in roads:
        x, y = road.xy if road.geom_type == "LineString" else ([], [])
        if len(x):
            ax.plot(x, y, color="black", linewidth=2, label="Western Avenue")

    for cluster_id in sorted(df[column].dropna().unique()):
        subset = df[df[column] == cluster_id]
        label = "Noise" if cluster_id == -1 else f"Cluster {cluster_id}"
        ax.scatter(
            subset["x"], subset["y"],
            s=45, alpha=0.8, label=label
        )

    ax.set_title(title)
    ax.set_xlabel("Easting (metres)")
    ax.set_ylabel("Northing (metres)")
    ax.legend(fontsize=8)
    ax.set_aspect("equal", adjustable="datalim")

plt.tight_layout()
plt.savefig(
    "western_avenue_dbscan_hdbscan_comparison.png",
    dpi=200,
    bbox_inches="tight"
)
plt.show()

print("Saved western_avenue_dbscan_hdbscan_comparison.png")
