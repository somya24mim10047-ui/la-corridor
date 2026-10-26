
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path
from shapely.geometry import Point

BASE_DIR = Path(__file__).resolve().parent

BUSINESS_FILE = BASE_DIR / "western_avenue_businesses.csv"
CENTERLINE_FILE = BASE_DIR / "western_avenue_centerline.geojson"

WIDTHS = [50, 100, 150, 200]

# Load business locations and official centerline.
businesses = pd.read_csv(BUSINESS_FILE)
centerline_gdf = gpd.read_file(CENTERLINE_FILE)

businesses = businesses.dropna(
    subset=["longitude", "latitude"]
).copy()

business_points = gpd.GeoDataFrame(
    businesses,
    geometry=gpd.points_from_xy(
        businesses["longitude"],
        businesses["latitude"],
    ),
    crs="EPSG:4326",
).to_crs("EPSG:32611")

centerline = centerline_gdf.to_crs("EPSG:32611").geometry.iloc[0]

results = []

for width in WIDTHS:
    boundary = centerline.buffer(
        width,
        cap_style="flat",
        join_style="round",
    )

    inside = (
        business_points.geometry.within(boundary)
        | business_points.geometry.touches(boundary)
    )

    total = len(business_points)
    count = int(inside.sum())
    percentage = count / total * 100 if total else 0

    results.append({
        "buffer_each_side_m": width,
        "businesses_inside": count,
        "total_businesses": total,
        "percentage_inside": round(percentage, 2),
        "boundary_area_km2": round(
            boundary.area / 1_000_000, 4
        ),
    })

    print(
        f"{width} m buffer: {count}/{total} businesses "
        f"({percentage:.2f}%)"
    )

results_df = pd.DataFrame(results)
output_csv = BASE_DIR / "western_avenue_width_comparison_updated.csv"
results_df.to_csv(output_csv, index=False)

print("\nComparison table:")
print(results_df.to_string(index=False))
print(f"\nSaved: {output_csv}")

# Plot business coverage against buffer width.
fig, ax = plt.subplots(figsize=(8, 5))

ax.plot(
    results_df["buffer_each_side_m"],
    results_df["percentage_inside"],
    marker="o",
)

ax.set_title("Western Avenue: Boundary Width Validation")
ax.set_xlabel("Buffer on each side (metres)")
ax.set_ylabel("Businesses inside boundary (%)")
ax.set_ylim(0, 105)
ax.grid(True, alpha=0.3)

plt.tight_layout()

output_png = BASE_DIR / "western_avenue_width_comparison_updated.png"
fig.savefig(output_png, dpi=200, bbox_inches="tight")
plt.close(fig)

print(f"Graph saved: {output_png}")
