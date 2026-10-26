
from pathlib import Path
import json
import pandas as pd

BASE = Path(__file__).resolve().parent
CONFIG_FILE = BASE / "corridor_boundaries.json"
INPUT_DIR = BASE / "data" / "corridors"
OUTPUT_DIR = BASE / "data" / "boundary_review"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not CONFIG_FILE.exists():
    raise FileNotFoundError(f"Missing configuration: {CONFIG_FILE}")

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    boundaries = json.load(f)

# Coordinate endpoints must be confirmed before filtering.
for corridor, config in boundaries.items():
    if "start_latitude" not in config or "end_latitude" not in config:
        print(
            f"{corridor}: PENDING — add confirmed start/end "
            "latitude and longitude before filtering."
        )

print("\nNo records have been filtered.")
print("Next, add confirmed endpoint coordinates to the JSON config.")
