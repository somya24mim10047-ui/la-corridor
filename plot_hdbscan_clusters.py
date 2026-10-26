
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import hdbscan

from pyproj import Transformer

# Load unique business locations
df = pd.read_csv("western_avenue_unique_location_clusters.csv")
df = df.dropna(subset=["longitude", "latitude"]).copy()

# Project coordinates to metres
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

# Run HDBSCAN with the same settings as before
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=4,
    min_samples=4,
    metric="euclidean"
)

df["hdbscan_cluster"] = clusterer.fit_predict(points)

# Plot clusters
plt.figure(figsize=(10, 8))

for cluster in sorted(df["hdbscan_cluster"].unique()):
    group = df[df["hdbscan_cluster"] == cluster]

    label = "Noise" if cluster == -1 else f"Cluster {cluster}"

    plt.scatter(
        group["longitude"],
        group["latitude"],
        label=label,
        s=45,
        alpha=0.8
    )

plt.title("Western Avenue: HDBSCAN Unique Locations")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig("western_avenue_hdbscan_clusters.png", dpi=200)
plt.show()

df.to_csv("western_avenue_hdbscan_unique_clusters.csv", index=False)

print("Map saved: western_avenue_hdbscan_clusters.png")
print("Cluster data saved: western_avenue_hdbscan_unique_clusters.csv")
