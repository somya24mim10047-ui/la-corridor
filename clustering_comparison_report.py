
import pandas as pd

# Load both clustering outputs
businesses = pd.read_csv("western_avenue_clustered.csv")
unique = pd.read_csv("western_avenue_unique_location_clusters.csv")
alignment = pd.read_csv("western_avenue_unique_location_alignment.csv")

def metrics(df, label):
    clusters = df.loc[df["cluster"] != -1, "cluster"].nunique()
    noise = (df["cluster"] == -1).sum()

    result = {
        "approach": label,
        "records": len(df),
        "clusters": clusters,
        "noise_records": int(noise),
    }

    return result

report = pd.DataFrame([
    metrics(businesses, "All business records"),
    metrics(unique, "Unique coordinate pairs"),
])

# Add overall road-alignment metrics
road_metrics = {
    "unique_locations_within_25m": int(
        (alignment["road_distance_m"] <= 25).sum()
    ),
    "unique_locations_within_50m": int(
        (alignment["road_distance_m"] <= 50).sum()
    ),
    "median_unique_location_distance_m": round(
        alignment["road_distance_m"].median(), 2
    ),
}

print("=== Clustering Comparison ===")
print(report.to_string(index=False))

print("\n=== Unique-Location Road Alignment ===")
for key, value in road_metrics.items():
    print(f"{key}: {value}")

report.to_csv("western_avenue_clustering_comparison.csv", index=False)

pd.DataFrame([road_metrics]).to_csv(
    "western_avenue_road_alignment_metrics.csv", index=False
)

print("\nSaved comparison and alignment metric CSV files.")
