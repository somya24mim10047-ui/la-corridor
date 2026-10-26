
from pathlib import Path
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.ops import unary_union, linemerge, nearest_points

ROOT = Path(__file__).resolve().parent
ROAD_DIR = ROOT / "data" / "corridors"
OUT_DIR = ROOT / "data" / "boundary_candidates" / "road_gap_maps"
OUT_DIR.mkdir(parents=True, exist_ok=True)

for corridor in ["wilshire_boulevard", "olympic_boulevard"]:
    path = ROAD_DIR / f"{corridor}_road_segments_clean.geojson"
    roads = gpd.read_file(path).to_crs("EPSG:32611")

    lines = [
        geom for geom in roads.geometry
        if geom is not None and not geom.is_empty
    ]
    merged = linemerge(unary_union(lines))

    if merged.geom_type == "LineString":
        components = [merged]
    else:
        components = [
            geom for geom in merged.geoms
            if geom.geom_type == "LineString"
        ]

    fig, ax = plt.subplots(figsize=(15, 8))

    # Plot every component and label its number.
    for i, line in enumerate(components):
        x, y = line.xy
        ax.plot(x, y, linewidth=2, color="steelblue")
        midpoint = line.interpolate(0.5, normalized=True)
        ax.annotate(
            str(i + 1),
            (midpoint.x, midpoint.y),
            fontsize=9,
            fontweight="bold",
            ha="center",
            bbox=dict(boxstyle="circle,pad=0.25",
                      facecolor="white", edgecolor="black")
        )

    # Mark closest points for component pairs within 130 m.
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            a, b = components[i], components[j]
            distance = a.distance(b)

            if distance <= 130:
                p1, p2 = nearest_points(a, b)
                ax.plot(
                    [p1.x, p2.x],
                    [p1.y, p2.y],
                    linestyle="--",
                    color="crimson",
                    linewidth=1.2,
                    alpha=0.8,
                )
                mid_x = (p1.x + p2.x) / 2
                mid_y = (p1.y + p2.y) / 2
                ax.annotate(
                    f"{distance:.0f} m",
                    (mid_x, mid_y),
                    fontsize=8,
                    color="darkred",
                    bbox=dict(facecolor="white", alpha=0.8, edgecolor="none")
                )

    ax.set_title(
        f"{corridor.replace('_', ' ').title()}: Road Components and Nearby Gaps"
    )
    ax.set_xlabel("Easting (m, EPSG:32611)")
    ax.set_ylabel("Northing (m, EPSG:32611)")
    ax.grid(True, alpha=0.2)
    ax.set_aspect("equal", adjustable="datalim")
    fig.tight_layout()

    output = OUT_DIR / f"{corridor}_component_gap_review.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)

    print("Saved:", output)

print("\nDiagnostic maps complete.")
