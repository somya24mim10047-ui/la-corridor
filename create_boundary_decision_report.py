
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent
AUDIT = BASE / "data" / "boundary_candidates" / "all_corridor_audit"
OUT = AUDIT / "boundary_decision_report.txt"

summary_file = AUDIT / "all_corridor_boundary_audit_summary.csv"
summary = pd.read_csv(summary_file)

lines = [
    "CORRIDOR BOUNDARY DECISION REPORT",
    "=" * 60,
    "",
    "Purpose: document boundary evidence before finalizing buffers.",
    "No source datasets or corridor boundaries were modified.",
    "",
    "SUMMARY FROM THE EXISTING AUDIT",
    "-" * 60,
    summary.to_string(index=False),
    "",
    "EXCEPTION REVIEW",
    "-" * 60,
    "",
    "WILSHIRE BOULEVARD",
    "- 10 businesses at 690 Wilshire Place are outside 150 m.",
    "- Nearby official Wilshire Place segments are about 3–91 m away.",
    "- Treat as likely side-street/address-matching exceptions.",
    "- Do not widen the Wilshire Boulevard buffer automatically.",
    "",
    "OLYMPIC BOULEVARD",
    "- SJ Investment: address says Olympic Blvd; nearest returned road",
    "  is Pico Blvd at about 9.5 m.",
    "- High School Alumni Association: nearest returned streets are",
    "  about 142–146 m away despite the Olympic Blvd address.",
    "- Investigate address/coordinate and road-source coverage.",
    "",
    "VERMONT AVENUE",
    "- Elena L Garcia: address says Vermont Avenue; nearest returned",
    "  roads are Kingsley Drive (about 12.6 m) and Beverly Blvd",
    "  (about 20 m). Investigate possible geocoding mismatch.",
    "",
    "DECISION",
    "-" * 60,
    "- Keep existing corridor geometry unchanged for now.",
    "- Do not delete exception records.",
    "- Do not finalize buffer widths from inclusion percentages alone.",
    "- Review the actual road extents and intended corridor endpoints.",
    "- Resolve exceptions before rerunning clustering.",
    "",
    "REVIEW MAPS",
    "-" * 60,
]

map_dir = BASE / "data" / "boundary_candidates" / "complete_road_review_maps"
for path in sorted(map_dir.glob("*.png")):
    lines.append(f"- {path.name}")

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Report created: {OUT}")
print(f"Report lines: {len(lines)}")
print("\n" + "\n".join(lines[:25]))
