
import requests
import pandas as pd
from pathlib import Path

URL = (
    "https://geocode.gis.lacounty.gov/"
    "geocode/rest/services/CAMS_Locator/"
    "GeocodeServer/findAddressCandidates"
)

records = [
    {
        "business_name": "ELENA L GARCIA",
        "address": "225 N Vermont Avenue, Los Angeles, CA",
        "recorded_lat": 34.0761,
        "recorded_lon": -118.3031,
    },
    {
        "business_name": "SJ INVESTMENT 2020 LLC",
        "address": "3400 W Olympic Blvd, Los Angeles, CA",
        "recorded_lat": 34.0487,
        "recorded_lon": -118.3362,
    },
]

results = []

for record in records:
    print("\n" + "=" * 65)
    print("Business:", record["business_name"])
    print("Searching:", record["address"])

    params = {
        "SingleLine": record["address"],
        "outFields": "*",
        "maxLocations": 3,
        "f": "json",
    }

    try:
        response = requests.get(URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        print("Request failed:", exc)
        continue

    if "error" in data:
        print("Geocoder error:", data["error"])
        continue

    candidates = data.get("candidates", [])

    if not candidates:
        print("No address match returned.")
        continue

    for candidate in candidates:
        location = candidate.get("location", {})
        attrs = candidate.get("attributes", {})

        result = {
            "business_name": record["business_name"],
            "searched_address": record["address"],
            "recorded_lat": record["recorded_lat"],
            "recorded_lon": record["recorded_lon"],
            "matched_address": candidate.get("address"),
            "match_score": candidate.get("score"),
            "geocoded_lon": location.get("x"),
            "geocoded_lat": location.get("y"),
        }
        results.append(result)

        print("Matched address:", result["matched_address"])
        print("Match score:", result["match_score"])
        print("Geocoded latitude:", result["geocoded_lat"])
        print("Geocoded longitude:", result["geocoded_lon"])

out = Path("data/validation/geocoder_address_check.csv")
out.parent.mkdir(parents=True, exist_ok=True)

if results:
    pd.DataFrame(results).to_csv(out, index=False)
    print("\nSaved results to:", out)
else:
    print("\nNo candidates to save.")
