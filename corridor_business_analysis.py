
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# -----------------------------------------
# 1. LOAD EXISTING BUSINESS DATA
# -----------------------------------------

input_file = Path("western_avenue_businesses.csv")

if not input_file.exists():
    raise FileNotFoundError(
        "western_avenue_businesses.csv was not found. "
        "Run this script from your project folder."
    )

df = pd.read_csv(input_file)
df.columns = df.columns.str.strip().str.lower()

# Find coordinate columns
lat_col = next(
    (c for c in ["latitude", "lat"] if c in df.columns), None
)
lon_col = next(
    (c for c in ["longitude", "lon", "lng"] if c in df.columns), None
)

if lat_col is None or lon_col is None:
    raise ValueError(
        f"Could not find coordinate columns. Found: {list(df.columns)}"
    )

df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
df = df.dropna(subset=[lat_col, lon_col]).copy()

# Proposed endpoint latitudes
south_lat = 34.062100
north_lat = 34.068419

# Keep records between the proposed endpoint latitudes
# and within the existing study-window longitude range.
df = df[
    df[lat_col].between(south_lat, north_lat)
    & df[lon_col].between(-118.3125, -118.3060)
].copy()

if df.empty:
    raise ValueError("No business records remain in the selected area.")

print("Records in analysis window:", len(df))
print("Available columns:", list(df.columns))


# -----------------------------------------
# 2. DIVIDE AREA INTO THREE LATITUDE BANDS
# -----------------------------------------
# These are preliminary analysis bands, not
# validated road-based corridor boundaries.

df["section"] = pd.cut(
    df[lat_col],
    bins=[south_lat, south_lat + (north_lat - south_lat) / 3,
          south_lat + 2 * (north_lat - south_lat) / 3, north_lat],
    labels=["South", "Middle", "North"],
    include_lowest=True
)

section_counts = (
    df.groupby("section", observed=False)
      .size()
      .reindex(["South", "Middle", "North"], fill_value=0)
      .rename("business_records")
      .reset_index()
)

section_counts.to_csv(
    "western_avenue_section_analysis.csv", index=False
)

print("\nBusiness records by preliminary section:")
print(section_counts.to_string(index=False))


# -----------------------------------------
# 3. IDENTIFY AVAILABLE BUSINESS CATEGORY
# -----------------------------------------

possible_type_columns = [
    "business_type",
    "industry",
    "naics_description",
    "business_category",
    "business_name",
    "business_name_legal"
]

type_col = next(
    (c for c in possible_type_columns if c in df.columns), None
)

if type_col:
    categories = (
        df[type_col]
        .fillna("Unknown")
        .astype(str)
        .value_counts()
        .head(15)
    )

    categories.rename_axis("category").reset_index(
        name="records"
    ).to_csv("western_avenue_business_categories.csv", index=False)

    print(f"\nMost common values in '{type_col}':")
    print(categories.to_string())
else:
    print(
        "\nNo obvious business type/name column found. "
        "Inspect the available columns printed above."
    )


# -----------------------------------------
# 4. CREATE SECTION COUNT CHART
# -----------------------------------------

plt.figure(figsize=(8, 5))

plt.bar(
    section_counts["section"].astype(str),
    section_counts["business_records"]
)

plt.title("Business Records by Section of Study Area")
plt.xlabel("Preliminary latitude section")
plt.ylabel("Number of business records")
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(
    "western_avenue_section_analysis.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()


# -----------------------------------------
# 5. CREATE LOCATION MAP WITH SECTION LINES
# -----------------------------------------

fig, ax = plt.subplots(figsize=(9, 10))

ax.scatter(
    df[lon_col],
    df[lat_col],
    s=18,
    alpha=0.7,
    label="Business records"
)

# Draw the two internal latitude separators
first_split = south_lat + (north_lat - south_lat) / 3
second_split = south_lat + 2 * (north_lat - south_lat) / 3

for split in [first_split, second_split]:
    ax.axhline(split, linestyle="--", linewidth=1)

ax.scatter(
    [-118.308881, -118.309011],
    [south_lat, north_lat],
    marker="X",
    s=120,
    label="Proposed endpoints"
)

ax.set_title("Western Avenue Study Area: Business Distribution")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.grid(alpha=0.25)
ax.legend()
ax.set_aspect("equal", adjustable="datalim")

plt.tight_layout()
plt.savefig(
    "western_avenue_business_sections.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

print("\nAnalysis complete. Files created:")
print("- western_avenue_section_analysis.csv")
print("- western_avenue_business_categories.csv (if a suitable column exists)")
print("- western_avenue_section_analysis.png")
print("- western_avenue_business_sections.png")

print(
    "\nImportant: These are preliminary study-window results. "
    "The latitude bands are not final corridor boundaries."
)
