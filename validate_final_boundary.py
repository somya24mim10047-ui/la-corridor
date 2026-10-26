
import geopandas as gpd
from shapely.geometry import Point

FILE = "western_avenue_final_boundary.geojson"

boundary = gpd.read_file(FILE)

if boundary.empty:
    raise SystemExit("ERROR: Saved boundary file is empty.")

geom = boundary.to_crs("EPSG:32611").geometry.union_all()

start = gpd.GeoSeries(
    [Point(-118.308881, 34.062100)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

end = gpd.GeoSeries(
    [Point(-118.309011, 34.068419)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

print("\nSAVED BOUNDARY VERIFICATION")
print("---------------------------")
print("Geometry type:", geom.geom_type)
print("Geometry valid:", geom.is_valid)
print("Boundary area:", round(geom.area / 1_000_000, 4), "sq km")
print("Start endpoint covered:", geom.covers(start))
print("End endpoint covered:", geom.covers(end))

if not geom.is_valid:
    print("RESULT: Boundary geometry needs attention.")
elif geom.covers(start) and geom.covers(end):
    print("RESULT: Both endpoints are covered.")
else:
    print("RESULT: At least one endpoint is outside.")
