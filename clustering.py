
import numpy as np
import pandas as pd

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import silhouette_score


def prepare_data(df):
    """Clean the business coordinates."""
    df = df.copy()

    df["latitude"] = pd.to_numeric(
        df["latitude"], errors="coerce"
    )
    df["longitude"] = pd.to_numeric(
        df["longitude"], errors="coerce"
    )

    df = df.dropna(
        subset=["latitude", "longitude"]
    )

    df = df[
        df["latitude"].between(-90, 90)
        & df["longitude"].between(-180, 180)
    ]

    df = df.drop_duplicates(
        subset=["latitude", "longitude", "business_name"]
    )

    df["primary_naics_description"] = (
        df["primary_naics_description"]
        .fillna("Unknown")
    )

    return df.reset_index(drop=True)


def run_dbscan(df, eps=100, min_samples=4):
    """
    Cluster business locations using DBSCAN.

    eps is in metres.
    """
    df = prepare_data(df)

    if len(df) < min_samples:
        raise ValueError("Not enough records for these settings.")

    # LA is projected into UTM Zone 11N.
    coords = df[["longitude", "latitude"]].to_numpy()

    from pyproj import Transformer

    transformer = Transformer.from_crs(
        "EPSG:4326", "EPSG:32611",
        always_xy=True
    )

    x, y = transformer.transform(
        coords[:, 0], coords[:, 1]
    )

    xy = np.column_stack((x, y))

    model = DBSCAN(
        eps=eps,
        min_samples=min_samples
    )

    df["cluster"] = model.fit_predict(xy)

    return df


def cluster_summary(df):
    """Summarize clusters and unassigned noise points."""
    result = []

    for cluster_id, group in df.groupby("cluster"):
        result.append({
            "cluster": int(cluster_id),
            "businesses": len(group),
            "categories": group[
                "primary_naics_description"
            ].nunique(),
            "noise": cluster_id == -1
        })

    return pd.DataFrame(result)


def suggest_eps(df, min_samples=4):
    """Estimate a useful starting distance in metres."""
    from pyproj import Transformer

    df = prepare_data(df)

    coords = df[["longitude", "latitude"]].to_numpy()

    transformer = Transformer.from_crs(
        "EPSG:4326", "EPSG:32611",
        always_xy=True
    )

    x, y = transformer.transform(
        coords[:, 0], coords[:, 1]
    )

    xy = np.column_stack((x, y))

    if len(xy) <= min_samples:
        return 100

    neighbors = NearestNeighbors(
        n_neighbors=min_samples
    ).fit(xy)

    distances, _ = neighbors.kneighbors(xy)

    return float(np.median(distances[:, -1]))
