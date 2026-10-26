
import pandas as pd
import numpy as np
import hdbscan

from sklearn.cluster import DBSCAN
from pyproj import Transformer


def run_corridor_pipeline(
    csv_path,
    output_prefix,
    eps=40,
    min_samples=4,
    min_cluster_size=4
):
    """
    Run DBSCAN and HDBSCAN on business coordinates.
    Save business-level and unique-location results.
    """

    # Load business data
    df = pd.read_csv(csv_path)

    required = {"longitude", "latitude"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    df = df.dropna(
        subset=["longitude", "latitude"]
    ).copy()

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

    # Business-level clustering
    df["dbscan_cluster"] = DBSCAN(
        eps=eps,
        min_samples=min_samples
    ).fit_predict(points)

    df["hdbscan_cluster"] = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean"
    ).fit_predict(points)

    # Save business-level results
    df.to_csv(
        f"{output_prefix}_business_clusters.csv",
        index=False
    )

    # Unique coordinates: keep a representative row per location
    unique = df.drop_duplicates(
        subset=["longitude", "latitude"]
    ).copy()

    ux, uy = transformer.transform(
        unique["longitude"].to_numpy(),
        unique["latitude"].to_numpy()
    )
    unique_points = np.column_stack((ux, uy))

    unique["dbscan_cluster"] = DBSCAN(
        eps=eps,
        min_samples=min_samples
    ).fit_predict(unique_points)

    unique["hdbscan_cluster"] = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean"
    ).fit_predict(unique_points)

    unique.to_csv(
        f"{output_prefix}_unique_location_clusters.csv",
        index=False
    )

    # Summary for both datasets
    summaries = []

    for dataset_name, result in [
        ("Business records", df),
        ("Unique locations", unique)
    ]:
        for method in ["dbscan_cluster", "hdbscan_cluster"]:
            labels = result[method]

            summaries.append({
                "dataset": dataset_name,
                "method": method.replace("_cluster", "").upper(),
                "records": len(result),
                "clusters": len(set(labels) - {-1}),
                "noise": int((labels == -1).sum())
            })

    summary = pd.DataFrame(summaries)
    summary.to_csv(
        f"{output_prefix}_summary.csv",
        index=False
    )

    print("\n=== Corridor Pipeline Summary ===")
    print(summary.to_string(index=False))
    print("\nFiles saved with prefix:", output_prefix)

    return summary


if __name__ == "__main__":
    run_corridor_pipeline(
        csv_path="western_avenue_businesses.csv",
        output_prefix="western_avenue",
        eps=40,
        min_samples=4,
        min_cluster_size=4
    )
