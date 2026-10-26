
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# 1. Load the existing dataset
df = pd.read_csv("western_avenue_businesses.csv")

required = [
    "business_name",
    "primary_naics_description",
    "latitude",
    "longitude",
    "section"
]

missing_columns = [c for c in required if c not in df.columns]
if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")

print("Total business records:", len(df))

# 2. Clean category names, keeping missing values identifiable
category_col = "primary_naics_description"

df[category_col] = (
    df[category_col]
    .fillna("Unknown / Missing")
    .astype(str)
    .str.strip()
    .replace("", "Unknown / Missing")
)

# 3. Overall business composition
category_counts = (
    df[category_col]
    .value_counts()
    .rename_axis("business_category")
    .reset_index(name="record_count")
)

category_counts["percentage_of_all_records"] = (
    category_counts["record_count"] / len(df) * 100
).round(2)

category_counts.to_csv(
    "western_avenue_business_composition.csv",
    index=False
)

print("\nTop 15 business categories:")
print(category_counts.head(15).to_string(index=False))

# 4. Business records by section
section_counts = (
    df["section"]
    .fillna("Unknown")
    .astype(str)
    .value_counts()
)

print("\nRecords by section:")
print(section_counts.to_string())

# 5. Category comparison across sections
cross_tab = pd.crosstab(
    df["section"].fillna("Unknown"),
    df[category_col]
)

cross_tab.to_csv("western_avenue_categories_by_section.csv")

# Plot the top 10 categories, excluding missing classifications
known = df[df[category_col] != "Unknown / Missing"]
top_categories = known[category_col].value_counts().head(10)

if not top_categories.empty:
    plt.figure(figsize=(11, 6))
    top_categories.sort_values().plot(kind="barh")
    plt.title("Top 10 Recorded Business Categories")
    plt.xlabel("Number of records")
    plt.ylabel("Business category")
    plt.tight_layout()
    plt.savefig(
        "western_avenue_top_business_categories.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.close()

# 6. Plot total records by existing section label
section_counts = section_counts.reindex(
    ["South", "Middle", "North"]
).dropna()

plt.figure(figsize=(8, 5))

# Count businesses in each section
section_counts = df["section"].value_counts().sort_index()

print("\nRecords by section:")
print(section_counts)

# Plot section counts safely
import matplotlib.pyplot as plt

if not section_counts.empty:
    plt.figure(figsize=(8, 5))
    section_counts.plot(kind="bar", color="steelblue")

    plt.title("Business Records by Corridor Section")
    plt.xlabel("Corridor Section")
    plt.ylabel("Number of Business Records")
    plt.xticks(rotation=0)
    plt.tight_layout()

    plt.savefig(
        "western_avenue_section_counts_verified.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.show()
    print("Section-count chart saved successfully.")
else:
    print("No valid section data found. Check the section column.")

plt.title("Business Records by Preliminary Section")
plt.xlabel("Preliminary section")
plt.ylabel("Number of records")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(
    "western_avenue_section_counts_verified.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

# 7. Basic data-quality summary
print("\nData quality:")
print("Rows:", len(df))
print(
    "Missing business categories:",
    (df[category_col] == "Unknown / Missing").sum()
)
print(
    "Exact duplicate rows:",
    df.duplicated().sum()
)
print(
    "Unique business names:",
    df["business_name"].nunique()
)
print(
    "Unique street addresses:",
    df["street_address"].nunique()
)

print("\nFiles created:")
print("- western_avenue_business_composition.csv")
print("- western_avenue_categories_by_section.csv")
print("- western_avenue_top_business_categories.png")
print("- western_avenue_section_counts_verified.png")
