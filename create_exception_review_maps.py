
from pathlib import Path
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
ROAD_DIR = BASE / "data" / "boundary_candidates" / "complete_road_sources"
AUDIT_DIR = BASE / "data" / "boundary_candidates" / "all_corridor_audit"
OUT_DIR = AUDIT_DIR / "exception_review_maps"
OUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "wilshire_boulevard": (
        "wilshire_boulevard_outside_150m.csv", 350
    ),
    "olympic_boulevard": (
        "olympic_boulevard_outside_100m.csv", 1400
    ),
    "vermont_avenue": (
        "vermont_avenue_outside_100m.csv", 600
    ),
}

for corridor, (csv_name, padding) in FILES.items():
    road_file = ROAD_DIR / f"{corridor}_complete_clean.geojson"
    exception_file = AUDIT_DIR / csv_name

    roads = gpd.read_file(road_file).to_crs("EPSG:32611")
    df = pd.read_csv(exception_file)

    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs="EPSG:4326",
    ).to_crs("EPSG:32611")

    fig, ax = plt.subplots(figsize=(11, 9))
    roads.plot(ax=ax, color="black", linewidth=1.2)

    points.plot(
        ax=ax, color="red", markersize=55,
        edgecolor="white", linewidth=0.8
    )

    for _, row in points.iterrows():
        label = str(row["business_name"])[:35]
        ax.annotate(
            label,
            (row.geometry.x, row.geometry.y),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=7,
        )

    minx, miny, maxx, maxy = points.total_bounds
    ax.set_xlim(minx - padding, maxx + padding)
    ax.set_ylim(miny - padding, maxy + padding)
    ax.set_title(
        f"{corridor.replace('_', ' ').title()} — Exception review\n"
        "Black = retrieved official road geometry; red = outside business"
    )
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.tight_layout()

    output = OUT_DIR / f"{corridor}_exceptions.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output}")

print("\nException maps created.")
