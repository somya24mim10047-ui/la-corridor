
import pandas as pd

files = [
    "data/corridors/olympic_boulevard_businesses.csv",
    "data/corridors/vermont_avenue_businesses.csv",
]

terms = [
    "SJ INVESTMENT 2020",
    "LOS ANGELES HIGH SCHOOL ALUMNI",
    "ELENA L GARCIA",
]

for file in files:
    df = pd.read_csv(file)

    print(f"\n{'=' * 15} {file} {'=' * 15}")

    for term in terms:
        mask = df.astype(str).apply(
            lambda column: column.str.contains(
                term, case=False, na=False
            )
        ).any(axis=1)

        matches = df.loc[mask]

        if not matches.empty:
            print(f"\nSearch: {term}")
            print(matches.to_string(index=False))

print("\nVerification complete. Original CSVs were not modified.")
