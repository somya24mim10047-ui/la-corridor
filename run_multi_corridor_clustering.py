
from pathlib import Path
import pandas as pd
from sklearn.cluster import DBSCAN
import numpy as np

BASE = Path(__file__).parent
DATA_DIR = BASE / "data" / "corridors"
OUTPUT_DIR = BASE / "data" / "clustered"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 40 metres; haversine distance uses radians.
EARTH_RADIUS_M = 6_371_000
EPS_METERS = 40
MIN_SAMPLES = 4

summary = []

for file in DATA_DIR.glob("*_businesses.csv"):
    print(f"\nProcessing {file.name}...")

    df = pd.read_csv(file)
    df = df.dropna(subset=["latitude", "longitude"]).copy()

    if len(df) == 0:
        print("Skipped: no records with coordinates.")
        continue

    # DBSCAN with geographic coordinates in radians.
    coords = np.radians(df[["latitude", "longitude"]].to_numpy())

    model = DBSCAN(
        eps=EPS_METERS / EARTH_RADIUS_M,
        min_samples=MIN_SAMPLES,
        metric="haversine"
    )

    df["cluster_id"] = model.fit_predict(coords)

    output_file = OUTPUT_DIR / file.name.replace(
        "_businesses.csv", "_clusters.csv"
    )
    df.to_csv(output_file, index=False)

    cluster_ids = set(df["cluster_id"])
    cluster_count = len(cluster_ids - {-1})
    noise_count = int((df["cluster_id"] == -1).sum())

    summary.append({
        "corridor": file.stem.replace("_businesses", ""),
        "business_records": len(df),
        "unique_locations": len(
            df[["latitude", "longitude"]].drop_duplicates()
        ),
        "clusters": cluster_count,
        "noise_records": noise_count,
        "noise_percent": round(noise_count / len(df) * 100, 2),
        "eps_meters": EPS_METERS,
        "min_samples": MIN_SAMPLES,
    })

    print(f"Businesses: {len(df)}")
    print(f"Clusters: {cluster_count}")
    print(f"Noise records: {noise_count}")
    print(f"Saved: {output_file.name}")

summary_df = pd.DataFrame(summary)
summary_file = OUTPUT_DIR / "multi_corridor_clustering_summary.csv"
summary_df.to_csv(summary_file, index=False)

print("\n=== MULTI-CORRIDOR SUMMARY ===")
print(summary_df.to_string(index=False))
print(f"\nSummary saved: {summary_file}")
