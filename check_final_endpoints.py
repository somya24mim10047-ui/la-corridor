
import requests
import geopandas as gpd
from shapely.geometry import Point, MultiLineString
from shapely.ops import linemerge, substring

START = (-118.308881, 34.062100)
END = (-118.309011, 34.068419)
ROAD_IDS = [124436, 84883, 134991, 141603]

url = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

params = {
    "where": "OBJECTID IN (124436,84883,134991,141603)",
    "outFields": "OBJECTID,STNAME,ADRF,ADRT,INT_ID_FROM,INT_ID_TO",
    "returnGeometry": "true",
    "outSR": 4326,
    "f": "geojson",
}

response = requests.get(url, params=params, timeout=60)
response.raise_for_status()

features = response.json().get("features", [])
roads = gpd.GeoDataFrame.from_features(
    features, crs="EPSG:4326"
).to_crs("EPSG:32611")

if set(roads["OBJECTID"].astype(int)) != set(ROAD_IDS):
    raise RuntimeError("The returned road segments do not match the requested IDs.")

parts = []
for geom in roads.geometry:
    if geom.geom_type == "LineString":
        parts.append(geom)
    elif geom.geom_type == "MultiLineString":
        parts.extend(list(geom.geoms))

road = linemerge(MultiLineString(parts))

if road.geom_type != "LineString":
    raise RuntimeError(f"Road is not one continuous line: {road.geom_type}")

start = gpd.GeoSeries(
    [Point(START)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

end = gpd.GeoSeries(
    [Point(END)], crs="EPSG:4326"
).to_crs("EPSG:32611").iloc[0]

d1 = road.project(start)
d2 = road.project(end)
section = substring(road, min(d1, d2), max(d1, d2))

def show_point(label, point):
    geographic = gpd.GeoSeries(
        [point], crs="EPSG:32611"
    ).to_crs("EPSG:4326").iloc[0]

    print(f"{label}:")
    print(f"  Longitude: {geographic.x:.6f}")
    print(f"  Latitude:  {geographic.y:.6f}")

print("\nENDPOINT VALIDATION")
print("===================")
print(f"Connected road length: {road.length:.1f} m")
print(f"Selected section length: {section.length:.1f} m")
print(f"Start coordinate to road: {start.distance(road):.1f} m")
print(f"End coordinate to road:   {end.distance(road):.1f} m")

show_point("Original start (labelled Wilshire)", start)
show_point("Nearest road point to start", road.interpolate(d1))
show_point("Original end (labelled West 3rd)", end)
show_point("Nearest road point to end", road.interpolate(d2))

print("\nRoad records:")
for _, row in roads.sort_values("OBJECTID").iterrows():
    print(
        f"OBJECTID {int(row['OBJECTID'])}: "
        f"{row['STNAME']}, addresses {row['ADRF']}-{row['ADRT']}, "
        f"intersections {row['INT_ID_FROM']} -> {row['INT_ID_TO']}"
    )
