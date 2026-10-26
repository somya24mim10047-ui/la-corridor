
import geopandas as gpd
from pathlib import Path
from shapely.ops import unary_union

source = Path(
    "data/boundary_candidates/complete_road_sources/"
    "wilshire_boulevard_complete_clean.geojson"
)

output = Path(
    "data/boundary_candidates/complete_road_candidates/"
    "wilshire_boulevard_125m_complete_candidate.geojson"
)

if not source.exists():
    raise FileNotFoundError(f"Road source not found: {source}")

roads = gpd.read_file(source)

if roads.empty or roads.geometry.is_empty.all():
    raise ValueError("The official road source contains no usable geometry.")

# Los Angeles is in UTM Zone 11N; buffer in metres.
roads_m = roads.to_crs(epsg=32611)
road_union = unary_union(
    [geom for geom in roads_m.geometry if geom is not None and not geom.is_empty]
)

buffer_geometry = road_union.buffer(125)

candidate = gpd.GeoDataFrame(
    [{"corridor": "wilshire_boulevard", "buffer_m": 125}],
    geometry=[buffer_geometry],
    crs="EPSG:32611",
).to_crs(epsg=4326)

candidate.to_file(output, driver="GeoJSON")

print(f"Official road features used: {len(roads)}")
print("Buffer width: 125 metres")
print(f"Saved candidate: {output.resolve()}")
print("Original road geometry and existing candidates were not modified.")
