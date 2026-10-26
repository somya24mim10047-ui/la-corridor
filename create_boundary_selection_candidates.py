import geopandas as gpd
import pandas as pd
from pathlib import Path

root = Path("data")
road_dir = root / "boundary_candidates" / "complete_road_sources"
out_dir = root / "final_corridor_boundaries" / "selection_candidates"
out_dir.mkdir(parents=True, exist_ok=True)

results = []

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    print(f"\n=== {name.upper()} ===")

    roads = gpd.read_file(
        road_dir / f"{name}_complete_clean.geojson"
    ).to_crs("EPSG:32611")

    businesses = pd.read_csv(
        root / "corridors" / f"{name}_businesses.csv"
    )

    points = gpd.GeoDataFrame(
        businesses,
        geometry=gpd.points_from_xy(
            businesses["longitude"], businesses["latitude"]
        ),
        crs="EPSG:4326"
    ).to_crs("EPSG:32611")

    road_union = roads.geometry.union_all()

    for buffer_m in [50, 100]:
        candidate_geometry = road_union.buffer(buffer_m)

        candidate = gpd.GeoDataFrame(
            {
                "corridor": [name],
                "buffer_m": [buffer_m],
                "area_km2": [candidate_geometry.area / 1_000_000],
                "geometry": [candidate_geometry],
            },
            crs="EPSG:32611"
        )

        # Save in geographic coordinates for standard GeoJSON use.
        output_path = out_dir / f"{name}_{buffer_m}m_candidate.geojson"
        candidate.to_crs("EPSG:4326").to_file(
            output_path, driver="GeoJSON"
        )

        inside = points.geometry.map(candidate_geometry.covers)
        parts = (
            len(candidate_geometry.geoms)
            if hasattr(candidate_geometry, "geoms") else 1
        )

        results.append({
            "corridor": name,
            "buffer_m": buffer_m,
            "area_km2": candidate_geometry.area / 1_000_000,
            "businesses_total": len(points),
            "businesses_inside": int(inside.sum()),
            "businesses_outside": int((~inside).sum()),
            "inside_percent": inside.mean() * 100,
            "polygon_parts": parts,
            "geometry_valid": candidate_geometry.is_valid,
            "candidate_file": str(output_path)
        })

        print(
            f"{buffer_m} m candidate | "
            f"area={candidate_geometry.area / 1_000_000:.3f} km² | "
            f"inside={inside.sum()}/{len(points)} "
            f"({inside.mean() * 100:.2f}%) | "
            f"parts={parts} | valid={candidate_geometry.is_valid}"
        )
        print("Saved:", output_path)

report_path = out_dir / "boundary_selection_comparison.csv"
pd.DataFrame(results).to_csv(report_path, index=False)

print("\nComparison report saved:", report_path)
print("Existing final boundary files were not changed.")
