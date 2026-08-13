
from __future__ import annotations

from pathlib import Path
import html
import re
import sys
import pandas as pd

PROJECT_ROOT = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)

OUTPUT_DIR = PROJECT_ROOT / "07_Reference_Outputs_Web"
REGISTER_PATH = OUTPUT_DIR / "Section7_Web_Reference_Register_493.csv"
OUTPUT_BIB = OUTPUT_DIR / "included_studies_493_SPRINGER_CLEAN.bib"
QC_PATH = OUTPUT_DIR / "included_studies_493_SPRINGER_QC.csv"

REQUIRED_COLUMNS = [
    "Paper_ID",
    "Title",
    "Authors",
    "Year",
    "Source_Title",
    "DOI",
    "Volume",
    "Issue",
    "Pages_or_Article_Number",
    "Publisher",
    "URL",
    "Document_Type",
]

CORE_FIELDS = [
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
]

ACRONYMS = [
    "ARIMA", "GARCH", "LSTM", "GRU", "CNN", "RNN", "SVM", "SVR",
    "ANN", "GNN", "GCN", "XGBOOST", "LIGHTGBM", "FINBERT", "BERT",
    "NLP", "AI", "ML", "DL", "IOT", "ESG", "MCMC", "TCN", "DQN",
    "GAN", "CYCLEGAN", "MLP", "GPR", "ARO", "PSO", "GWO", "XAI",
    "LLM", "LLMS", "RELU", "RMSE", "MAE", "MAPE",
]


def clean_text(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_doi(value: object) -> str:
    text = clean_text(value).lower()
    text = re.sub(
        r"^(https?://(dx\.)?doi\.org/|doi:\s*)",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text.strip(" .;,")


def bibtex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def protect_acronyms(title: str) -> str:
    protected = title
    for acronym in sorted(ACRONYMS, key=len, reverse=True):
        pattern = re.compile(
            rf"(?<![A-Za-z0-9{{]){re.escape(acronym)}(?![A-Za-z0-9}}])",
            flags=re.IGNORECASE,
        )
        protected = pattern.sub(lambda m: "{" + m.group(0).upper() + "}", protected)
    return protected


def normalize_pages(value: object) -> str:
    text = clean_text(value)
    text = re.sub(r"\s*[-–—]\s*", "--", text)
    return text


def entry_type(document_type: str) -> str:
    value = document_type.lower().strip()

    if any(token in value for token in ["journal", "article"]):
        if any(token in value for token in ["conference", "proceedings"]):
            return "inproceedings"
        return "article"

    if any(token in value for token in ["conference", "proceedings"]):
        return "inproceedings"

    if any(token in value for token in ["book-chapter", "chapter", "incollection"]):
        return "incollection"

    if value == "book" or "monograph" in value:
        return "book"

    if "thesis" in value or "dissertation" in value:
        return "phdthesis"

    return "misc"


def add_field(lines: list[str], name: str, value: str) -> None:
    if value:
        lines.append(f"  {name:<10} = {{{value}}},")


def make_entry(row: pd.Series) -> str:
    paper_id = clean_text(row["Paper_ID"])
    authors = bibtex_escape(clean_text(row["Authors"]))
    title = protect_acronyms(bibtex_escape(clean_text(row["Title"])))
    year = clean_text(row["Year"])
    source = bibtex_escape(clean_text(row["Source_Title"]))
    doi = normalize_doi(row["DOI"])
    volume = bibtex_escape(clean_text(row["Volume"]))
    issue = bibtex_escape(clean_text(row["Issue"]))
    pages = bibtex_escape(normalize_pages(row["Pages_or_Article_Number"]))
    publisher = bibtex_escape(clean_text(row["Publisher"]))
    url = clean_text(row["URL"])
    doc_type = clean_text(row["Document_Type"])
    kind = entry_type(doc_type)

    lines = [f"@{kind}{{{paper_id},"]
    add_field(lines, "author", authors)
    add_field(lines, "title", title)
    add_field(lines, "year", year)

    if kind == "article":
        add_field(lines, "journal", source)
        add_field(lines, "volume", volume)
        add_field(lines, "number", issue)
        add_field(lines, "pages", pages)
        add_field(lines, "publisher", publisher)

    elif kind in {"inproceedings", "incollection"}:
        add_field(lines, "booktitle", source)
        add_field(lines, "volume", volume)
        add_field(lines, "number", issue)
        add_field(lines, "pages", pages)
        add_field(lines, "publisher", publisher)

    elif kind == "book":
        add_field(lines, "publisher", publisher or source)
        add_field(lines, "volume", volume)

    elif kind == "phdthesis":
        add_field(lines, "school", publisher or source)

    else:
        add_field(lines, "howpublished", source)
        add_field(lines, "publisher", publisher)
        add_field(lines, "volume", volume)
        add_field(lines, "number", issue)
        add_field(lines, "pages", pages)

    add_field(lines, "doi", doi)

    # Avoid duplicated DOI and URL. Keep URL only when no DOI exists.
    if not doi and url:
        add_field(lines, "url", bibtex_escape(url))

    # Deliberately omit all internal audit notes, Paper-ID notes, and match status.
    if lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]

    lines.append("}")
    return "\n".join(lines)


def main() -> None:
    if not REGISTER_PATH.exists():
        raise FileNotFoundError(f"Reference register not found: {REGISTER_PATH}")

    df = pd.read_csv(
        REGISTER_PATH,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing register columns: {missing_columns}")

    for col in REQUIRED_COLUMNS:
        df[col] = df[col].map(clean_text)

    placeholder_pattern = re.compile(
        r"^(correct[a-z]?|your[_ ]?email@example\.com|__clear__|"
        r"manual[_ ]?verification[_ ]?required|unresolved)$",
        flags=re.IGNORECASE,
    )

    qc_rows: list[dict[str, str]] = []

    for _, row in df.iterrows():
        problems: list[str] = []

        if not row["Paper_ID"]:
            problems.append("Missing Paper_ID")
        if not row["Authors"]:
            problems.append("Missing authors")
        if not row["Title"]:
            problems.append("Missing title")
        if not row["Year"]:
            problems.append("Missing year")
        if not row["Source_Title"]:
            problems.append("Missing source title")

        for field in CORE_FIELDS:
            value = clean_text(row[field])
            if value and placeholder_pattern.fullmatch(value):
                problems.append(f"Placeholder in {field}: {value}")

        if "&amp;" in str(row.to_dict()) or "&lt;" in str(row.to_dict()):
            problems.append("Unresolved HTML entity")

        if problems:
            qc_rows.append(
                {
                    "Paper_ID": row["Paper_ID"],
                    "Title": row["Title"],
                    "Problems": " | ".join(problems),
                }
            )

    qc = pd.DataFrame(qc_rows)
    qc.to_csv(QC_PATH, index=False, encoding="utf-8-sig")

    print(f"Register rows: {len(df)}")
    print(f"Unique Paper IDs: {df['Paper_ID'].nunique()}")
    print(f"QC-blocking rows: {len(qc)}")
    print(f"QC report: {QC_PATH}")

    if len(df) != 493:
        raise ValueError(f"Expected 493 records, found {len(df)}.")

    if df["Paper_ID"].nunique() != 493:
        raise ValueError("Paper_ID values are not unique.")

    if not qc.empty:
        print("\nSpringer bibliography was NOT generated.")
        print("Repair the rows listed in the QC file, rerun the reference recovery,")
        print("and then run this exporter again.")
        sys.exit(2)

    entries = [make_entry(row) for _, row in df.sort_values("Paper_ID").iterrows()]
    bib_text = "\n\n".join(entries) + "\n"
    OUTPUT_BIB.write_text(bib_text, encoding="utf-8")

    keys = re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib_text)
    print(f"BibTeX entries written: {len(keys)}")
    print(f"Unique BibTeX keys: {len(set(keys))}")
    print(f"Output: {OUTPUT_BIB}")


if __name__ == "__main__":
    main()
