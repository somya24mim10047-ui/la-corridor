
import json
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import shape
from shapely.ops import transform as project_geometry
from pyproj import Transformer

df = pd.read_csv("western_avenue_unique_location_clusters.csv")

transformer = Transformer.from_crs(
    "EPSG:4326", "EPSG:32611", always_xy=True
)
df["x"], df["y"] = transformer.transform(
    df["longitude"].to_numpy(),
    df["latitude"].to_numpy()
)

with open("western_avenue_centerline.geojson", encoding="utf-8") as f:
    data = json.load(f)

features = data.get("features", [])
if data.get("type") == "Feature":
    features = [data]

fig, ax = plt.subplots(figsize=(12, 8))

for feature in features:
    if not feature.get("geometry"):
        continue
    road = project_geometry(
        transformer.transform, shape(feature["geometry"])
    )
    if road.geom_type == "LineString":
        x, y = road.xy
        ax.plot(x, y, color="black", linewidth=3, label="Western Avenue")
    elif road.geom_type == "MultiLineString":
        for line in road.geoms:
            x, y = line.xy
            ax.plot(x, y, color="black", linewidth=3)

column = "dbscan_cluster"
if column not in df.columns:
    column = "cluster"
if column not in df.columns:
    raise ValueError("No DBSCAN cluster column found in the CSV.")

for cluster_id in sorted(df[column].dropna().unique()):
    part = df[df[column] == cluster_id]
    label = "Noise / unassigned" if cluster_id == -1 else f"Cluster {cluster_id}"
    ax.scatter(part["x"], part["y"], s=45, label=label)

ax.set_title("Western Avenue: Business Clusters and Road Alignment")
ax.set_xlabel("Easting (metres)")
ax.set_ylabel("Northing (metres)")
ax.legend()
ax.set_aspect("equal", adjustable="datalim")
plt.tight_layout()
plt.savefig("western_avenue_final_corridor_map.png", dpi=200)
plt.show()

print("Saved western_avenue_final_corridor_map.png")
