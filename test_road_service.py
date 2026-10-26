
import requests

URL = (
    "https://maps.lacity.org/arcgis/rest/services/"
    "Core/Street_Information/MapServer/9/query"
)

tests = [
    ("ELENA L GARCIA", 34.0761, -118.3031, "VERMONT"),
    ("SJ INVESTMENT 2020 LLC", 34.0487, -118.3362, "OLYMPIC"),
]

for business, lat, lon, expected_road in tests:
    print("\n" + "=" * 70)
    print(f"Business: {business} | Expected road: {expected_road}")

    params = {
        "where": "1=1",
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "distance": 500,
        "units": "esriSRUnit_Meter",
        "outFields": "OBJECTID,STNAME,STSFX,SFXDIR",
        "returnGeometry": "false",
        "returnExceededLimitFeatures": "true",
        "outSR": "4326",
        "f": "json",
        "resultRecordCount": 1000,
    }

    try:
        response = requests.get(URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        print("Request failed:", exc)
        continue

    if "error" in data:
        print("API error:", data["error"])
        continue

    features = data.get("features", [])
    print("Nearby road segments returned:", len(features))
    print("Transfer limit exceeded:", data.get("exceededTransferLimit", False))

    names = sorted({
        " ".join(
            str(attrs.get(field) or "").strip()
            for field in ("SFXDIR", "STNAME", "STSFX")
        ).strip()
        for attrs in (f.get("attributes", {}) for f in features)
    })

    for name in names:
        if name:
            print(" -", name)

    matches = [
        name for name in names
        if expected_road.lower() in name.lower()
    ]
    print("Expected road found:", bool(matches))
