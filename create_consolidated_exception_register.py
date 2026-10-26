import csv
from pathlib import Path

folder = Path("data/boundary_candidates/all_corridor_audit")
output = folder / "consolidated_exception_register.csv"

rows = []

# Olympic Boulevard
olympic = folder / "olympic_boulevard_outside_100m.csv"
with olympic.open(encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        rows.append({
            "corridor": "olympic_boulevard",
            "review_group": r.get("business_name", ""),
            "records": 1,
            "address_or_sample": r.get("street_address", ""),
            "latitude": r.get("latitude", ""),
            "longitude": r.get("longitude", ""),
            "distance_m": r.get("road_distance_m", ""),
            "status": "Unresolved",
            "recommended_action": "Verify address and coordinates against official mapping; do not widen buffer automatically"
        })

# Vermont Avenue
vermont = folder / "vermont_avenue_outside_100m.csv"
with vermont.open(encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        rows.append({
            "corridor": "vermont_avenue",
            "review_group": r.get("business_name", ""),
            "records": 1,
            "address_or_sample": r.get("street_address", ""),
            "latitude": r.get("latitude", ""),
            "longitude": r.get("longitude", ""),
            "distance_m": r.get("road_distance_m", ""),
            "status": "Unresolved",
            "recommended_action": "Verify address/coordinate and road coverage; do not widen buffer automatically"
        })

# Wilshire Boulevard, grouped by coordinate
wilshire = folder / "wilshire_125m_exception_coordinate_groups.csv"
with wilshire.open(encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        rows.append({
            "corridor": "wilshire_boulevard",
            "review_group": f"Coordinate group {r.get('latitude', '')}, {r.get('longitude', '')}",
            "records": r.get("records", ""),
            "address_or_sample": r.get("sample_addresses", ""),
            "latitude": r.get("latitude", ""),
            "longitude": r.get("longitude", ""),
            "distance_m": r.get("distance_m", ""),
            "status": "Unresolved",
            "recommended_action": "Review address, nearby streets, and mapping evidence; retain source records"
        })

fields = [
    "corridor", "review_group", "records", "address_or_sample",
    "latitude", "longitude", "distance_m", "status", "recommended_action"
]

with output.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print(f"Created: {output}")
print(f"Review entries: {len(rows)}")
print(f"Olympic entries: {sum(r['corridor'] == 'olympic_boulevard' for r in rows)}")
print(f"Vermont entries: {sum(r['corridor'] == 'vermont_avenue' for r in rows)}")
print(f"Wilshire groups: {sum(r['corridor'] == 'wilshire_boulevard' for r in rows)}")
print("All entries remain unresolved pending evidence review.")
