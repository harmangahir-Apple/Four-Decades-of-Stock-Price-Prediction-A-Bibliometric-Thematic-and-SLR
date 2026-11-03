import csv
import shutil
from pathlib import Path
from datetime import date, datetime
from collections import Counter

base = Path("PhaseB3_Pilot_Selected_v1")
review_path = base / "B3_pilot_40_AUTHOR_SELECTION_REVIEW.csv"
selection_path = base / "B3_pilot_40_SELECTION_LOCKED_PENDING_AUTHOR.csv"

flagged = {"P01112", "P03446", "P00584", "P00853"}

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)

fields, reviews = read_csv(review_path)
_, selections = read_csv(selection_path)

selected = {r["Paper_ID"]: r for r in selections}

assert len(reviews) == 40
assert len(selected) == 40
assert {r["Paper_ID"] for r in reviews} == set(selected)

print("\nARCO PHASE B3 — AUTHOR SELECTION REVIEW")
print("======================================")
print("40 studies selected")
print("36 routine approval candidates")
print("4 flagged studies requiring investigation\n")

name = input("Enter your reviewer name: ").strip()
if not name:
    raise SystemExit("STOP: Reviewer name cannot be blank.")

review_date = input(
    "Enter actual review date (YYYY-MM-DD): "
).strip()

try:
    date.fromisoformat(review_date)
except ValueError:
    raise SystemExit("STOP: Invalid review date.")

for r in reviews:
    pid = r["Paper_ID"]
    s = selected[pid]

    print("\n" + "=" * 60)
    print("Pilot ID:", r["Pilot_ID"])
    print("Paper ID:", pid)
    print("Title:", s.get("Title", "See selection CSV"))
    print("DOI:", s.get("DOI", "See selection CSV"))

    if pid in flagged:
        print("HOLD: Flagged for investigation.")
        print("Decision will remain blank.")
        continue

    current = r["Pilot_Inclusion_Decision"].strip()

    if current:
        print("Existing decision preserved:", current)
        continue

    answer = input(
        "A = Approve after review; ENTER = Pending: "
    ).strip().upper()

    if answer == "A":
        r["Pilot_Inclusion_Decision"] = "APPROVE"
        r["Reviewer_Name"] = name
        r["Review_Date_YYYY_MM_DD"] = review_date

        if not r["Inclusion_Comments"].strip():
            r["Inclusion_Comments"] = (
                "Author accepted pilot selection after review "
                "of frozen-register eligibility and sampling "
                "criteria. Primary-source verification and "
                "methodological coding remain pending."
            )

        print("APPROVE selected.")
    else:
        print("Decision remains blank.")

counts = Counter(
    r["Pilot_Inclusion_Decision"].strip().upper()
    or "BLANK"
    for r in reviews
)

print("\nPROPOSED DECISIONS:", dict(counts))

confirm = input(
    "\nType SAVE to write the reviewed decisions: "
).strip()

if confirm != "SAVE":
    raise SystemExit("No changes saved.")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = base / f"B3_AUTHOR_REVIEW_BACKUP_{stamp}.csv"

shutil.copy2(review_path, backup)

with review_path.open(
    "w", encoding="utf-8-sig", newline=""
) as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(reviews)

print("\nAUTHOR DECISIONS SAVED")
print("Backup:", backup)
print("Review file:", review_path)
print("Summary:", dict(counts))
print("Frozen Phase A register: UNCHANGED")
