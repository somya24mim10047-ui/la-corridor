
from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.ops import unary_union, linemerge

BASE = Path(__file__).parent
DATA = BASE / "data" / "corridors"
CANDIDATES = BASE / "data" / "boundary_candidates"
MAPS = CANDIDATES / "review_maps"
MAPS.mkdir(parents=True, exist_ok=True)

CORRIDORS = [
    "wilshire_boulevard",
    "olympic_boulevard",
    "vermont_avenue",
    "larchmont_boulevard",
]

METRIC_CRS = "EPSG:32611"

for name in CORRIDORS:
    print(f"\nReviewing {name}...")

    road_file = DATA / f"{name}_road_segments.geojson"
    business_file = DATA / f"{name}_businesses.csv"
    boundary_file = CANDIDATES / f"{name}_50m_candidate.geojson"

    missing = [
        str(path.name)
        for path in [road_file, business_file, boundary_file]
        if not path.exists()
    ]
    if missing:
        print("Skipped; missing files:", ", ".join(missing))
        continue

    roads = gpd.read_file(road_file).to_crs(METRIC_CRS)
    boundary = gpd.read_file(boundary_file).to_crs(METRIC_CRS)
    df = pd.read_csv(business_file).dropna(
        subset=["longitude", "latitude"]
    )

    points = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df["longitude"], df["latitude"]
        ),
        crs="EPSG:4326",
    ).to_crs(METRIC_CRS)

    polygon = unary_union(boundary.geometry)
    road_union = unary_union(roads.geometry)
    merged_roads = linemerge(road_union)

    # Count connected line components after dissolving shared geometry.
    if merged_roads.geom_type == "LineString":
        component_count = 1
    elif merged_roads.geom_type == "MultiLineString":
        component_count = len(merged_roads.geoms)
    elif merged_roads.geom_type == "GeometryCollection":
        component_count = sum(
            1 for g in merged_roads.geoms
            if g.geom_type in ("LineString", "MultiLineString")
        )
    else:
        component_count = 0

    inside = points.geometry.intersects(polygon)
    print("Source road features:", len(roads))
    print("Dissolved road geometry type:", road_union.geom_type)
    print("Merged line component count:", component_count)
    print("Road length (km):",
          round(roads.geometry.length.sum() / 1000, 2))
    print("Businesses inside 50 m candidate:",
          f"{int(inside.sum())}/{len(points)}")

    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot the candidate boundary and actual retrieved road segments.
    boundary.boundary.plot(
        ax=ax, color="black", linewidth=1.2,
        label="50 m candidate boundary"
    )
    roads.plot(
        ax=ax, color="blue", linewidth=1.5,
        label="Retrieved road segments"
    )

    points.loc[inside].plot(
        ax=ax, color="green", markersize=7,
        alpha=0.65, label="Businesses inside"
    )
    points.loc[~inside].plot(
        ax=ax, color="red", markersize=12,
        alpha=0.9, label="Businesses outside"
    )

    ax.set_title(f"{name.replace('_', ' ').title()} — 50 m Candidate")
    ax.set_axis_off()
    ax.legend(loc="best")
    plt.tight_layout()

    output = MAPS / f"{name}_50m_review.png"
    plt.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print("Saved map:", output)

print("\nVisual review maps created.")
print("Inspect road continuity and geographic extent before finalizing boundaries.")
