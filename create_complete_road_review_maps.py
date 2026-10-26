
from pathlib import Path
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent

SOURCE_DIR = BASE / "data" / "boundary_candidates" / "complete_road_sources"
CANDIDATE_DIR = BASE / "data" / "boundary_candidates" / "complete_road_candidates"
BUSINESS_DIR = BASE / "data" / "corridors"
OUTPUT_DIR = BASE / "data" / "boundary_candidates" / "complete_road_review_maps"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CORRIDORS = {
    "wilshire_boulevard": "Wilshire Boulevard",
    "olympic_boulevard": "Olympic Boulevard",
}

WIDTHS = [50, 100, 150]

for corridor, display_name in CORRIDORS.items():
    road_file = SOURCE_DIR / f"{corridor}_complete_clean.geojson"
    business_file = BUSINESS_DIR / f"{corridor}_businesses.csv"

    if not road_file.exists():
        print(f"Missing road source: {road_file}")
        continue

    if not business_file.exists():
        print(f"Missing business file: {business_file}")
        continue

    roads = gpd.read_file(road_file).to_crs("EPSG:32611")
    businesses_df = pd.read_csv(business_file)

    required = {"longitude", "latitude"}
    if not required.issubset(businesses_df.columns):
        print(f"Missing longitude/latitude columns in {business_file}")
        print(f"Available columns: {list(businesses_df.columns)}")
        continue

    businesses_df["longitude"] = pd.to_numeric(
        businesses_df["longitude"], errors="coerce"
    )
    businesses_df["latitude"] = pd.to_numeric(
        businesses_df["latitude"], errors="coerce"
    )
    businesses_df = businesses_df.dropna(
        subset=["longitude", "latitude"]
    ).copy()

    businesses = gpd.GeoDataFrame(
        businesses_df,
        geometry=gpd.points_from_xy(
            businesses_df["longitude"],
            businesses_df["latitude"],
        ),
        crs="EPSG:4326",
    ).to_crs("EPSG:32611")

    road_union = roads.geometry.union_all()

    for width in WIDTHS:
        candidate_file = (
            CANDIDATE_DIR
            / f"{corridor}_{width}m_complete_candidate.geojson"
        )

        if not candidate_file.exists():
            print(f"Missing candidate: {candidate_file}")
            continue

        boundary = gpd.read_file(candidate_file).to_crs("EPSG:32611")
        boundary_union = boundary.geometry.union_all()

        inside_mask = businesses.geometry.intersects(boundary_union)
        inside = businesses.loc[inside_mask]
        outside = businesses.loc[~inside_mask]

        fig, ax = plt.subplots(figsize=(12, 10))

        # Candidate boundary
        boundary.plot(
            ax=ax,
            facecolor="lightblue",
            edgecolor="blue",
            alpha=0.35,
            linewidth=1.5,
        )

        # Complete official road geometry
        roads.plot(
            ax=ax,
            color="black",
            linewidth=1.3,
        )

        # Business locations
        if not inside.empty:
            inside.plot(
                ax=ax,
                color="green",
                markersize=8,
                alpha=0.65,
                label=f"Inside buffer ({len(inside)})",
            )

        if not outside.empty:
            outside.plot(
                ax=ax,
                color="red",
                markersize=18,
                alpha=0.9,
                label=f"Outside buffer ({len(outside)})",
            )

        percent = 100 * len(inside) / len(businesses)

        ax.set_title(
            f"{display_name} — {width} m Candidate Buffer\n"
            f"{len(inside)}/{len(businesses)} businesses inside "
            f"({percent:.2f}%)",
            fontsize=13,
        )
        ax.set_xlabel("Easting (m)")
        ax.set_ylabel("Northing (m)")
        ax.legend(loc="best")
        ax.set_aspect("equal", adjustable="datalim")

        output_file = (
            OUTPUT_DIR / f"{corridor}_{width}m_review.png"
        )

        plt.tight_layout()
        plt.savefig(output_file, dpi=200, bbox_inches="tight")
        plt.close(fig)

        print(f"Saved: {output_file}")

print("\nReview-map generation complete.")
