
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parent
ROAD_DIR = ROOT / "data" / "corridors"
BOUNDARY_DIR = ROOT / "data" / "boundary_candidates"
BUSINESS_DIR = ROOT / "data" / "corridors"
OUTPUT_DIR = BOUNDARY_DIR / "clean_review_maps"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CORRIDORS = [
    "wilshire_boulevard",
    "olympic_boulevard",
    "vermont_avenue",
    "larchmont_boulevard",
]

METRIC_CRS = "EPSG:32611"

for corridor in CORRIDORS:
    business_file = BUSINESS_DIR / f"{corridor}_businesses.csv"
    road_file = ROAD_DIR / f"{corridor}_road_segments_clean.geojson"

    if not business_file.exists() or not road_file.exists():
        print(f"SKIPPED {corridor}: missing business or road file")
        continue

    df = pd.read_csv(business_file)
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df = df.dropna(subset=["longitude", "latitude"])

    businesses = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    ).to_crs(METRIC_CRS)

    roads = gpd.read_file(road_file).to_crs(METRIC_CRS)

    for width in [50, 100, 150]:
        boundary_file = (
            BOUNDARY_DIR / f"{corridor}_{width}m_clean_candidate.geojson"
        )

        if not boundary_file.exists():
            print(f"Missing candidate: {boundary_file.name}")
            continue

        boundary = gpd.read_file(boundary_file).to_crs(METRIC_CRS)
        polygon = boundary.geometry.union_all()

        inside = businesses.geometry.intersects(polygon)
        outside = ~inside

        fig, ax = plt.subplots(figsize=(12, 9))

        boundary.plot(
            ax=ax, color="lightblue", edgecolor="steelblue",
            alpha=0.35, linewidth=1, label=f"{width} m candidate"
        )
        businesses.loc[outside].plot(
            ax=ax, color="red", markersize=9,
            alpha=0.65, label="Outside candidate"
        )
        businesses.loc[inside].plot(
            ax=ax, color="seagreen", markersize=7,
            alpha=0.55, label="Inside candidate"
        )
        roads.plot(
            ax=ax, color="black", linewidth=1.8,
            label="Official road segments"
        )

        percent = 100 * inside.sum() / len(businesses) if len(businesses) else 0

        ax.set_title(
            f"{corridor.replace('_', ' ').title()} — {width} m candidate\n"
            f"{inside.sum()} of {len(businesses)} business records inside "
            f"({percent:.2f}%)"
        )
        ax.set_xlabel("Easting (metres)")
        ax.set_ylabel("Northing (metres)")
        ax.legend(loc="best")
        ax.set_aspect("equal")
        ax.grid(alpha=0.2)

        output = OUTPUT_DIR / f"{corridor}_{width}m.png"
        fig.savefig(output, dpi=180, bbox_inches="tight")
        plt.close(fig)

        print(f"Saved: {output}")

print("\nMap generation complete.")
