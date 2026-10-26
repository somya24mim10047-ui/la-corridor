
import requests
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path
from shapely.geometry import (
    shape,
    Point,
    LineString,
    MultiLineString,
    mapping,
)
from shapely.ops import linemerge, substring
from pyproj import Transformer


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SERVICE_URL = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

# Five connected official Western Avenue road segments.
ROAD_IDS = [137008, 124436, 84883, 134991, 141603]

# Western Avenue at Wilshire Boulevard.
START = (-118.309098, 34.061698)

# Western Avenue near West 3rd Street.
END = (-118.309011, 34.068419)

BUFFER_METERS = 100

BUSINESS_FILE = BASE_DIR / "western_avenue_businesses.csv"

OUTPUT_GEOJSON = BASE_DIR / "western_avenue_final_boundary.geojson"
OUTPUT_PNG = BASE_DIR / "western_avenue_final_boundary.png"


# ============================================================
# 2. DOWNLOAD EACH ROAD SEGMENT INDIVIDUALLY
# ============================================================

def download_road_segments():
    features = []

    print("Downloading selected official road segments...")

    for road_id in ROAD_IDS:
        params = {
            "where": f"OBJECTID={road_id}",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": 4326,
            "f": "geojson",
        }

        response = requests.get(
            SERVICE_URL,
            params=params,
            timeout=60,
        )
        response.raise_for_status()

        result = response.json()

        if "error" in result:
            raise RuntimeError(
                f"GIS service error for OBJECTID {road_id}: "
                f"{result['error']}"
            )

        returned = result.get("features", [])

        if not returned:
            raise RuntimeError(
                f"Road OBJECTID {road_id} was not returned."
            )

        feature = returned[0]
        actual_id = feature.get("properties", {}).get("OBJECTID")

        if actual_id is not None and int(actual_id) != road_id:
            raise RuntimeError(
                f"Requested OBJECTID {road_id}, "
                f"but received {actual_id}."
            )

        features.extend(returned)
        print(f"Retrieved road segment: {road_id}")

    if len(features) != len(ROAD_IDS):
        raise RuntimeError(
            f"Expected {len(ROAD_IDS)} segments, "
            f"received {len(features)}."
        )

    print(f"Total road segments retrieved: {len(features)}")

    return features


# ============================================================
# 3. BUILD A CONNECTED ROAD CENTERLINE
# ============================================================

def build_centerline(features):
    geometries = []

    for feature in features:
        geometry_data = feature.get("geometry")

        if geometry_data:
            geometries.append(shape(geometry_data))

    if not geometries:
        raise RuntimeError("No road geometries were downloaded.")

    merged = linemerge(MultiLineString(geometries))

    if isinstance(merged, LineString):
        centerline = merged

    elif isinstance(merged, MultiLineString):
        # Choose the longest connected line if the service returns
        # more than one line component.
        centerline = max(merged.geoms, key=lambda line: line.length)

        print(
            "Warning: multiple line components found; "
            "using the longest connected component."
        )

    else:
        raise RuntimeError(
            f"Unexpected merged geometry: {merged.geom_type}"
        )

    if centerline.is_empty or centerline.length == 0:
        raise RuntimeError("The merged centerline is empty.")

    return centerline


# ============================================================
# 4. CLIP THE CENTERLINE BETWEEN THE SELECTED ENDPOINTS
# ============================================================

def clip_centerline(centerline):
    # EPSG:32611 is a metre-based projected CRS suitable for LA.
    to_projected = Transformer.from_crs(
        "EPSG:4326",
        "EPSG:32611",
        always_xy=True,
    ).transform

    to_geographic = Transformer.from_crs(
        "EPSG:32611",
        "EPSG:4326",
        always_xy=True,
    ).transform

    projected_line = gpd.GeoSeries(
        [centerline],
        crs="EPSG:4326",
    ).to_crs("EPSG:32611").iloc[0]

    start_point = gpd.GeoSeries(
        [Point(START)],
        crs="EPSG:4326",
    ).to_crs("EPSG:32611").iloc[0]

    end_point = gpd.GeoSeries(
        [Point(END)],
        crs="EPSG:4326",
    ).to_crs("EPSG:32611").iloc[0]

    start_offset = projected_line.distance(start_point)
    end_offset = projected_line.distance(end_point)

    print(f"Start endpoint offset: {start_offset:.1f} m")
    print(f"End endpoint offset: {end_offset:.1f} m")

    # Project the endpoints onto the road.
    start_distance = projected_line.project(start_point)
    end_distance = projected_line.project(end_point)

    # Keep the segment between the two projected locations.
    if start_distance <= end_distance:
        clipped = substring(
            projected_line,
            start_distance,
            end_distance,
        )
    else:
        clipped = substring(
            projected_line,
            end_distance,
            start_distance,
        )
        clipped = LineString(list(clipped.coords)[::-1])

    if clipped.is_empty or clipped.length == 0:
        raise RuntimeError(
            "The clipped centerline is empty. "
            "Check the endpoint coordinates and road segments."
        )

    print(f"Connected road length: {projected_line.length:.1f} m")
    print(f"Clipped centerline length: {clipped.length:.1f} m")

    clipped_geographic = gpd.GeoSeries(
        [clipped],
        crs="EPSG:32611",
    ).to_crs("EPSG:4326").iloc[0]

    return clipped, clipped_geographic, to_geographic


# ============================================================
# 5. CREATE THE CORRIDOR BOUNDARY
# ============================================================

def create_boundary(clipped_projected):
    # Flat end caps prevent the corridor from extending beyond
    # the selected endpoints by an additional 100 metres.
    boundary_projected = clipped_projected.buffer(
        BUFFER_METERS,
        cap_style="flat",
        join_style="round",
    )

    area_km2 = boundary_projected.area / 1_000_000

    boundary_geographic = gpd.GeoSeries(
        [boundary_projected],
        crs="EPSG:32611",
    ).to_crs("EPSG:4326").iloc[0]

    print("\nBoundary created.")
    print(f"Buffer on each side: {BUFFER_METERS} m")
    print(f"Boundary area: {area_km2:.4f} km²")

    return boundary_projected, boundary_geographic, area_km2


# ============================================================
# 6. LOAD AND CHECK THE BUSINESS DATA
# ============================================================

def load_businesses(boundary_projected):
    if not BUSINESS_FILE.exists():
        raise FileNotFoundError(
            f"Business CSV not found: {BUSINESS_FILE}"
        )

    businesses = pd.read_csv(BUSINESS_FILE)

    required_columns = {"longitude", "latitude"}

    if not required_columns.issubset(businesses.columns):
        raise ValueError(
            "Business CSV must contain longitude and latitude columns."
        )

    businesses["longitude"] = pd.to_numeric(
        businesses["longitude"],
        errors="coerce",
    )
    businesses["latitude"] = pd.to_numeric(
        businesses["latitude"],
        errors="coerce",
    )

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

    businesses["inside_boundary"] = (
        business_points.geometry.within(boundary_projected)
        | business_points.geometry.touches(boundary_projected)
    )

    inside_count = int(businesses["inside_boundary"].sum())
    total_count = len(businesses)

    percentage = (
        inside_count / total_count * 100
        if total_count
        else 0
    )

    print("\nFINAL BOUNDARY CHECK")
    print(f"Buffer each side: {BUFFER_METERS} m")
    print(f"Businesses inside: {inside_count}/{total_count}")
    print(f"Percentage inside: {percentage:.2f}%")

    return businesses, business_points, inside_count, percentage


# ============================================================
# 7. SAVE THE GEOJSON BOUNDARY
# ============================================================

def save_boundary(boundary_geographic, clipped_geographic, area_km2):
    output = gpd.GeoDataFrame(
        {
            "corridor": ["Western Avenue"],
            "start": ["Wilshire Boulevard"],
            "end": ["Near West 3rd Street"],
            "buffer_m": [BUFFER_METERS],
            "area_km2": [area_km2],
        },
        geometry=[boundary_geographic],
        crs="EPSG:4326",
    )

    output.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON",
    )

    print(f"\nGeoJSON saved: {OUTPUT_GEOJSON}")

    centerline_output = gpd.GeoDataFrame(
        {
            "corridor": ["Western Avenue"],
        },
        geometry=[clipped_geographic],
        crs="EPSG:4326",
    )

    centerline_path = BASE_DIR / "western_avenue_centerline.geojson"
    centerline_output.to_file(
        centerline_path,
        driver="GeoJSON",
    )

    print(f"Centerline saved: {centerline_path}")


# ============================================================
# 8. VISUALIZE THE CORRIDOR USING MATPLOTLIB
# ============================================================

def create_plot(
    boundary_projected,
    clipped_projected,
    business_points,
    inside_count,
    percentage,
):
    fig, ax = plt.subplots(figsize=(11, 9))

    # Plot the full corridor polygon.
    boundary_series = gpd.GeoSeries(
        [boundary_projected],
        crs="EPSG:32611",
    )
    boundary_series.plot(
        ax=ax,
        alpha=0.30,
        edgecolor="black",
        linewidth=2,
    )

    # Plot business locations inside the corridor.
    inside_mask = (
        business_points.geometry.within(boundary_projected)
        | business_points.geometry.touches(boundary_projected)
    )

    inside_points = business_points[inside_mask]
    outside_points = business_points[~inside_mask]

    if not outside_points.empty:
        outside_points.plot(
            ax=ax,
            markersize=12,
            alpha=0.5,
            label="Businesses outside boundary",
        )

    if not inside_points.empty:
        inside_points.plot(
            ax=ax,
            markersize=16,
            alpha=0.8,
            label="Businesses inside boundary",
        )

    # Draw the selected Western Avenue centerline.
    gpd.GeoSeries(
        [clipped_projected],
        crs="EPSG:32611",
    ).plot(
        ax=ax,
        linewidth=2.5,
        label="Western Avenue centerline",
    )

    ax.set_title(
        "Western Avenue Corridor Boundary\n"
        f"{BUFFER_METERS} m buffer on each side | "
        f"{inside_count} businesses inside ({percentage:.2f}%)"
    )

    ax.set_xlabel("Easting (metres, EPSG:32611)")
    ax.set_ylabel("Northing (metres, EPSG:32611)")
    ax.legend(loc="best")
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, alpha=0.25)

    plt.tight_layout()
        # Save the figure
    png_path = str(BASE_DIR / "western_avenue_final_boundary.png")

    fig.savefig(
        png_path,
        format="png",
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)

    print(f"Matplotlib map saved: {png_path}")

    print(f"Matplotlib map saved: {OUTPUT_PNG}")


# ============================================================
# 9. MAIN PROGRAM
# ============================================================

def main():
    features = download_road_segments()

    centerline = build_centerline(features)

    clipped_projected, clipped_geographic, _ = clip_centerline(
        centerline
    )

    (
        boundary_projected,
        boundary_geographic,
        area_km2,
    ) = create_boundary(clipped_projected)

    (
        businesses,
        business_points,
        inside_count,
        percentage,
    ) = load_businesses(boundary_projected)

    save_boundary(
        boundary_geographic,
        clipped_geographic,
        area_km2,
    )

    create_plot(
        boundary_projected,
        clipped_projected,
        business_points,
        inside_count,
        percentage,
    )

    # Save the business classification for further analysis.
    business_output = BASE_DIR / "western_avenue_businesses_checked.csv"
    businesses.to_csv(business_output, index=False)

    print(f"Business analysis saved: {business_output}")
    print("\nCorridor boundary generation completed.")


if __name__ == "__main__":
    main()
