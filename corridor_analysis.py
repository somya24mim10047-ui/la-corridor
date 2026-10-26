
import requests
import pandas as pd
import matplotlib.pyplot as plt
import json

# -------------------------------------------------
# 1. Download matching records from the online API
# -------------------------------------------------

URL = "https://data.lacity.org/resource/6rrh-rzua.json"

params = {
    "$select": (
        "business_name,street_address,"
        "primary_naics_description,location_1"
    ),
    "$where": (
        "upper(street_address) like '%WESTERN%' "
        "AND location_1 IS NOT NULL"
    ),
    "$limit": 50000
}

print("Fetching business data from Los Angeles Open Data...")

response = requests.get(URL, params=params, timeout=60)
response.raise_for_status()

df = pd.DataFrame(response.json())

print("Records retrieved:", len(df))

if df.empty:
    raise SystemExit(
        "No records returned. Check the dataset API or query."
    )

# -------------------------------------------------
# 2. Extract longitude and latitude
# -------------------------------------------------

def extract_coordinates(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return pd.Series([None, None])

    if not isinstance(value, dict):
        return pd.Series([None, None])

    # GeoJSON point: [longitude, latitude]
    if value.get("type") == "Point":
        coordinates = value.get("coordinates", [])
        if len(coordinates) >= 2:
            return pd.Series([
                float(coordinates[0]),
                float(coordinates[1])
            ])

    # Alternative named-coordinate format
    if "longitude" in value and "latitude" in value:
        return pd.Series([
            float(value["longitude"]),
            float(value["latitude"])
        ])

    return pd.Series([None, None])


df[["longitude", "latitude"]] = df["location_1"].apply(
    extract_coordinates
)

df = df.dropna(subset=["longitude", "latitude"]).copy()

print("Records with usable coordinates:", len(df))

# -------------------------------------------------
# 3. Initial geographic filter
# Approximate limits; verify before using for research.
# -------------------------------------------------

SOUTH_LAT = 34.0621
NORTH_LAT = 34.0685
WEST_LON = -118.3120
EAST_LON = -118.3060

study = df[
    df["latitude"].between(SOUTH_LAT, NORTH_LAT)
    & df["longitude"].between(WEST_LON, EAST_LON)
].copy()

print("Records in initial study window:", len(study))

if study.empty:
    raise SystemExit(
        "No records inside the initial window. "
        "Inspect coordinate ranges and verify the study area "
        "on OpenStreetMap before changing the limits."
    )

# -------------------------------------------------
# 4. Plot the locations
# -------------------------------------------------

plt.figure(figsize=(8, 9))

plt.scatter(
    study["longitude"],
    study["latitude"],
    alpha=0.7,
    s=18
)

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Registered Businesses: Initial Study Window")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("business_locations.png", dpi=200)
plt.close()

# -------------------------------------------------
# 5. Count businesses in approximate 250 m sections
# -------------------------------------------------

# Latitude distance is approximately 111,320 metres per degree.
study["distance_m"] = (
    study["latitude"] - SOUTH_LAT
) * 111320

study["section"] = (
    study["distance_m"] // 250
).astype(int)

counts = study.groupby("section").size()

counts = counts.reindex(
    range(counts.index.min(), counts.index.max() + 1),
    fill_value=0
)

analysis = pd.DataFrame({
    "business_count": counts
})

analysis["rolling_average"] = (
    analysis["business_count"]
    .rolling(window=3, center=True, min_periods=1)
    .mean()
)

# -------------------------------------------------
# 6. Plot the business-count graph
# -------------------------------------------------

plt.figure(figsize=(12, 5))

plt.bar(
    analysis.index,
    analysis["business_count"],
    label="Business count"
)

plt.plot(
    analysis.index,
    analysis["rolling_average"],
    marker="o",
    label="Rolling average"
)

plt.xlabel("Section number (south to north)")
plt.ylabel("Registered businesses")
plt.title("Business Activity Along Western Avenue")
plt.legend()
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig("business_activity.png", dpi=200)
plt.close()

# -------------------------------------------------
# 7. Display results
# -------------------------------------------------

print("\nBusiness counts by section:")
print(analysis.to_string())

# Save the filtered records for further analysis.
study.to_csv("western_avenue_businesses.csv", index=False)
analysis.to_csv("western_avenue_section_counts.csv")

print("\nSaved files:")
print("- business_locations.png")
print("- business_activity.png")
print("- western_avenue_businesses.csv")
print("- western_avenue_section_counts.csv")

print("\n--- Geographic check ---")
print("Latitude range:")
print(study["latitude"].min(), "to", study["latitude"].max())

print("Longitude range:")
print(study["longitude"].min(), "to", study["longitude"].max())

print("\nFirst 10 business locations:")
print(
    study[
        ["business_name", "street_address",
         "latitude", "longitude"]
    ].head(10).to_string(index=False)
)

print("\nSection counts:")
print(analysis.to_string())
print("\n--- Geographic check ---")
print("Latitude:", study["latitude"].min(), "to", study["latitude"].max())
print("Longitude:", study["longitude"].min(), "to", study["longitude"].max())
print("\nSection counts:")
print(analysis.to_string())
# Save the filtered business data
study.to_csv("western_avenue_businesses.csv", index=False)

# Save the business counts by section
analysis.to_csv("western_avenue_section_counts.csv")

print("\nCSV files saved successfully!")
print("Businesses CSV:", "western_avenue_businesses.csv")
print("Section counts CSV:", "western_avenue_section_counts.csv")