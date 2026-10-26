
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

BASE = Path(__file__).parent
INPUT_DIR = BASE / "data" / "corridors"
OUTPUT_DIR = BASE / "data" / "clustered"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EARTH_RADIUS_M = 6_371_000
EPS_VALUES = [25, 40, 60]
MIN_SAMPLES = 4

sources = {}

# Existing Western Avenue pilot
western = BASE / "western_avenue_businesses.csv"
if western.exists():
    sources["western_avenue"] = western

# Four additional corridors
for path in INPUT_DIR.glob("*_businesses.csv"):
    sources[path.stem.replace("_businesses", "")] = path

if not sources:
    raise FileNotFoundError("No corridor business CSV files found.")

summary = []

for corridor, path in sorted(sources.items()):
    print(f"\nProcessing: {corridor}")

    df = pd.read_csv(path)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).copy()

    if df.empty:
        print("Skipped: no valid coordinates.")
        continue

    # Cluster unique coordinates to avoid duplicate businesses
    # at one location artificially increasing density.
    locations = (
        df[["latitude", "longitude"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    coords = np.radians(
        locations[["latitude", "longitude"]].to_numpy()
    )

    for eps_m in EPS_VALUES:
        model = DBSCAN(
            eps=eps_m / EARTH_RADIUS_M,
            min_samples=MIN_SAMPLES,
            metric="haversine"
        )

        locations[f"cluster_{eps_m}m"] = model.fit_predict(coords)

        labels = locations[["latitude", "longitude",
                            f"cluster_{eps_m}m"]]

        # Attach each unique location's label to its business records.
        df = df.merge(
            labels,
            on=["latitude", "longitude"],
            how="left",
            validate="many_to_one"
        )

        cluster_col = f"cluster_{eps_m}m"
        cluster_count = locations.loc[
            locations[cluster_col] != -1, cluster_col
        ].nunique()

        noise_locations = int(
            (locations[cluster_col] == -1).sum()
        )
        noise_businesses = int((df[cluster_col] == -1).sum())

        summary.append({
            "corridor": corridor,
            "eps_meters": eps_m,
            "min_samples": MIN_SAMPLES,
            "business_records": len(df),
            "unique_locations": len(locations),
            "clusters": int(cluster_count),
            "noise_locations": noise_locations,
            "noise_business_records": noise_businesses,
            "noise_location_percent": round(
                noise_locations / len(locations) * 100, 2
            ),
        })

    output_file = OUTPUT_DIR / f"{corridor}_sensitivity.csv"
    df.to_csv(output_file, index=False)
    print(f"Saved {output_file.name}")

summary_df = pd.DataFrame(summary)
summary_file = OUTPUT_DIR / "cluster_parameter_comparison.csv"
summary_df.to_csv(summary_file, index=False)

print("\n=== CLUSTER PARAMETER COMPARISON ===")
print(summary_df.to_string(index=False))
print(f"\nSummary saved to: {summary_file}")
