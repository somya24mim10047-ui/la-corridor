
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent
VALIDATION_DIR = BASE / "data" / "validation"

files = sorted(VALIDATION_DIR.glob("*_road_validation.csv"))

if not files:
    raise FileNotFoundError(
        "No road-validation CSV files found in data/validation"
    )

all_data = []

for file in files:
    df = pd.read_csv(file)

    # Standardize corridor names
    if "corridor" not in df.columns:
        df["corridor"] = file.stem.replace(
            "_road_validation", ""
        )

    # Standardize column names and coordinate formats
    df.columns = df.columns.str.strip()

    for col in ["latitude", "longitude", "road_distance_m"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    required = [
        "corridor", "latitude", "longitude", "road_distance_m"
    ]
    missing = [col for col in required if col not in df.columns]

    if missing:
        print(f"Skipping {file.name}: missing {missing}")
        continue

    # Recalculate flags consistently from measured distance
    df["within_25m"] = df["road_distance_m"] <= 25
    df["within_50m"] = df["road_distance_m"] <= 50

    all_data.append(df)

if not all_data:
    raise ValueError("No usable validation datasets were found.")

combined = pd.concat(all_data, ignore_index=True)

# Create a stable location key to avoid counting repeated businesses
# at the same coordinates as separate unique locations.
combined["location_key"] = (
    combined["latitude"].round(6).astype("string")
    + "_"
    + combined["longitude"].round(6).astype("string")
)

# Invalid coordinates or distances need separate review.
invalid = (
    combined["latitude"].isna()
    | combined["longitude"].isna()
    | combined["road_distance_m"].isna()
)

# Flag for manual review; do not delete these records.
combined["review_reason"] = ""

combined.loc[
    combined["road_distance_m"] > 50,
    "review_reason"
] = "More than 50 m from matching road centerline"

combined.loc[
    (combined["road_distance_m"] > 25)
    & (combined["road_distance_m"] <= 50),
    "review_reason"
] = "25–50 m from matching road centerline"

combined.loc[
    invalid,
    "review_reason"
] = "Missing or invalid coordinates/distance"

# Unique-location summary per corridor
summary_rows = []

for corridor, group in combined.groupby("corridor"):
    group_invalid = (
        group["latitude"].isna()
        | group["longitude"].isna()
        | group["road_distance_m"].isna()
    )

    valid = group.loc[~group_invalid].copy()
    unique = valid.drop_duplicates("location_key")
    unique = valid.drop_duplicates("location_key")

    summary_rows.append({
        "corridor": corridor,
        "business_records": len(group),
        "unique_valid_locations": len(unique),
        "median_road_distance_m": round(
            valid["road_distance_m"].median(), 2
        ) if len(valid) else None,
        "unique_locations_within_25m": int(
            unique["within_25m"].sum()
        ),
        "unique_locations_within_50m": int(
            unique["within_50m"].sum()
        ),
        "unique_locations_over_50m": int(
            (unique["road_distance_m"] > 50).sum()
        ),
        "invalid_records": int(group_invalid.sum())
    })

summary = pd.DataFrame(summary_rows)

for threshold in [25, 50]:
    count_col = f"unique_locations_within_{threshold}m"
    summary[f"within_{threshold}m_percent"] = (
        summary[count_col]
        / summary["unique_valid_locations"].replace(0, pd.NA)
        * 100
    ).round(1)

# Save full combined data and review candidates
combined_path = VALIDATION_DIR / "combined_corridor_quality_check.csv"
review_path = VALIDATION_DIR / "potential_outliers_for_review.csv"
summary_path = VALIDATION_DIR / "corridor_quality_summary.csv"

combined.to_csv(combined_path, index=False)

review = combined[
    (combined["review_reason"] != "")
].copy()
review.to_csv(review_path, index=False)

summary.to_csv(summary_path, index=False)

print("\n=== CORRIDOR QUALITY SUMMARY ===")
print(summary.to_string(index=False))

print("\nSaved files:")
print(combined_path)
print(review_path)
print(summary_path)

print(
    "\nImportant: These are road-distance quality checks, "
    "not final corridor-boundary verification."
)
