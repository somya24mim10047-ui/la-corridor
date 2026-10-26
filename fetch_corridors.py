
import requests
import pandas as pd
from pathlib import Path

OUT = Path(__file__).parent / "data" / "corridors"
OUT.mkdir(parents=True, exist_ok=True)

API = "https://data.lacity.org/resource/r4uk-afju.json"

# Candidate corridor name, address keyword, and geographic search bounds.
# Bounds restrict the search area; they are not final corridor boundaries.
CORRIDORS = {
    "wilshire_boulevard": {
        "street": "WILSHIRE",
        "bounds": (34.050, -118.350, 34.075, -118.275),
    },
    "olympic_boulevard": {
        "street": "OLYMPIC",
        "bounds": (34.035, -118.350, 34.060, -118.275),
    },
    "vermont_avenue": {
        "street": "VERMONT",
        "bounds": (34.040, -118.305, 34.085, -118.285),
    },
    "larchmont_boulevard": {
        "street": "LARCHMONT",
        "bounds": (34.060, -118.335, 34.085, -118.305),
    },
}


def fetch_corridor(name, config):
    south, west, north, east = config["bounds"]

    params = {
        "$select": (
            "business_name,street_address,city,"
            "primary_naics_description,location"
        ),
        "$where": (
            f"within_box(location,{north},{west},{south},{east})"
        ),
        "$limit": 50000,
    }

    print(f"\nFetching {name}...")
    response = requests.get(API, params=params, timeout=90)
    response.raise_for_status()
    records = response.json()

    rows = []

    for item in records:
        address = str(item.get("street_address") or "").upper()

        # Keep records whose address contains the corridor street name.
        if config["street"] not in address:
            continue

        location = item.get("location") or {}

        try:
            latitude = float(location["latitude"])
            longitude = float(location["longitude"])
        except (KeyError, TypeError, ValueError):
            continue

        rows.append({
            "corridor": name,
            "business_name": item.get("business_name"),
            "street_address": item.get("street_address"),
            "city": item.get("city"),
            "primary_naics_description":
                item.get("primary_naics_description"),
            "latitude": latitude,
            "longitude": longitude,
        })

    df = pd.DataFrame(rows)
    output_file = OUT / f"{name}_businesses.csv"
    df.to_csv(output_file, index=False)

    print(f"Saved: {output_file}")
    print(f"Matching businesses: {len(df)}")


if __name__ == "__main__":
    for name, config in CORRIDORS.items():
        try:
            fetch_corridor(name, config)
        except Exception as error:
            print(f"FAILED: {name}: {error}")

    print("\nCollection finished. Check each corridor's record count.")
