#!/usr/bin/env python3
"""
Recover bibliographic metadata for the 493-study technical-synthesis register
using only the authoritative Excel workbook plus Crossref and OpenAlex.

Designed for VS Code Jupyter:
    %run "/full/path/recover_493_bibtex_from_web.py"

Outputs:
    07_Reference_Outputs_Web/
        Section7_Web_Reference_Register_493.csv
        Section7_Web_Match_Audit.csv
        Section7_Web_Weak_Matches.csv
        Section7_Web_Unresolved.csv
        Section7_Manual_Reference_Overrides_TEMPLATE.csv
        included_studies_493_DRAFT.bib
        included_studies_493_DRAFT.ris
        included_studies_493.bib          # only when all required checks pass
        included_studies_493.ris          # only when all required checks pass
        crossref_cache.json
        openalex_cache.json

Important:
- This script does not use or modify the Section 7 method-family taxonomy.
- It matches by title and publication year.
- Crossref is searched first; OpenAlex is used as a second source.
- Weak or unresolved matches must be manually verified before the final BibTeX
  file is used in the manuscript.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
import json
import re
import time

import pandas as pd
import requests


# ============================================================================
# 1. USER SETTINGS
# ============================================================================

PROJECT_DIR = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

WORKBOOK_CANDIDATES = [
    PROJECT_DIR
    / "06_Quality_Assessment"
    / "Section5_5_Review_264_Closed_45_Pending.xlsx",

    PROJECT_DIR
    / "06_Quality_Assessment"
    / "Section5_5_Review_264_Closed_45_Pending(3).xlsx",
]

PREFERRED_SHEETS = [
    "Section5_Coding_Master",
    "Section5_Coding_Consolidated",
    "Sheet1",
]

OUTPUT_DIR = PROJECT_DIR / "07_Reference_Outputs_Web"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Put your real email here. It is sent in polite API requests.
CONTACT_EMAIL = "harmangahir@outlook.com"

EXPECTED_STUDY_COUNT = 493

# Conservative thresholds. Scores are title-similarity values from 0 to 1.
AUTO_ACCEPT_SCORE = 0.965
WEAK_MATCH_SCORE = 0.920

# Small delay between API calls.
REQUEST_DELAY_SECONDS = 0.20

# Number of API candidates requested for each title.
CANDIDATES_PER_SOURCE = 5

# Set to False to use only already-cached API responses.
ALLOW_NEW_API_REQUESTS = True


# ============================================================================
# 2. TEXT HELPERS
# ============================================================================

EMPTY_VALUES = {
    "",
    "nan",
    "none",
    "null",
    "n/a",
    "na",
    "not reported",
    "not stated",
    "-",
    "--",
    "23",
}


def clean_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if text.casefold() in EMPTY_VALUES:
        return ""

    return text


def normalize_title(value: Any) -> str:
    text = clean_text(value).casefold()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_year(value: Any) -> str:
    match = re.search(r"\b(?:19|20)\d{2}\b", clean_text(value))
    return match.group(0) if match else ""


def normalize_doi(value: Any) -> str:
    text = clean_text(value).casefold()
    text = re.sub(
        r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)",
        "",
        text,
    )
    text = text.strip(" .;,")
    return text if text.startswith("10.") else ""


def title_similarity(left: Any, right: Any) -> float:
    left_norm = normalize_title(left)
    right_norm = normalize_title(right)

    if not left_norm or not right_norm:
        return 0.0

    return SequenceMatcher(
        None,
        left_norm,
        right_norm,
    ).ratio()


def year_difference(left: Any, right: Any) -> int | None:
    left_year = normalize_year(left)
    right_year = normalize_year(right)

    if not left_year or not right_year:
        return None

    return abs(int(left_year) - int(right_year))


def first_nonblank(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def split_authors(value: Any) -> list[str]:
    text = clean_text(value)

    if not text:
        return []

    if " and " in text:
        pieces = re.split(r"\s+\band\b\s+", text)
    elif ";" in text:
        pieces = text.split(";")
    elif "|" in text:
        pieces = text.split("|")
    else:
        pieces = [text]

    return [
        re.sub(r"\s+", " ", piece).strip(" ,;")
        for piece in pieces
        if clean_text(piece)
    ]


def bibtex_escape(value: Any) -> str:
    text = clean_text(value)

    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    return text


# ============================================================================
# 3. RECORD MODEL
# ============================================================================

@dataclass
class Candidate:
    source_api: str = ""
    title: str = ""
    authors: str = ""
    year: str = ""
    source_title: str = ""
    doi: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    publisher: str = ""
    url: str = ""
    document_type: str = ""
    openalex_id: str = ""
    title_score: float = 0.0
    year_diff: int | None = None
    combined_score: float = 0.0


# ============================================================================
# 4. LOAD THE 493 STUDIES
# ============================================================================

def locate_workbook() -> Path:
    for path in WORKBOOK_CANDIDATES:
        if path.exists():
            return path

    raise FileNotFoundError(
        "The authoritative workbook was not found. Checked:\n"
        + "\n".join(str(path) for path in WORKBOOK_CANDIDATES)
    )


def standardize_headers(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    dataframe.columns = [
        re.sub(r"\s+", "_", str(column).strip())
        for column in dataframe.columns
    ]
    return dataframe


def select_sheet(workbook: Path) -> tuple[str, pd.DataFrame]:
    excel = pd.ExcelFile(workbook)

    ordered_sheets = [
        sheet
        for sheet in PREFERRED_SHEETS
        if sheet in excel.sheet_names
    ] + [
        sheet
        for sheet in excel.sheet_names
        if sheet not in PREFERRED_SHEETS
    ]

    for sheet in ordered_sheets:
        dataframe = pd.read_excel(
            workbook,
            sheet_name=sheet,
            dtype=str,
            keep_default_na=False,
        )
        dataframe = standardize_headers(dataframe)

        if {"Paper_ID", "Title", "Year"}.issubset(dataframe.columns):
            return sheet, dataframe

    raise KeyError(
        "No worksheet contains Paper_ID, Title, and Year.\n"
        f"Available sheets: {excel.sheet_names}"
    )


def load_studies() -> pd.DataFrame:
    workbook = locate_workbook()
    sheet, dataframe = select_sheet(workbook)

    print("Authoritative workbook:")
    print(workbook)
    print("Selected study-level worksheet:")
    print(sheet)

    for column in dataframe.columns:
        dataframe[column] = (
            dataframe[column]
            .astype(str)
            .str.strip()
        )

    if "Decision_Final" in dataframe.columns:
        decision = (
            dataframe["Decision_Final"]
            .astype(str)
            .str.casefold()
            .str.strip()
        )
        dataframe = dataframe.loc[
            decision.isin({"include", "maybe"})
        ].copy()

    # Known off-topic title--abstract metadata mismatch.
    dataframe = dataframe.loc[
        ~dataframe["Paper_ID"].eq("P00295")
    ].copy()

    dataframe = dataframe.drop_duplicates(
        subset="Paper_ID",
        keep="last",
    )

    dataframe["Paper_ID"] = (
        dataframe["Paper_ID"]
        .astype(str)
        .str.strip()
    )

    dataframe["Title"] = (
        dataframe["Title"]
        .astype(str)
        .map(clean_text)
    )

    dataframe["Year"] = (
        dataframe["Year"]
        .astype(str)
        .map(normalize_year)
    )

    if len(dataframe) != EXPECTED_STUDY_COUNT:
        raise AssertionError(
            f"Expected {EXPECTED_STUDY_COUNT} studies; "
            f"found {len(dataframe)}."
        )

    if dataframe["Paper_ID"].duplicated().any():
        raise AssertionError("Duplicate Paper_ID values remain.")

    if dataframe["Title"].eq("").any():
        raise AssertionError("At least one study has a blank title.")

    return dataframe[
        ["Paper_ID", "Title", "Year"]
    ].sort_values(
        "Paper_ID"
    ).reset_index(drop=True)


# ============================================================================
# 5. API CACHE
# ============================================================================

CROSSREF_CACHE_PATH = OUTPUT_DIR / "crossref_cache.json"
OPENALEX_CACHE_PATH = OUTPUT_DIR / "openalex_cache.json"


def load_json_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_json_cache(path: Path, cache: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            cache,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary.replace(path)


crossref_cache = load_json_cache(CROSSREF_CACHE_PATH)
openalex_cache = load_json_cache(OPENALEX_CACHE_PATH)


# ============================================================================
# 6. HTTP SESSION
# ============================================================================

session = requests.Session()
session.headers.update(
    {
        "User-Agent": (
            "FourDecadeStockSLRReferenceRecovery/1.0 "
            f"(mailto:{CONTACT_EMAIL})"
        )
    }
)


def request_json(
    url: str,
    params: dict[str, Any],
    attempts: int = 4,
) -> dict[str, Any] | None:

    for attempt in range(1, attempts + 1):
        try:
            response = session.get(
                url,
                params=params,
                timeout=40,
            )

            if response.status_code == 200:
                return response.json()

            if response.status_code in {429, 500, 502, 503, 504}:
                wait_seconds = min(2 ** attempt, 20)
                print(
                    f"HTTP {response.status_code}; "
                    f"retrying in {wait_seconds}s"
                )
                time.sleep(wait_seconds)
                continue

            print(
                f"HTTP {response.status_code}: "
                f"{response.url}"
            )
            return None

        except requests.RequestException as error:
            if attempt == attempts:
                print(f"Request failed: {error}")
                return None
            time.sleep(min(2 ** attempt, 20))

    return None


# ============================================================================
# 7. CROSSREF SEARCH
# ============================================================================

def crossref_year(item: dict[str, Any]) -> str:
    for field in [
        "published-print",
        "published-online",
        "published",
        "issued",
        "created",
    ]:
        date_parts = (
            item.get(field, {})
            .get("date-parts", [])
        )

        if date_parts and date_parts[0]:
            return str(date_parts[0][0])

    return ""


def crossref_authors(item: dict[str, Any]) -> str:
    names = []

    for author in item.get("author", []) or []:
        family = clean_text(author.get("family", ""))
        given = clean_text(author.get("given", ""))

        if family and given:
            names.append(f"{family}, {given}")
        else:
            name = first_nonblank(
                family,
                given,
                author.get("name", ""),
            )
            if name:
                names.append(name)

    return " and ".join(names)


def crossref_candidates(
    paper_id: str,
    title: str,
    year: str,
) -> list[Candidate]:

    cache_key = f"{paper_id}|{title}|{year}"

    if cache_key in crossref_cache:
        items = crossref_cache[cache_key]
    elif not ALLOW_NEW_API_REQUESTS:
        items = []
    else:
        params: dict[str, Any] = {
            "query.bibliographic": title,
            "rows": CANDIDATES_PER_SOURCE,
            "mailto": CONTACT_EMAIL,
        }

        if year:
            params["filter"] = (
                f"from-pub-date:{int(year)-1}-01-01,"
                f"until-pub-date:{int(year)+1}-12-31"
            )

        payload = request_json(
            "https://api.crossref.org/works",
            params=params,
        )

        items = (
            payload.get("message", {}).get("items", [])
            if payload
            else []
        )

        crossref_cache[cache_key] = items
        save_json_cache(
            CROSSREF_CACHE_PATH,
            crossref_cache,
        )
        time.sleep(REQUEST_DELAY_SECONDS)

    candidates: list[Candidate] = []

    for item in items:
        candidate_title = first_nonblank(
            *(item.get("title", []) or [])
        )

        if not candidate_title:
            continue

        candidate_year = crossref_year(item)
        difference = year_difference(year, candidate_year)
        title_score = title_similarity(title, candidate_title)

        # Penalize substantial year disagreement.
        year_bonus = 0.025 if difference == 0 else 0.0
        year_penalty = (
            0.0
            if difference in {None, 0, 1}
            else min(0.20, difference * 0.05)
        )

        combined = title_score + year_bonus - year_penalty

        candidates.append(
            Candidate(
                source_api="Crossref",
                title=candidate_title,
                authors=crossref_authors(item),
                year=candidate_year,
                source_title=first_nonblank(
                    *(item.get("container-title", []) or [])
                ),
                doi=normalize_doi(item.get("DOI", "")),
                volume=clean_text(item.get("volume", "")),
                issue=clean_text(item.get("issue", "")),
                pages=first_nonblank(
                    item.get("page", ""),
                    item.get("article-number", ""),
                ),
                publisher=clean_text(
                    item.get("publisher", "")
                ),
                url=clean_text(item.get("URL", "")),
                document_type=clean_text(
                    item.get("type", "")
                ),
                title_score=title_score,
                year_diff=difference,
                combined_score=combined,
            )
        )

    return candidates


# ============================================================================
# 8. OPENALEX SEARCH
# ============================================================================

def openalex_authors(item: dict[str, Any]) -> str:
    names = []

    for authorship in item.get("authorships", []) or []:
        author = authorship.get("author", {}) or {}
        name = clean_text(author.get("display_name", ""))

        if name:
            names.append(name)

    return " and ".join(names)


def openalex_source(item: dict[str, Any]) -> str:
    primary = (
        item.get("primary_location", {}) or {}
    )
    source = primary.get("source", {}) or {}

    return clean_text(source.get("display_name", ""))


def openalex_doi(item: dict[str, Any]) -> str:
    ids = item.get("ids", {}) or {}

    return normalize_doi(
        first_nonblank(
            ids.get("doi", ""),
            item.get("doi", ""),
        )
    )


def openalex_candidates(
    paper_id: str,
    title: str,
    year: str,
) -> list[Candidate]:

    cache_key = f"{paper_id}|{title}|{year}"

    if cache_key in openalex_cache:
        items = openalex_cache[cache_key]
    elif not ALLOW_NEW_API_REQUESTS:
        items = []
    else:
        params: dict[str, Any] = {
            "search": title,
            "per-page": CANDIDATES_PER_SOURCE,
            "mailto": CONTACT_EMAIL,
        }

        if year:
            params["filter"] = (
                f"from_publication_date:{int(year)-1}-01-01,"
                f"to_publication_date:{int(year)+1}-12-31"
            )

        payload = request_json(
            "https://api.openalex.org/works",
            params=params,
        )

        items = payload.get("results", []) if payload else []

        openalex_cache[cache_key] = items
        save_json_cache(
            OPENALEX_CACHE_PATH,
            openalex_cache,
        )
        time.sleep(REQUEST_DELAY_SECONDS)

    candidates: list[Candidate] = []

    for item in items:
        candidate_title = clean_text(
            item.get("display_name", "")
        )

        if not candidate_title:
            continue

        candidate_year = normalize_year(
            item.get("publication_year", "")
        )
        difference = year_difference(year, candidate_year)
        title_score = title_similarity(title, candidate_title)

        year_bonus = 0.025 if difference == 0 else 0.0
        year_penalty = (
            0.0
            if difference in {None, 0, 1}
            else min(0.20, difference * 0.05)
        )

        combined = title_score + year_bonus - year_penalty

        primary = item.get("primary_location", {}) or {}

        candidates.append(
            Candidate(
                source_api="OpenAlex",
                title=candidate_title,
                authors=openalex_authors(item),
                year=candidate_year,
                source_title=openalex_source(item),
                doi=openalex_doi(item),
                volume=clean_text(
                    item.get("biblio", {}).get("volume", "")
                ),
                issue=clean_text(
                    item.get("biblio", {}).get("issue", "")
                ),
                pages=first_nonblank(
                    item.get("biblio", {}).get("first_page", ""),
                    item.get("biblio", {}).get("last_page", ""),
                ),
                publisher=clean_text(
                    (
                        primary.get("source", {}) or {}
                    ).get("host_organization_name", "")
                ),
                url=first_nonblank(
                    primary.get("landing_page_url", ""),
                    item.get("id", ""),
                ),
                document_type=clean_text(item.get("type", "")),
                openalex_id=clean_text(item.get("id", "")),
                title_score=title_score,
                year_diff=difference,
                combined_score=combined,
            )
        )

    return candidates


# ============================================================================
# 9. CANDIDATE SELECTION
# ============================================================================

def candidate_completeness(candidate: Candidate) -> int:
    fields = [
        candidate.authors,
        candidate.year,
        candidate.source_title,
        candidate.doi,
        candidate.volume,
        candidate.issue,
        candidate.pages,
        candidate.publisher,
        candidate.url,
    ]

    return sum(bool(clean_text(field)) for field in fields)


def choose_candidate(
    title: str,
    year: str,
    candidates: list[Candidate],
) -> tuple[Candidate | None, str]:

    if not candidates:
        return None, "Unresolved"

    candidates = sorted(
        candidates,
        key=lambda candidate: (
            candidate.combined_score,
            candidate_completeness(candidate),
            candidate.source_api == "Crossref",
        ),
        reverse=True,
    )

    best = candidates[0]

    if (
        best.title_score >= AUTO_ACCEPT_SCORE
        and best.year_diff in {None, 0, 1}
        and best.authors
        and best.source_title
    ):
        return best, "Auto_Accepted"

    if (
        best.title_score >= WEAK_MATCH_SCORE
        and best.year_diff in {None, 0, 1}
    ):
        return best, "Manual_Verification_Required"

    return best, "Unresolved"


# ============================================================================
# 10. MANUAL OVERRIDES
# ============================================================================

OVERRIDE_PATH = (
    OUTPUT_DIR
    / "Section7_Manual_Reference_Overrides.csv"
)

OVERRIDE_TEMPLATE_PATH = (
    OUTPUT_DIR
    / "Section7_Manual_Reference_Overrides_TEMPLATE.csv"
)

OVERRIDE_FIELDS = [
    "Paper_ID",
    "Authors",
    "Title",
    "Year",
    "Source_Title",
    "DOI",
    "Volume",
    "Issue",
    "Pages_or_Article_Number",
    "Publisher",
    "URL",
    "Document_Type",
    "Verification_Note",
]


def create_override_template() -> None:
    if OVERRIDE_TEMPLATE_PATH.exists():
        return

    pd.DataFrame(
        columns=OVERRIDE_FIELDS
    ).to_csv(
        OVERRIDE_TEMPLATE_PATH,
        index=False,
        encoding="utf-8-sig",
    )


def load_overrides() -> dict[str, dict[str, str]]:
    if not OVERRIDE_PATH.exists():
        return {}

    dataframe = pd.read_csv(
        OVERRIDE_PATH,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    if "Paper_ID" not in dataframe.columns:
        raise KeyError(
            f"{OVERRIDE_PATH.name} must contain Paper_ID."
        )

    dataframe["Paper_ID"] = (
        dataframe["Paper_ID"]
        .astype(str)
        .str.strip()
    )

    return {
        row["Paper_ID"]: {
            column: clean_text(row.get(column, ""))
            for column in dataframe.columns
        }
        for _, row in dataframe.iterrows()
        if row["Paper_ID"]
    }


def apply_override(
    output: dict[str, Any],
    override: dict[str, str] | None,
) -> dict[str, Any]:

    if not override:
        return output

    mapping = {
        "Authors": "Authors",
        "Title": "Title",
        "Year": "Year",
        "Source_Title": "Source_Title",
        "DOI": "DOI",
        "Volume": "Volume",
        "Issue": "Issue",
        "Pages_or_Article_Number": "Pages_or_Article_Number",
        "Publisher": "Publisher",
        "URL": "URL",
        "Document_Type": "Document_Type",
    }

    for override_field, output_field in mapping.items():
        value = clean_text(override.get(override_field, ""))

        if value:
            output[output_field] = (
                normalize_doi(value)
                if output_field == "DOI"
                else value
            )

    output["Match_Status"] = "Manual_Override"
    output["Reference_Source"] = "Manual override"
    output["Verification_Note"] = clean_text(
        override.get("Verification_Note", "")
    )

    return output


# ============================================================================
# 11. BIBTEX AND RIS WRITERS
# ============================================================================

def infer_bibtex_type(row: pd.Series) -> str:
    document_type = clean_text(
        row["Document_Type"]
    ).casefold()
    source = clean_text(
        row["Source_Title"]
    ).casefold()

    if any(
        token in document_type
        for token in [
            "proceedings",
            "conference",
            "posted-content",
        ]
    ):
        return "inproceedings"

    if any(
        token in document_type
        for token in [
            "book-chapter",
            "chapter",
            "incollection",
        ]
    ):
        return "incollection"

    if any(
        token in source
        for token in [
            "conference",
            "proceedings",
        ]
    ):
        return "inproceedings"

    if clean_text(row["Source_Title"]):
        return "article"

    return "misc"


def write_bibtex(
    register: pd.DataFrame,
    output_path: Path,
) -> None:

    entries = []

    for _, row in register.iterrows():
        entry_type = infer_bibtex_type(row)
        fields: list[tuple[str, str]] = []

        authors = clean_text(row["Authors"])
        if authors:
            author_value = " and ".join(
                split_authors(authors)
            )
            fields.append(
                ("author", bibtex_escape(author_value))
            )

        fields.append(
            ("title", bibtex_escape(row["Title"]))
        )

        if clean_text(row["Year"]):
            fields.append(("year", row["Year"]))

        source = clean_text(row["Source_Title"])

        if source:
            source_field = (
                "journal"
                if entry_type == "article"
                else "booktitle"
            )
            fields.append(
                (source_field, bibtex_escape(source))
            )

        optional_fields = [
            ("volume", row["Volume"]),
            ("number", row["Issue"]),
            ("pages", row["Pages_or_Article_Number"]),
            ("publisher", row["Publisher"]),
            ("doi", row["DOI"]),
            ("url", row["URL"]),
            (
                "note",
                (
                    f"Technical-synthesis Paper ID {row['Paper_ID']}; "
                    f"match status: {row['Match_Status']}"
                ),
            ),
        ]

        for name, value in optional_fields:
            text = clean_text(value)
            if text:
                fields.append(
                    (name, bibtex_escape(text))
                )

        body = ",\n".join(
            f"  {name} = {{{value}}}"
            for name, value in fields
        )

        entries.append(
            f"@{entry_type}{{{row['Paper_ID']},\n"
            f"{body}\n"
            f"}}"
        )

    output_path.write_text(
        "\n\n".join(entries) + "\n",
        encoding="utf-8",
    )


def write_ris(
    register: pd.DataFrame,
    output_path: Path,
) -> None:

    lines = []

    type_map = {
        "article": "JOUR",
        "inproceedings": "CPAPER",
        "incollection": "CHAP",
        "misc": "GEN",
    }

    for _, row in register.iterrows():
        bib_type = infer_bibtex_type(row)
        lines.append(f"TY  - {type_map[bib_type]}")
        lines.append(f"ID  - {row['Paper_ID']}")
        lines.append(f"T1  - {row['Title']}")

        for author in split_authors(row["Authors"]):
            lines.append(f"AU  - {author}")

        if clean_text(row["Year"]):
            lines.append(f"PY  - {row['Year']}")

        if clean_text(row["Source_Title"]):
            lines.append(f"JO  - {row['Source_Title']}")

        if clean_text(row["Volume"]):
            lines.append(f"VL  - {row['Volume']}")

        if clean_text(row["Issue"]):
            lines.append(f"IS  - {row['Issue']}")

        if clean_text(row["Pages_or_Article_Number"]):
            lines.append(
                f"SP  - {row['Pages_or_Article_Number']}"
            )

        if clean_text(row["Publisher"]):
            lines.append(f"PB  - {row['Publisher']}")

        if clean_text(row["DOI"]):
            lines.append(f"DO  - {row['DOI']}")

        if clean_text(row["URL"]):
            lines.append(f"UR  - {row['URL']}")

        lines.append(
            f"N1  - Match status: {row['Match_Status']}"
        )
        lines.append("ER  - ")
        lines.append("")

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


# ============================================================================
# 12. MAIN RECOVERY LOOP
# ============================================================================

def main() -> None:
    if CONTACT_EMAIL == "YOUR_EMAIL@example.com":
        raise ValueError(
            "Set CONTACT_EMAIL near the top of the script "
            "before running API requests."
        )

    create_override_template()
    overrides = load_overrides()
    studies = load_studies()

    output_rows = []
    audit_rows = []

    for index, row in studies.iterrows():
        paper_id = row["Paper_ID"]
        title = row["Title"]
        year = row["Year"]

        crossref = crossref_candidates(
            paper_id,
            title,
            year,
        )

        openalex = openalex_candidates(
            paper_id,
            title,
            year,
        )

        all_candidates = crossref + openalex

        candidate, status = choose_candidate(
            title,
            year,
            all_candidates,
        )

        if candidate is None:
            output = {
                "Paper_ID": paper_id,
                "Title": title,
                "Authors": "",
                "Year": year,
                "Source_Title": "",
                "DOI": "",
                "Volume": "",
                "Issue": "",
                "Pages_or_Article_Number": "",
                "Publisher": "",
                "URL": "",
                "Document_Type": "",
                "Reference_Source": "",
                "Match_Status": "Unresolved",
                "Title_Match_Score": 0.0,
                "Year_Difference": "",
                "Matched_Title": "",
                "Verification_Note": "",
            }
        else:
            output = {
                "Paper_ID": paper_id,
                "Title": first_nonblank(
                    candidate.title,
                    title,
                ),
                "Authors": candidate.authors,
                "Year": first_nonblank(
                    candidate.year,
                    year,
                ),
                "Source_Title": candidate.source_title,
                "DOI": candidate.doi,
                "Volume": candidate.volume,
                "Issue": candidate.issue,
                "Pages_or_Article_Number": candidate.pages,
                "Publisher": candidate.publisher,
                "URL": candidate.url,
                "Document_Type": candidate.document_type,
                "Reference_Source": candidate.source_api,
                "Match_Status": status,
                "Title_Match_Score": round(
                    candidate.title_score,
                    4,
                ),
                "Year_Difference": (
                    ""
                    if candidate.year_diff is None
                    else candidate.year_diff
                ),
                "Matched_Title": candidate.title,
                "Verification_Note": "",
            }

        output = apply_override(
            output,
            overrides.get(paper_id),
        )

        # Keep the authoritative workbook title separately.
        output["Workbook_Title"] = title
        output["Workbook_Year"] = year

        output_rows.append(output)

        ranked_candidates = sorted(
            all_candidates,
            key=lambda item: item.combined_score,
            reverse=True,
        )

        for rank, item in enumerate(
            ranked_candidates[:5],
            start=1,
        ):
            audit_rows.append(
                {
                    "Paper_ID": paper_id,
                    "Workbook_Title": title,
                    "Workbook_Year": year,
                    "Candidate_Rank": rank,
                    **asdict(item),
                }
            )

        processed = index + 1
        if processed % 20 == 0 or processed == len(studies):
            print(
                f"Processed {processed}/{len(studies)}"
            )

    register = pd.DataFrame(output_rows)
    audit = pd.DataFrame(audit_rows)

    # Required bibliographic fields for a usable reference.
    required_complete = (
        register["Authors"].map(clean_text).ne("")
        & register["Year"].map(clean_text).ne("")
        & register["Source_Title"].map(clean_text).ne("")
    )

    unresolved_mask = (
        register["Match_Status"].eq("Unresolved")
        | ~required_complete
    )

    weak_mask = (
        register["Match_Status"]
        .eq("Manual_Verification_Required")
    )

    unresolved = register.loc[
        unresolved_mask
    ].copy()

    weak = register.loc[
        weak_mask
    ].copy()

    register_path = (
        OUTPUT_DIR
        / "Section7_Web_Reference_Register_493.csv"
    )
    audit_path = (
        OUTPUT_DIR
        / "Section7_Web_Match_Audit.csv"
    )
    unresolved_path = (
        OUTPUT_DIR
        / "Section7_Web_Unresolved.csv"
    )
    weak_path = (
        OUTPUT_DIR
        / "Section7_Web_Weak_Matches.csv"
    )

    register.to_csv(
        register_path,
        index=False,
        encoding="utf-8-sig",
    )
    audit.to_csv(
        audit_path,
        index=False,
        encoding="utf-8-sig",
    )
    unresolved.to_csv(
        unresolved_path,
        index=False,
        encoding="utf-8-sig",
    )
    weak.to_csv(
        weak_path,
        index=False,
        encoding="utf-8-sig",
    )

    draft_bib = (
        OUTPUT_DIR
        / "included_studies_493_DRAFT.bib"
    )
    draft_ris = (
        OUTPUT_DIR
        / "included_studies_493_DRAFT.ris"
    )

    write_bibtex(register, draft_bib)
    write_ris(register, draft_ris)

    print("\n" + "=" * 76)
    print("493-STUDY WEB REFERENCE RECOVERY COMPLETED")
    print("=" * 76)

    print("\nCompleteness:")
    print("Rows:", len(register))
    print(
        "Unique Paper IDs:",
        register["Paper_ID"].nunique(),
    )
    print(
        "Authors recovered:",
        register["Authors"].map(clean_text).ne("").sum(),
    )
    print(
        "Source titles recovered:",
        register["Source_Title"].map(clean_text).ne("").sum(),
    )
    print(
        "DOIs recovered:",
        register["DOI"].map(clean_text).ne("").sum(),
    )
    print(
        "Automatically accepted:",
        register["Match_Status"].eq("Auto_Accepted").sum(),
    )
    print(
        "Manual verification required:",
        len(weak),
    )
    print(
        "Unresolved/incomplete:",
        len(unresolved),
    )

    print("\nDraft files:")
    print(draft_bib)
    print(draft_ris)

    print("\nAudit files:")
    print(register_path)
    print(audit_path)
    print(weak_path)
    print(unresolved_path)
    print(OVERRIDE_TEMPLATE_PATH)

    # Final files are generated only after all records are complete and
    # no weak matches remain.
    if unresolved.empty and weak.empty:
        final_bib = (
            OUTPUT_DIR
            / "included_studies_493.bib"
        )
        final_ris = (
            OUTPUT_DIR
            / "included_studies_493.ris"
        )

        write_bibtex(register, final_bib)
        write_ris(register, final_ris)

        print("\nFINAL BIBLIOGRAPHY CREATED:")
        print(final_bib)
        print(final_ris)
    else:
        print(
            "\nThe final BibTeX file was not frozen because "
            "weak or unresolved records remain."
        )
        print(
            "Verify those records, create "
            "Section7_Manual_Reference_Overrides.csv from the "
            "template, and rerun the script."
        )


if __name__ == "__main__":
    main()
