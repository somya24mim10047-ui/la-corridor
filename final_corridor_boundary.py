
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

FOLDER = Path(__file__).parent

business_file = FOLDER / "western_avenue_business_road_distances.csv"
output_file = FOLDER / "western_avenue_final_boundary_comparison.png"

df = pd.read_csv(business_file)

# Check the required columns
print("Available columns:", df.columns.tolist())

required = {"longitude", "latitude", "distance_to_road_m"}
if not required.issubset(df.columns):
    raise ValueError(
        "Required columns are missing. Check the column names printed above."
    )

dist = df["distance_to_road_m"]

fig, axes = plt.subplots(1, 3, figsize=(17, 7))

widths = [50, 100, 200]

for ax, width in zip(axes, widths):
    inside = dist <= width

    ax.scatter(
        df.loc[~inside, "longitude"],
        df.loc[~inside, "latitude"],
        color="red",
        s=24,
        label="Outside buffer",
        alpha=0.8
    )

    ax.scatter(
        df.loc[inside, "longitude"],
        df.loc[inside, "latitude"],
        color="green",
        s=24,
        label="Inside buffer",
        alpha=0.8
    )

    ax.set_title(f"{width} m each side")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True, alpha=0.25)
    ax.legend()

    count = int(inside.sum())
    ax.text(
        0.03, 0.97,
        f"Included: {count}/{len(df)} ({count / len(df) * 100:.1f}%)",
        transform=ax.transAxes,
        va="top",
        bbox=dict(facecolor="white", alpha=0.8)
    )

fig.suptitle(
    "Western Avenue, Los Angeles — Preliminary Buffer Comparison",
    fontsize=14
)
plt.tight_layout()
plt.savefig(output_file, dpi=300, bbox_inches="tight")
plt.show()

print(f"\nSaved map: {output_file}")
