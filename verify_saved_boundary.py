import geopandas as gpd
from shapely.geometry import Point

# Read the boundary you already created
boundary = gpd.read_file("western_avenue_final_boundary.geojson")

if boundary.empty:
    print("ERROR: The boundary file is empty.")
    raise SystemExit

# Measure the boundary in metres
boundary_m = boundary.to_crs("EPSG:32611")
geom = boundary_m.geometry.union_all()

print("\nSAVED BOUNDARY VERIFICATION")
print("---------------------------")
print("Geometry type:", geom.geom_type)
print("Geometry valid:", geom.is_valid)
print("Boundary area:", round(geom.area / 1_000_000, 4), "sq km")

# Check whether the intended endpoints fall inside the boundary
start = gpd.GeoSeries(
    [Point(-118.308881, 34.062100)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

end = gpd.GeoSeries(
    [Point(-118.309011, 34.068419)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

print("Start endpoint covered:", geom.covers(start))
print("End endpoint covered:", geom.covers(end))

print("\nBOUNDARY CHECK:")
if not geom.is_valid:
    print("Needs attention: invalid geometry.")
elif geom.covers(start) and geom.covers(end):
    print("Both endpoints are covered. Continue checking road alignment.")
else:
    print("At least one endpoint is outside the saved boundary.")