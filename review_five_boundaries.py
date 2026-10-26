
from pathlib import Path

import geopandas as gpd
import pandas as pd


# --------------------------------------------------
# 1. LOAD FINAL CORRIDOR BOUNDARIES
# --------------------------------------------------

folder = Path("data/final_corridor_boundaries")
files = sorted(folder.glob("*_boundary.geojson"))

rows = []
layers = []

if not files:
    raise FileNotFoundError(
        f"No *_boundary.geojson files found in: {folder.resolve()}"
    )

for path in files:
    gdf = gpd.read_file(path)

    if gdf.empty:
        print(f"Skipping empty file: {path.name}")
        continue

    if gdf.crs is None:
        gdf = gdf.set_crs("OGC:CRS84")

    # Use a projected CRS for area calculation
    metric = gdf.to_crs("EPSG:32611")
    geom = metric.geometry.union_all()

    bounds_gdf = gdf.to_crs("OGC:CRS84")
    bounds = bounds_gdf.total_bounds

    corridor = path.stem.replace("_boundary", "")

    polygon_parts = 0
    for geometry in gdf.geometry:
        if geometry is None or geometry.is_empty:
            continue

        if hasattr(geometry, "geoms"):
            polygon_parts += sum(
                1 for part in geometry.geoms
                if not part.is_empty
            )
        else:
            polygon_parts += 1

    rows.append({
        "corridor": corridor,
        "features": len(gdf),
        "polygon_parts": polygon_parts,
        "area_km2": round(geom.area / 1_000_000, 4),
        "valid": bool(gdf.geometry.is_valid.all()),
        "min_lon": round(bounds[0], 6),
        "min_lat": round(bounds[1], 6),
        "max_lon": round(bounds[2], 6),
        "max_lat": round(bounds[3], 6),
    })

    layer = bounds_gdf[["geometry"]].copy()
    layer["corridor"] = corridor
    layers.append(layer)


# --------------------------------------------------
# 2. SAVE GEOMETRY QUALITY REPORT
# --------------------------------------------------

report = pd.DataFrame(rows)

report_path = folder / "boundary_geometry_qa.csv"
report.to_csv(report_path, index=False)

print("\n" + "=" * 65)
print("CORRIDOR GEOMETRY QUALITY REPORT")
print("=" * 65)
print(report.to_string(index=False))
print(f"\nQA report saved to: {report_path.resolve()}")


# --------------------------------------------------
# 3. CREATE MAP WITHOUT EXTERNAL TILES OR API KEYS
# --------------------------------------------------

try:
    import folium
    from folium.plugins import Fullscreen

    if not layers:
        raise ValueError("No valid corridor boundary layers were loaded.")

    all_bounds = gpd.GeoDataFrame(
        pd.concat(layers, ignore_index=True),
        geometry="geometry",
        crs="OGC:CRS84"
    )

    bounds = all_bounds.total_bounds

    center = [
        (bounds[1] + bounds[3]) / 2,
        (bounds[0] + bounds[2]) / 2
    ]

    # No external tile provider: avoids tile API-key errors
    m = folium.Map(
        location=center,
        zoom_start=13,
        tiles=None,
        control_scale=True,
        prefer_canvas=True
    )

    # Five distinct corridor colors
    corridor_colors = {
        "western_avenue": "#e63946",
        "larchmont_boulevard": "#277da1",
        "olympic_boulevard": "#2a9d8f",
        "vermont_avenue": "#f4a261",
        "wilshire_boulevard": "#805ad5",
    }

    display_names = {
        "western_avenue": "Western Avenue",
        "larchmont_boulevard": "Larchmont Boulevard",
        "olympic_boulevard": "Olympic Boulevard",
        "vermont_avenue": "Vermont Avenue",
        "wilshire_boulevard": "Wilshire Boulevard",
    }

    # Add each corridor as a separate selectable layer
    for layer in layers:
        name = layer["corridor"].iloc[0]
        color = corridor_colors.get(name, "#333333")
        display_name = display_names.get(
            name, name.replace("_", " ").title()
        )

        styled_layer = layer.copy()
        styled_layer["display_name"] = display_name

        folium.GeoJson(
            styled_layer.to_json(),
            name=display_name,
            style_function=lambda feature, c=color: {
                "color": c,
                "weight": 4,
                "opacity": 1.0,
                "fillColor": c,
                "fillOpacity": 0.22,
            },
            highlight_function=lambda feature, c=color: {
                "color": c,
                "weight": 6,
                "fillOpacity": 0.35,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["display_name"],
                aliases=["Corridor:"],
                sticky=True
            )
        ).add_to(m)

    # Add a fixed legend
    legend_html = """
    <div style="
        position: fixed;
        bottom: 25px;
        left: 25px;
        z-index: 9999;
        background: white;
        padding: 12px 16px;
        border: 1px solid #777;
        border-radius: 6px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        font-family: Arial, sans-serif;
        font-size: 13px;
        color: #222;
    ">
      <b>LA Corridor Boundaries</b><br><br>
      <span style="color:#e63946;">&#9632;</span>
      Western Avenue<br>
      <span style="color:#277da1;">&#9632;</span>
      Larchmont Boulevard<br>
      <span style="color:#2a9d8f;">&#9632;</span>
      Olympic Boulevard<br>
      <span style="color:#f4a261;">&#9632;</span>
      Vermont Avenue<br>
      <span style="color:#805ad5;">&#9632;</span>
      Wilshire Boulevard
    </div>
    """

    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=False).add_to(m)

    Fullscreen(
        position="topright",
        title="Full screen",
        title_cancel="Exit full screen"
    ).add_to(m)

    # Fit the map to include all five corridors
    m.fit_bounds([
        [bounds[1], bounds[0]],
        [bounds[3], bounds[2]]
    ])

    # Save the HTML review map
    map_path = folder / "five_corridor_boundary_review.html"
    m.save(str(map_path))

    print("\n" + "=" * 65)
    print("MAP CREATED SUCCESSFULLY")
    print("=" * 65)
    print(f"Review map: {map_path.resolve()}")
    print("External map tiles: Disabled")
    print("API key required: No")
    print("Boundary GeoJSON files: Not modified")

except ImportError:
    print("\nFolium is not installed.")
    print("Install it using: python -m pip install folium")
