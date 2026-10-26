
import pandas as pd
from pathlib import Path
from pyproj import Transformer
from math import hypot

input_file = Path("data/validation/geocoder_address_check.csv")
output_file = Path("data/validation/address_coordinate_comparison.csv")

df = pd.read_csv(input_file)

# The LA County geocoder returns projected coordinates.
# Test common coordinate systems and select the one that
# produces plausible Los Angeles longitude/latitude values.
transformers = {
    "EPSG:2229": Transformer.from_crs(
        "EPSG:2229", "EPSG:4326", always_xy=True
    ),
    "EPSG:26911": Transformer.from_crs(
        "EPSG:26911", "EPSG:4326", always_xy=True
    ),
}

chosen = None

for crs, transformer in transformers.items():
    lon, lat = transformer.transform(
        df.loc[0, "geocoded_lon"],
        df.loc[0, "geocoded_lat"],
    )

    print(f"{crs} test: longitude={lon:.6f}, latitude={lat:.6f}")

    if -119 < lon < -117 and 33 < lat < 35:
        chosen = (crs, transformer)
        break

if chosen is None:
    raise ValueError(
        "Neither tested CRS produced plausible Los Angeles coordinates. "
        "Check the geocoder's spatial-reference metadata before proceeding."
    )

crs, transformer = chosen
print("\nSelected coordinate system:", crs)

converted = df.apply(
    lambda row: transformer.transform(
        row["geocoded_lon"], row["geocoded_lat"]
    ),
    axis=1,
)

df["geocoded_longitude"] = [point[0] for point in converted]
df["geocoded_latitude"] = [point[1] for point in converted]

# Approximate straight-line distance between the two coordinate pairs.
def distance_m(row):
    lat1 = row["recorded_lat"]
    lon1 = row["recorded_lon"]
    lat2 = row["geocoded_latitude"]
    lon2 = row["geocoded_longitude"]

    from math import radians, sin, cos, asin, sqrt

    earth_radius_m = 6371000
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )
    return 2 * earth_radius_m * asin(sqrt(a))

df["coordinate_difference_m"] = df.apply(distance_m, axis=1)

df.to_csv(output_file, index=False)

print("\n=== Coordinate comparison ===")
print(
    df[
        [
            "business_name",
            "matched_address",
            "recorded_lat",
            "recorded_lon",
            "geocoded_latitude",
            "geocoded_longitude",
            "coordinate_difference_m",
        ]
    ].to_string(index=False)
)

print("\nSaved:", output_file)
