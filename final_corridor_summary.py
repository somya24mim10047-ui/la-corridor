
import pandas as pd

df = pd.read_csv("western_avenue_unique_location_clusters.csv")
validation = pd.read_csv("western_avenue_cluster_validation.csv")

for method in ["dbscan_cluster", "hdbscan_cluster"]:
    if method not in df.columns:
        continue

    counts = df.groupby(method).size().rename("locations")
    report = counts.reset_index().rename(
        columns={method: "cluster"}
    )

    report["status"] = report["cluster"].apply(
        lambda x: "Noise" if x == -1 else "Cluster"
    )

    details = validation[
        validation["method"] == method
    ].drop(columns="method")

    report = report.merge(details, on="cluster", how="left")
    report["road_alignment_pct"] = (
        report["within_50m"] / report["locations"] * 100
    ).round(1)

    report.to_csv(
        f"western_avenue_final_{method}_summary.csv",
        index=False
    )

    print(f"\n=== {method.upper()} ===")
    print(report.to_string(index=False))

print("\nFinal summary files created.")
