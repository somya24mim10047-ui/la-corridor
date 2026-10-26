
from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from matplotlib.lines import Line2D

BASE = Path(__file__).resolve().parent
CRS = "EPSG:32611"

CENTERLINE_FILE = BASE / "western_avenue_centerline.geojson"
BUSINESS_FILE = BASE / "western_avenue_businesses.csv"

MAP_FILE = BASE / "western_avenue_final_presentation_map.png"
REPORT_FILE = BASE / "western_avenue_methodology.md"

BUFFER_M = 100

# ------------------------------------------------------------
# 1. Load and project the road centerline
# ------------------------------------------------------------

roads = gpd.read_file(CENTERLINE_FILE).to_crs(CRS)
line = roads.geometry.iloc[0]

if line is None or line.is_empty:
    raise ValueError("The saved centerline is empty.")

boundary = line.buffer(
    BUFFER_M,
    cap_style="flat",
    join_style="round",
)

start = line.interpolate(0)
end = line.interpolate(line.length)

# ------------------------------------------------------------
# 2. Load business records
# ------------------------------------------------------------

df = pd.read_csv(BUSINESS_FILE)
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df = df.dropna(subset=["longitude", "latitude"]).copy()

businesses = gpd.GeoDataFrame(
    df,
    geometry=gpd.points_from_xy(df.longitude, df.latitude),
    crs="EPSG:4326",
).to_crs(CRS)

inside = (
    businesses.geometry.within(boundary)
    | businesses.geometry.touches(boundary)
)

total = len(businesses)
count_inside = int(inside.sum())
coverage = 100 * count_inside / total if total else 0
area_km2 = boundary.area / 1_000_000
length_m = line.length

# ------------------------------------------------------------
# 3. Create presentation map
# ------------------------------------------------------------

fig, ax = plt.subplots(figsize=(12, 9))

# Boundary polygon
gpd.GeoSeries([boundary], crs=CRS).plot(
    ax=ax,
    facecolor="#DCEAF7",
    edgecolor="#245A85",
    linewidth=2,
    alpha=0.8,
    zorder=1,
)

# Business records
if (~inside).any():
    businesses.loc[~inside].plot(
        ax=ax,
        color="#D97706",
        markersize=28,
        marker="x",
        label="Outside boundary",
        zorder=3,
    )

if inside.any():
    businesses.loc[inside].plot(
        ax=ax,
        color="#2878B5",
        markersize=16,
        alpha=0.75,
        label="Business records inside",
        zorder=3,
    )

# Road centerline
gpd.GeoSeries([line], crs=CRS).plot(
    ax=ax,
    color="#202020",
    linewidth=2.5,
    zorder=4,
)

# Endpoints
ax.scatter(
    [start.x, end.x],
    [start.y, end.y],
    color="#B91C1C",
    s=75,
    edgecolor="white",
    linewidth=1,
    zorder=6,
)

# Label positions with small offsets to reduce overlap
ax.annotate(
    "Wilshire Blvd\n(Southern endpoint)",
    (start.x, start.y),
    xytext=(12, -20),
    textcoords="offset points",
    fontsize=9,
    fontweight="bold",
    color="#8B1E1E",
    arrowprops=dict(arrowstyle="->", color="#8B1E1E"),
)

ax.annotate(
    "West 3rd Street\n(Northern endpoint)",
    (end.x, end.y),
    xytext=(12, 12),
    textcoords="offset points",
    fontsize=9,
    fontweight="bold",
    color="#8B1E1E",
    arrowprops=dict(arrowstyle="->", color="#8B1E1E"),
)

# Road label near the middle of the line
mid = line.interpolate(line.length / 2)
ax.text(
    mid.x + 12,
    mid.y,
    "WESTERN AVENUE",
    fontsize=10,
    fontweight="bold",
    rotation=90,
    ha="left",
    va="center",
    bbox=dict(
        boxstyle="round,pad=0.25",
        facecolor="white",
        edgecolor="none",
        alpha=0.85,
    ),
    zorder=7,
)

# North arrow
ax.annotate(
    "N",
    xy=(0.94, 0.94),
    xytext=(0.94, 0.86),
    xycoords="axes fraction",
    textcoords="axes fraction",
    ha="center",
    va="center",
    fontsize=12,
    fontweight="bold",
    arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5),
)

# Approximate scale bar: 100 m in projected CRS
x_min, x_max = ax.get_xlim()
y_min, y_max = ax.get_ylim()
bar_x = x_min + (x_max - x_min) * 0.07
bar_y = y_min + (y_max - y_min) * 0.06

ax.add_line(
    Line2D(
        [bar_x, bar_x + 100],
        [bar_y, bar_y],
        color="black",
        linewidth=3,
    )
)
ax.text(
    bar_x + 50,
    bar_y + (y_max - y_min) * 0.012,
    "100 m",
    ha="center",
    fontsize=9,
)

ax.set_title(
    "Western Avenue Corridor — Proposed Boundary",
    fontsize=16,
    fontweight="bold",
    pad=16,
)

ax.text(
    0.5,
    1.005,
    f"100 m buffer each side | Length {length_m:.1f} m | "
    f"Area {area_km2:.4f} km² | "
    f"Business coverage {count_inside}/{total} ({coverage:.2f}%)",
    transform=ax.transAxes,
    ha="center",
    fontsize=9,
)

ax.set_xlabel("Easting (metres, EPSG:32611)")
ax.set_ylabel("Northing (metres, EPSG:32611)")
ax.set_aspect("equal", adjustable="datalim")
ax.grid(True, linestyle="--", alpha=0.25)
ax.legend(loc="lower right", frameon=True)

fig.text(
    0.01,
    0.01,
    "Source: City of Los Angeles official street centerline and "
    "Listing of Active Businesses dataset. Boundary is a proposed "
    "100 m buffer around the selected road segment.",
    fontsize=8,
)

plt.tight_layout(rect=[0, 0.035, 1, 0.96])
fig.savefig(MAP_FILE, dpi=300, bbox_inches="tight")
plt.close(fig)

print(f"Final map saved: {MAP_FILE}")

# ------------------------------------------------------------
# 4. Write methodology and results report
# ------------------------------------------------------------

report = f"""# Western Avenue Corridor: Boundary Methodology and Results

## 1. Objective
Define and validate a geographic corridor along Western Avenue in Los
Angeles using official road geometry and business-location data.

## 2. Corridor selection
The selected road is Western Avenue, between Wilshire Boulevard and
West 3rd Street. The endpoints are based on the road-network
intersection evidence inspected from the City of Los Angeles street
centerline service.

## 3. Data sources
- City of Los Angeles Street Information road-centerline GIS service.
- City of Los Angeles Listing of Active Businesses dataset.
- Business coordinates and attributes from the locally saved CSV.

## 4. Boundary method
The selected Western Avenue centerline was projected to EPSG:32611,
a metre-based coordinate reference system suitable for this area.
A 100 m buffer was created on each side of the clipped centerline.
Flat end caps were used so the buffer would not extend an extra 100 m
past the selected endpoints.

## 5. Results
- Centerline length: {length_m:.1f} metres
- Buffer on each side: {BUFFER_M} metres
- Boundary area: {area_km2:.4f} square kilometres
- Business records checked: {total}
- Records inside boundary: {count_inside}
- Business-record coverage: {coverage:.2f}%

## 6. Buffer-width comparison
The comparison using the saved centerline produced:

| Buffer each side | Businesses inside | Coverage | Area (km²) |
|---:|---:|---:|---:|
| 50 m | 192/251 | 76.49% | 0.0745 |
| 100 m | 246/251 | 98.01% | 0.1491 |
| 150 m | 248/251 | 98.80% | 0.2236 |
| 200 m | 248/251 | 98.80% | 0.2981 |

The 100 m buffer is a reasonable provisional choice because it captures
98.01% of the collected business records while keeping the mapped area
smaller than the 150 m and 200 m alternatives. Wider buffers add few
business records in this dataset but increase the area substantially.

## 7. Outside-record inspection
Three outside records near 319–321 S Western Avenue are approximately
9.3 m from the centerline but fall beyond the northern endpoint.
Two records at 450 S Western Avenue are approximately 146.2 m from the
centerline and fall outside the 100 m buffer.

The northern endpoint was checked against official road records.
Western Avenue and West 3rd Street share intersection ID 18879 in the
returned road-network attributes.

## 8. Limitations
1. Business coverage describes the records in the collected dataset; it
   does not prove that every included business belongs to the corridor.
2. Business records can have missing categories or shared coordinates.
   These records should not be removed without checking their source.
3. A 100 m buffer is an analytical choice, not a universally correct
   corridor width. It should also be checked against maps, land use,
   pedestrian access, and the project's intended definition of a corridor.
4. The intersection check supports the endpoint choice, but final
   visual inspection of the saved map and source geometry remains important.
5. This analysis does not yet establish business density, employment,
   population, building density, or independent field validation.

## 9. Conclusion
The current boundary is a reproducible, data-informed proposal for the
Western Avenue segment between Wilshire Boulevard and West 3rd Street.
It follows the selected official road centerline and uses a 100 m buffer
on each side. Business coverage and alternative buffer widths provide
supporting evidence, while geographic context and the intended corridor
definition remain important validation criteria.
"""

REPORT_FILE.write_text(report, encoding="utf-8")

print(f"Methodology report saved: {REPORT_FILE}")
print("\nBoth deliverables generated successfully.")
