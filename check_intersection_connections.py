
import geopandas as gpd
import requests

url = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

params = {
    "where": "1=1",
    "outFields": "*",
    "returnGeometry": "true",
    "f": "geojson",
    "geometry": "-118.33,34.05,-118.29,34.08",
    "geometryType": "esriGeometryEnvelope",
    "spatialRel": "esriSpatialRelIntersects",
    "inSR": "4326",
    "outSR": "4326",
    "resultRecordCount": 2000,
}

r = requests.get(url, params=params, timeout=60)
r.raise_for_status()

roads = gpd.GeoDataFrame.from_features(
    r.json()["features"], crs="EPSG:4326"
)

western = roads[
    roads["STNAME"].astype(str).str.contains(
        "WESTERN", case=False, na=False
    )
].copy()


print("\nGEOMETRY DIAGNOSTICS")
print("--------------------")

for _, row in western.iterrows():
    geom = row.geometry

    if geom is None:
        print(f"OBJECTID={row['OBJECTID']}: Missing geometry")
        continue

    if geom.geom_type == "LineString":
        coords = list(geom.coords)
        print(
            f"OBJECTID={row['OBJECTID']} | "
            f"FROM={row['INT_ID_FROM']} | "
            f"TO={row['INT_ID_TO']} | "
            f"Type={geom.geom_type} | "
            f"Coordinates={len(coords)} | "
            f"Length={geom.length:.8f} source units"
        )
    else:
        print(
            f"OBJECTID={row['OBJECTID']} | "
            f"Type={geom.geom_type} | "
            f"Length={geom.length:.8f} source units"
        )
