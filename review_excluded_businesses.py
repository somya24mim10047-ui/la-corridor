import pandas as pd
from pathlib import Path

folder = Path("data/final_corridor_boundaries")

for name in ["olympic_boulevard", "wilshire_boulevard"]:
    path = folder / f"{name}_outside_business_diagnostic.csv"
    df = pd.read_csv(path)

    print(f"\n{'='*20} {name.upper()} {'='*20}")
    print("Columns:", df.columns.tolist())

    print("\nClosest 20 excluded businesses:")
    print(df.sort_values("road_distance_m").head(20).to_string(index=False))

    print("\nDistance groups:")
    print(pd.cut(
        df["road_distance_m"],
        bins=[-1, 25, 50, 100, 200, float("inf")],
        labels=["0–25 m", "25–50 m", "50–100 m", "100–200 m", "200+ m"]
    ).value_counts(sort=False))
