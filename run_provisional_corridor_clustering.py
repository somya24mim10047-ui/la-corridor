
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN

BASE = Path(__file__).parent
DATA_DIR = BASE / "data" / "corridors"
OUT_DIR = BASE / "data" / "clustered" / "provisional_boundary_review"
OUT_DIR.mkdir(parents=True, exist_ok=True)

EARTH_RADIUS_M = 6_371_000
EPS_METERS = 40
MIN_SAMPLES = 4

summary = []

for corridor in [
    "larchmont_boulevard",
    "olympic_boulevard",
    "vermont_avenue",
    "wilshire_boulevard",
]:
    path = DATA_DIR / f"{corridor}_businesses.csv"

    if not path.exists():
        print(f"SKIP: missing {path.name}")
        continue

    df = pd.read_csv(path).dropna(
        subset=["latitude", "longitude"]
    ).copy()

    coords = np.radians(df[["latitude", "longitude"]].to_numpy())

    model = DBSCAN(
        eps=EPS_METERS / EARTH_RADIUS_M,
        min_samples=MIN_SAMPLES,
        metric="haversine",
    )

    df["cluster_id"] = model.fit_predict(coords)

    output = OUT_DIR / f"{corridor}_provisional_clusters.csv"
    df.to_csv(output, index=False)

    cluster_count = df.loc[df.cluster_id != -1, "cluster_id"].nunique()
    noise_count = int((df.cluster_id == -1).sum())

    summary.append({
        "corridor": corridor,
        "business_records": len(df),
        "unique_locations": len(
            df[["latitude", "longitude"]].drop_duplicates()
        ),
        "clusters": int(cluster_count),
        "noise_records": noise_count,
        "noise_percent": round(noise_count / len(df) * 100, 2),
        "eps_meters": EPS_METERS,
        "min_samples": MIN_SAMPLES,
        "status": "PROVISIONAL — not clipped to validated corridor boundaries",
    })

    print(
        f"{corridor}: {len(df)} businesses, "
        f"{cluster_count} clusters, {noise_count} noise records"
    )

summary_df = pd.DataFrame(summary)
summary_path = OUT_DIR / "provisional_clustering_summary.csv"
summary_df.to_csv(summary_path, index=False)

print("\nPROVISIONAL SUMMARY")
print(summary_df.to_string(index=False))
print(f"\nSaved summary: {summary_path}")
print("Original business CSVs and clustering outputs were not modified.")
