
import pandas as pd

df = pd.read_csv("western_avenue_businesses.csv")

print("\nTOTAL ROWS:", len(df))
print("\nAVAILABLE COLUMNS:")
for column in df.columns:
    print("-", column)

print("\nMISSING VALUES:")
print(df.isna().sum().to_string())

print("\nPOSSIBLE BUSINESS CATEGORY COLUMNS:")
keywords = [
    "type", "industry", "category", "naics",
    "business", "primary", "address"
]

for column in df.columns:
    if any(word in column.lower() for word in keywords):
        print(f"\nColumn: {column}")
        print(df[column].fillna("Missing").value_counts().head(15))
