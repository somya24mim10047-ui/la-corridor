
from pathlib import Path
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
CANDIDATE_DIR = BASE / "data" / "boundary_candidates" / "complete_road_candidates"
BUSINESS_DIR = BASE / "data" / "corridors"
OUT_DIR = BASE / "data" / "boundary_candidates" / "complete_road_review_maps"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CORRIDORS = {
    "vermont_avenue": "vermont_avenue_businesses.csv",
    "larchmont_boulevard": "larchmont_boulevard_businesses.csv",
}

WIDTHS = [50, 100, 150]

for corridor, business_filename in CORRIDORS.items():
    road_file = (
        BASE / "data" / "boundary_candidates"
        / "complete_road_sources"
        / f"{corridor}_complete_clean.geojson"
    )
    business_file = BUSINESS_DIR / business_filename

    if not road_file.exists():
        print(f"SKIP: road file missing: {road_file}")
        continue
    if not business_file.exists():
        print(f"SKIP: business file missing: {business_file}")
        continue

    roads = gpd.read_file(road_file)
    businesses = pd.read_csv(business_file)

    required = {"longitude", "latitude"}
    if not required.issubset(businesses.columns):
        print(f"SKIP: missing longitude/latitude in {business_file}")
        continue

    businesses = businesses.dropna(
        subset=["longitude", "latitude"]
    ).copy()

    points = gpd.GeoDataFrame(
        businesses,
        geometry=gpd.points_from_xy(
            businesses["longitude"], businesses["latitude"]
        ),
        crs="EPSG:4326",
    )

    roads_m = roads.to_crs("EPSG:32611")
    points_m = points.to_crs("EPSG:32611")

    # Union official road geometry to measure distance to the actual roads.
    road_union = roads_m.geometry.union_all()
    distances = points_m.geometry.distance(road_union)

    for width in WIDTHS:
        inside = distances <= width

        fig, ax = plt.subplots(figsize=(12, 10))

        # Buffer is for visual inspection only; it is not the final boundary.
        buffer = gpd.GeoSeries(
            [road_union.buffer(width)], crs=roads_m.crs
        )
        buffer.plot(ax=ax, color="cornflowerblue", alpha=0.25)

        roads_m.plot(
            ax=ax, color="black", linewidth=1.2,
            label="Official road geometry"
        )

        points_m.loc[inside].plot(
            ax=ax, color="green", markersize=8,
            alpha=0.65, label="Businesses inside"
        )
        points_m.loc[~inside].plot(
            ax=ax, color="red", markersize=12,
            alpha=0.8, label="Businesses outside"
        )

        ax.set_title(
            f"{corridor.replace('_', ' ').title()} — {width} m candidate\n"
            f"{inside.sum()}/{len(points_m)} businesses inside "
            f"({inside.mean() * 100:.2f}%)"
        )
        ax.set_axis_off()
        ax.legend(loc="best")
        fig.tight_layout()

        output = OUT_DIR / f"{corridor}_{width}m_review.png"
        fig.savefig(output, dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {output}")

print("\nRemaining corridor review maps generated.")
