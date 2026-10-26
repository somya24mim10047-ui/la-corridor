
import pandas as pd
import matplotlib.pyplot as plt
from clustering import run_dbscan

# Load Western Avenue business data
df = pd.read_csv("western_avenue_businesses.csv")

# Run DBSCAN using the provisional 40 m threshold
result = run_dbscan(df, eps=40, min_samples=4)

# Plot each cluster
plt.figure(figsize=(10, 8))

clusters = sorted(result["cluster"].unique())
colors = plt.get_cmap("tab10")

for i, cluster_id in enumerate(clusters):
    group = result[result["cluster"] == cluster_id]

    if cluster_id == -1:
        color = "black"
        label = "Noise"
    else:
        color = colors(i % 10)
        label = f"Cluster {cluster_id}"

    plt.scatter(
        group["longitude"],
        group["latitude"],
        color=color,
        label=label,
        s=35,
        alpha=0.8
    )

plt.title("Western Avenue Business Clusters (DBSCAN, eps=40 m)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("western_avenue_dbscan_40m.png", dpi=300)
plt.show()

result.to_csv("western_avenue_clustered_40m.csv", index=False)

print("Map saved as western_avenue_dbscan_40m.png")
print("Clustered data saved as western_avenue_clustered_40m.csv")
