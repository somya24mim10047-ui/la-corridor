
from pathlib import Path
import pandas as pd

BASE = Path("data/final_corridor_boundaries/selection_candidates")

files = [
    (
        "OLYMPIC",
        BASE / "olympic_boulevard_excluded_business_review.csv",
    ),
    (
        "WILSHIRE",
        BASE / "wilshire_boulevard_excluded_business_review.csv",
    ),
]

for name, path in files:
    df = pd.read_csv(path)

    print(f"\n{'=' * 65}")
    print(name)
    print("=" * 65)

    print("\nCoordinate ranges:")
    print("Longitude:", df["longitude"].min(), "to", df["longitude"].max())
    print("Latitude:", df["latitude"].min(), "to", df["latitude"].max())

    print("\nMost common addresses:")
    print(df["street_address"].value_counts().head(15).to_string())

    print("\nExcluded business locations, first 20:")
    cols = [
        "business_name",
        "street_address",
        "latitude",
        "longitude",
    ]
    print(df[cols].head(20).to_string(index=False))
