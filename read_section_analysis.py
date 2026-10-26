
import pandas as pd

# Load the section-wise business category data
df = pd.read_csv("western_avenue_categories_by_section.csv")

# Convert the wide table into a long, readable table
# Keep the existing 'section' column as an identifier
long_df = df.melt(
    id_vars=["section"],
    var_name="business_category",
    value_name="business_count"
)

# Ensure counts are numeric
long_df["business_count"] = pd.to_numeric(
    long_df["business_count"],
    errors="coerce"
).fillna(0)

# Remove categories with zero businesses
long_df = long_df[long_df["business_count"] > 0].copy()

# Sort by section and descending business count
long_df = long_df.sort_values(
    ["section", "business_count"],
    ascending=[True, False]
)

# Display the 10 most common categories in each section
print("\nTOP 10 BUSINESS CATEGORIES IN EACH SECTION")

for section in sorted(long_df["section"].unique()):
    section_data = long_df[long_df["section"] == section]

    print(f"\nSECTION {section}")
    print(
        section_data[
            ["business_category", "business_count"]
        ].head(10).to_string(index=False)
    )

# Save the readable results
long_df.to_csv(
    "western_avenue_categories_readable.csv",
    index=False
)

print("\nSaved: western_avenue_categories_readable.csv")

# Create a comparison chart of the top 10 categories overall
import matplotlib.pyplot as plt

top_categories = (
    long_df.groupby("business_category")["business_count"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .sort_values()
)

plt.figure(figsize=(11, 7))
top_categories.plot(kind="barh")

plt.title("Top 10 Business Categories Across Western Avenue")
plt.xlabel("Number of Business Records")
plt.ylabel("Business Category")
plt.tight_layout()

plt.savefig(
    "western_avenue_top_categories_comparison.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("Saved: western_avenue_top_categories_comparison.png")

