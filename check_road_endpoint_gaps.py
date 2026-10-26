import geopandas as gpd
import pandas as pd
from pathlib import Path
from scipy.spatial.distance import cdist

root = Path("data")
out_dir = root / "final_corridor_boundaries"

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    path = (
        root / "boundary_candidates" /
        "complete_road_sources" /
        f"{name}_complete_clean.geojson"
    )

    roads = gpd.read_file(path).to_crs("EPSG:32611")
    lines = [
        geom for geom in roads.geometry
        if geom is not None and not geom.is_empty
    ]

    endpoints = []
    for i, line in enumerate(lines):
        coords = list(line.coords)
        endpoints.append((i, "start", coords[0][0], coords[0][1]))
        endpoints.append((i, "end", coords[-1][0], coords[-1][1]))

    ends = pd.DataFrame(
        endpoints,
        columns=["feature_id", "end_type", "x", "y"]
    )

    xy = ends[["x", "y"]].to_numpy()
    distances = cdist(xy, xy)
    pairs = []

    for i in range(len(ends)):
        for j in range(i + 1, len(ends)):
            if ends.iloc[i]["feature_id"] == ends.iloc[j]["feature_id"]:
                continue
            d = distances[i, j]
            if d <= 100:
                pairs.append({
                    "feature_a": int(ends.iloc[i]["feature_id"]),
                    "end_a": ends.iloc[i]["end_type"],
                    "feature_b": int(ends.iloc[j]["feature_id"]),
                    "end_b": ends.iloc[j]["end_type"],
                    "gap_m": float(d)
                })

    report = pd.DataFrame(pairs)
    if not report.empty:
        report = report.sort_values("gap_m")

    output = out_dir / f"{name}_road_endpoint_gaps.csv"
    report.to_csv(output, index=False)

    print(f"\n=== {name.upper()} ===")
    print("Line features:", len(lines))
    print("Endpoint pairs within 10 m:", int((report["gap_m"] <= 10).sum()) if not report.empty else 0)
    print("Endpoint pairs within 25 m:", int((report["gap_m"] <= 25).sum()) if not report.empty else 0)
    print("Endpoint pairs within 50 m:", int((report["gap_m"] <= 50).sum()) if not report.empty else 0)
    print("Endpoint pairs within 100 m:", len(report))
    print("Saved:", output)
