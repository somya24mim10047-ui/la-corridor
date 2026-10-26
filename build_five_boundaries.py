from pathlib import Path
import json
import pandas as pd
import geopandas as gpd

root = Path(".")
out = root / "data" / "final_corridor_boundaries"
out.mkdir(parents=True, exist_ok=True)

corridors = {
    "western_avenue": [
        root / "western_avenue_final_boundary.geojson"
    ],
    "larchmont_boulevard": [
        root / "data/boundary_candidates/complete_road_sources/larchmont_boulevard_100m_complete_candidate.geojson",
        root / "data/boundary_candidates/larchmont_boulevard_100m_candidate.geojson",
        root / "data/boundary_candidates/complete_road_sources/larchmont_boulevard_complete_clean.geojson",
        root / "data/corridors/larchmont_boulevard_road_segments_clean.geojson",
    ],
    "olympic_boulevard": [
        root / "data/boundary_candidates/complete_road_sources/olympic_boulevard_100m_complete_candidate.geojson",
        root / "data/boundary_candidates/olympic_boulevard_100m_candidate.geojson",
        root / "data/boundary_candidates/complete_road_sources/olympic_boulevard_complete_clean.geojson",
        root / "data/corridors/olympic_boulevard_road_segments_clean.geojson",
    ],
    "vermont_avenue": [
        root / "data/boundary_candidates/complete_road_sources/vermont_avenue_100m_complete_candidate.geojson",
        root / "data/boundary_candidates/vermont_avenue_100m_candidate.geojson",
        root / "data/boundary_candidates/complete_road_sources/vermont_avenue_complete_clean.geojson",
        root / "data/corridors/vermont_avenue_road_segments_clean.geojson",
    ],
    "wilshire_boulevard": [
        root / "data/boundary_candidates/complete_road_sources/wilshire_boulevard_100m_complete_candidate.geojson",
        root / "data/boundary_candidates/wilshire_boulevard_100m_candidate.geojson",
        root / "data/boundary_candidates/complete_road_sources/wilshire_boulevard_complete_clean.geojson",
        root / "data/corridors/wilshire_boulevard_road_segments_clean.geojson",
    ],
}

# A line-only fallback is buffered provisionally; its full extent
# is NOT assumed to be the correct corridor extent.
records = []

for name, candidates in corridors.items():
    source = next((p for p in candidates if p.exists()), None)
    if source is None:
        records.append({
            "corridor": name, "status": "MISSING",
            "source": "", "geometry": "", "area_km2": None,
            "valid": False, "note": "No source file found"
        })
        print(f"MISSING: {name}")
        continue

    try:
        gdf = gpd.read_file(source)
        if gdf.empty:
            raise ValueError("Source has no features")

        if gdf.crs is None:
            # These existing GeoJSON sources use longitude/latitude.
            gdf = gdf.set_crs("OGC:CRS84")

        geom_types = set(gdf.geometry.geom_type.dropna())
        is_polygon = geom_types.issubset({"Polygon", "MultiPolygon"})

        if not is_polygon:
            # Local metric projection for Los Angeles.
            metric = gdf.to_crs("EPSG:32611")
            merged = metric.geometry.union_all()
            polygon = merged.buffer(100)
            gdf = gpd.GeoDataFrame(
                [{"corridor": name, "buffer_m": 100}],
                geometry=[polygon], crs="EPSG:32611"
            ).to_crs("OGC:CRS84")
            method = "PROVISIONAL 100m buffer of source line geometry"
            status = "PROVISIONAL - EXTENT NEEDS REVIEW"
        else:
            method = "Existing polygon candidate; not independently endpoint-verified"
            status = "POLYGON FOUND - REVIEW ENDPOINTS"

        # Keep polygon features only and check geometry validity.
        gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
        if gdf.empty:
            raise ValueError("No polygon geometry after processing")

        gdf["geometry"] = gdf.geometry.make_valid()
        gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
        if gdf.empty:
            raise ValueError("No valid polygonal geometry remains")

        area_km2 = gdf.to_crs("EPSG:32611").geometry.area.sum() / 1_000_000
        dest = out / f"{name}_boundary.geojson"
        gdf.to_crs("OGC:CRS84").to_file(dest, driver="GeoJSON")

        records.append({
            "corridor": name,
            "status": status,
            "source": str(source),
            "geometry": ", ".join(sorted(set(gdf.geometry.geom_type))),
            "area_km2": round(area_km2, 6),
            "valid": bool(gdf.geometry.is_valid.all()),
            "note": method
        })
        print(f"OK: {name} -> {dest} | {status} | area={area_km2:.4f} km²")

    except Exception as e:
        records.append({
            "corridor": name, "status": "ERROR",
            "source": str(source), "geometry": "",
            "area_km2": None, "valid": False, "note": str(e)
        })
        print(f"ERROR: {name}: {e}")

report = pd.DataFrame(records)
report.to_csv(out / "boundary_validation_summary.csv", index=False)
(out / "boundary_validation_summary.txt").write_text(
    report.to_string(index=False), encoding="utf-8"
)

print("\n=== FIVE-CORRIDOR BOUNDARY SUMMARY ===")
print(report.to_string(index=False))
print(f"\nReports saved in: {out.resolve()}")
