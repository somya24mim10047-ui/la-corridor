
import pandas as pd
from pathlib import Path

files = {
    "Olympic": Path("data/corridors/olympic_boulevard_businesses.csv"),
    "Vermont": Path("data/corridors/vermont_avenue_businesses.csv"),
}

targets = {
    "Olympic": [
        "SJ INVESTMENT 2020 LLC",
        "LOS ANGELES HIGH SCHOOL ALUMNI ASSOCIATION",
    ],
    "Vermont": ["ELENA L GARCIA"],
}

for corridor, path in files.items():
    df = pd.read_csv(path)

    print(f"\n{'=' * 65}\n{corridor}")
    print("Available columns:", df.columns.tolist())

    for name in targets[corridor]:
        matches = df[
            df["business_name"].astype(str).str.contains(
                name, case=False, regex=False, na=False
            )
        ]

        for _, row in matches.iterrows():
            print(f"\nBusiness: {row.get('business_name')}")
            for column in df.columns:
                print(f"  {column}: {row.get(column)}")

print("\nInspection complete. No files modified.")
