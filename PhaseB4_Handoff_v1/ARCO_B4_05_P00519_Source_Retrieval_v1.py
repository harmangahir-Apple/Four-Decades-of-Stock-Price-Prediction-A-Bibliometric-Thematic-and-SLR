#!/usr/bin/env python3
"""ARCO Phase B4: safe original-source acquisition for P00519.

Run from the root of Stock_Price_Prediction_SLR_ACME:
    python /path/to/ARCO_B4_05_P00519_Source_Retrieval_v1.py

Creates only source and receipt for P00519 inside PhaseB4_Source_Recovery_v1_DRAFT.
Existing source and frozen Phase A/B1/B3 files are never changed.
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

PAPER_ID = "P00519"
DOI = "10.3390/electronics14071275"
TITLE = "Hybrid CNN-BiGRU-AM Model with Anomaly Detection for Nonlinear Stock Price Prediction"
PUBLISHER_PDF_URL = "https://www.mdpi.com/2079-9292/14/7/1275/pdf"
PUBLISHER_LANDING_URL = "https://www.mdpi.com/2079-9292/14/7/1275"
WORKLIST_REL = Path("PhaseA_Identity_Reconciliation_20261102_DRAFT/B4_Unflagged_32_Source_Worklist_v1_DRAFT.csv")
WORKLIST_SHA = "0de60fb595bea7ed172497358bd9d0f04c922f6aafac94b6e7ecf19dd268ed06"
CODEBOOK_REL = Path("PhaseB1_v1_2_Signoff_Candidate/PhaseB1_Evidence_Codebook_v1_2_SIGNOFF_CANDIDATE.csv")
CODEBOOK_SHA = "a1d5778ee8bfcbf8ac314e6f1e70934039434bc9e7e164f0ff915141b7f5a814"
DEST_REL = Path("PhaseB4_Source_Recovery_v1_DRAFT/P00519")
PDF_NAME = "P00519_ORIGINAL_MDPI_2025_CANDIDATE.pdf"
RECEIPT_NAME = "P00519_Source_Identity_Receipt_v1_DRAFT.csv"
MAX_BYTES = 30_000_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fd:
        for chunk in iter(lambda: fd.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp))


def fail(message: str) -> None:
    raise SystemExit("STOP: " + message)


def main() -> None:
    root = Path.cwd()
    print("=== ARCO B4: P00519 ORIGINAL SOURCE RECOVERY ===")
    print("Project:", root)
    worklist = root / WORKLIST_REL
    codebook = root / CODEBOOK_REL
    for src, expected in ((worklist, WORKLIST_SHA), (codebook, CODEBOOK_SHA)):
        if not src.is_file() or sha256(src) != expected:
            fail(f"locked input missing or checksum changed: {src}")

    rows = load_csv(worklist)
    if len(rows) != 32:
        fail("worklist record count is not 32")
    targets = [r for r in rows if r.get("Paper_ID") == PAPER_ID]
    if len(targets) != 1:
        fail("P00519 is missing/duplicated in protected worklist")
    row = targets[0]
    if row.get("Evidence_Scope") != "Full_Text":
        fail("P00519 has unexpected evidence scope")
    if compact(row.get("Original_DOI", "")) != compact(DOI):
        fail("P00519 original DOI does not match frozen working index")
    if compact(row.get("Original_Title", "")) != compact(TITLE):
        fail("P00519 original title does not match working index")
    if len(load_csv(codebook)) != 45:
        fail("B1 codebook field count differs from 45")

    if shutil.which("pdftotext") is None or shutil.which("pdfinfo") is None:
        fail("install poppler-utils to access pdftotext and pdfinfo")

    dest = root / DEST_REL
    final_pdf = dest / PDF_NAME
    receipt = dest / RECEIPT_NAME
    if final_pdf.exists() or receipt.exists():
        fail("source or receipt already exists; no overwrite. Review existing version first")
    if shutil.disk_usage(root).free < 200_000_000:
        fail("less than 200 MB free in project filesystem; do not download")

    # Prepare a temporary PDF OUTSIDE final destination; failures leave no staged content.
    req = urllib.request.Request(
        PUBLISHER_PDF_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; academic source verification)", "Accept": "application/pdf,*/*"},
    )
    fd, tmp = tempfile.mkstemp(prefix="arco_p00519_", suffix=".pdf", dir=str(root))
    os.close(fd)
    tmp_path = Path(tmp)
    try:
        try:
            with urllib.request.urlopen(req, timeout=35) as response:
                count = 0
                with tmp_path.open("wb") as f:
                    while True:
                        block = response.read(1024 * 1024)
                        if not block:
                            break
                        count += len(block)
                        if count > MAX_BYTES:
                            fail("download exceeds 30 MB safety cap")
                        f.write(block)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
            fail("publisher download unavailable (possibly HTTP 403/429): " + str(error)
                 + "\nOpen the official publisher PDF in your browser instead; do not bypass TLS or re-label HTML as PDF")
        if tmp_path.read_bytes()[:5] != b"%PDF-":
            fail("publisher response was not a PDF")
        try:
            info = subprocess.run(["pdfinfo", str(tmp_path)], text=True, capture_output=True, check=True, timeout=30).stdout
            body = subprocess.run(["pdftotext", "-layout", str(tmp_path), "-"], text=True, capture_output=True, check=True, timeout=30).stdout
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            fail("downloaded PDF could not be inspected: " + str(error))
        text = compact(body)
        title_ok = compact(TITLE) in text
        doi_ok = compact(DOI) in text
        if not (title_ok and doi_ok):
            fail(f"original publication mismatch: TITLE={title_ok}, DOI={doi_ok}; no file staged")
        page_match = re.search(r"^Pages:\s+(\d+)", info, flags=re.M)
        pages = int(page_match.group(1)) if page_match else 0
        if pages < 6:
            fail("unexpectedly short PDF; source review needed")
        digest = sha256(tmp_path)
        dest.mkdir(parents=True, exist_ok=True)
        tmp_path.replace(final_pdf)
        manifest = {
            "Paper_ID": PAPER_ID,
            "Original_DOI": DOI,
            "Original_Title": TITLE,
            "Evidence_Scope": "Full_Text",
            "Publisher_Landing_URL": PUBLISHER_LANDING_URL,
            "Source_Download_URL": PUBLISHER_PDF_URL,
            "Source_Path": str(final_pdf.relative_to(root)),
            "Source_SHA256": digest,
            "PDF_Pages": str(pages),
            "Source_Identity_Check": "TITLE_AND_DOI_MATCH",
            "Retrieved_UTC_Date": date.today().isoformat(),
            "Publisher_Correction_Retraction_Screen": "NOT_DEFINITIVELY_ASSESSED",
            "Coding_Status": "NOT_STARTED",
            "Author_Approval": "",
            "Implementation_Status": "SOURCE_RETRIEVED_ONLY",
        }
        with receipt.open("x", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(manifest))
            writer.writeheader()
            writer.writerow(manifest)
        print("PDF:", final_pdf.relative_to(root))
        print("PDF_SHA256:", digest)
        print("PDF_PAGES:", pages)
        print("RECEIPT:", receipt.relative_to(root))
        print("RECEIPT_SHA256:", sha256(receipt))
        print("SOURCE IDENTITY: PASS")
        print("45-FIELD CODING: NOT STARTED")
        print("PHASE A / B1 / B3: UNCHANGED")
        print("VALIDATION: PASS")
    finally:
        tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
