
from pathlib import Path
import pandas as pd

root = Path("data/boundary_candidates")
audit_dir = root / "all_corridor_audit"
summary_file = audit_dir / "all_corridor_boundary_audit_summary.csv"
output_file = audit_dir / "FINAL_BOUNDARY_VALIDATION_REPORT.txt"

df = pd.read_csv(summary_file)

working_buffers = {
    "larchmont_boulevard": 50,
    "olympic_boulevard": 100,
    "vermont_avenue": 100,
    "wilshire_boulevard": 100,
}

decisions = {
    "larchmont_boulevard":
        "Provisional 50m buffer. All records are inside; verify extent visually.",
    "olympic_boulevard":
        "Provisional 100m buffer. Review 2 exceptions; do not widen automatically.",
    "vermont_avenue":
        "Provisional 100m buffer. Review the coordinate exception; do not alter its coordinates.",
    "wilshire_boulevard":
        "Provisional 100m buffer. Review 505 outside records; do not finalize from inclusion alone.",
}

lines = [
    "FINAL CORRIDOR BOUNDARY VALIDATION REPORT",
    "=" * 48,
    "",
    "Status: PROVISIONAL — geometry and exceptions require final review.",
    "Original business records and source road geometries must be preserved.",
    "Do not delete or relocate exception records solely to improve inclusion.",
    "",
    "WORKING BUFFER SUMMARY",
    "-" * 48,
]

for corridor, buffer_m in working_buffers.items():
    row = df[
        (df["corridor"] == corridor) &
        (df["buffer_m"] == buffer_m)
    ]

    if row.empty:
        lines.append(f"{corridor}: MISSING AUDIT ROW")
        continue

    r = row.iloc[0]
    lines.extend([
        "",
        corridor.replace("_", " ").title(),
        f"Working buffer: {buffer_m} m",
        f"Road features: {int(r['official_road_features']) if 'official_road_features' in df.columns else 'see source summary'}",
        f"Business records: {int(r['business_records'])}",
        f"Inside: {int(r['inside_count'])} ({r['inside_pct']:.2f}%)",
        f"Outside: {int(r['outside_count'])}",
        f"Median distance to road: {r['median_road_distance_m']:.2f} m",
        f"Decision: {decisions[corridor]}",
    ])

lines.extend([
    "",
    "FINALIZATION CHECKLIST",
    "-" * 48,
    "[ ] Verify corridor start/end points and road coverage.",
    "[ ] Review exception locations against the full street network and addresses.",
    "[ ] Confirm buffer width based on corridor definition, not inclusion alone.",
    "[ ] Preserve all original records and document unresolved exceptions.",
    "[ ] Rerun clustering only after boundary decisions are accepted.",
    "",
    "This report records provisional decisions, not proof that every boundary is correct.",
])

output_file.write_text("\n".join(lines), encoding="utf-8")
print(f"Report saved: {output_file.resolve()}")
print("\n".join(lines))
