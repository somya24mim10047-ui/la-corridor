
from pathlib import Path
import pandas as pd

folder = Path("data/boundary_candidates/all_corridor_audit")

files = [
    "wilshire_boulevard_outside_150m.csv",
    "olympic_boulevard_outside_100m.csv",
    "vermont_avenue_outside_100m.csv",
]

for filename in files:
    path = folder / filename
    print(f"\n{'=' * 15} {filename} {'=' * 15}")

    if not path.exists():
        print(f"File not found: {path}")
        continue

    df = pd.read_csv(path)
    print(f"Exception records: {len(df)}")
    print("Columns:", df.columns.tolist())
    print(df.to_string(index=False))
