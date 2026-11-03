#!/usr/bin/env python3
"""
Extract author affiliations for a fixed list of 175 DOIs.

Source priority:
1. Local Scopus/WoS/IEEE CSV and XLSX files under the ACME project.
2. Crossref REST metadata for unresolved rows.
3. OpenAlex when OPENALEX_API_KEY is set.
4. IEEE Xplore Metadata API when IEEE_API_KEY is set.

The script NEVER infers affiliation or country from author names.
It creates a separate output workbook and does not modify source files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

try:
    import pandas as pd
    import requests
except ImportError as exc:
    raise SystemExit(
        "Missing package. Install with:\n"
        "  python3 -m pip install pandas openpyxl requests\n"
        f"Original error: {exc}"
    )

PROJECT_DEFAULT = Path(
    "/home/harman/projects/SLR Stock Price Prediction/"
    "Stock_Price_Prediction_SLR_ACME"
)
OUTPUT_DIR_DEFAULT = PROJECT_DEFAULT / "Affiliation_Extraction_Output"

DOIS = ['10.1109/R10-HTC54060.2022.9930042', '10.23919/ACIECPS00006.2026.00010', '10.1109/UEMCON59035.2023.10316142', '10.1109/ICISS49785.2020.9315988', '10.1109/ICAICCIT64383.2024.10912165', '10.1109/SCEECS61402.2024.10481893', '10.1109/IGESSC50231.2020.9285163', '10.1109/SACI51354.2021.9465634', '10.1109/IC-ICNS68863.2026.11537469', '10.1109/DAPIC66097.2025.00132', '10.1109/BigData52589.2021.9671412', '10.1109/CISCT55310.2022.10046540', '10.1109/ICCOINS49721.2021.9497157', '10.1109/ICCIAA68481.2026.11544016', '10.1109/ICMLC56445.2022.9941296', '10.1109/ICCCI50826.2021.9456999', '10.1109/AiDAS60501.2023.10284713', '10.1109/ISCON65210.2025.11340805', '10.1109/TLA.2020.9082218', '10.1109/InTech64186.2025.11198495', '10.1109/CONECCT50063.2020.9198494', '10.1109/INMIC64792.2024.11004356', '10.1109/SIML61815.2024.10578097', '10.1109/IMCOM51814.2021.9377370', '10.1109/ICCICT50803.2021.9510159', '10.1109/ACET61898.2024.10730548', '10.1109/IRASET57153.2023.10152930', '10.1109/GCAT55367.2022.9972059', '10.1109/ACCESS.2025.3631096', '10.1109/ICIC56845.2022.10006897', '10.1109/ICBDML68582.2026.11544752', '10.1109/ICECAA55415.2022.9936204', '10.1109/ACCESS.2020.3015966', '10.1109/ICFTS62006.2025.11031782', '10.1109/ICOA55659.2022.9934252', '10.1109/ICSSES64899.2025.11009670', '10.23919/Eusipco47968.2020.9287506', '10.1109/ICSSSM.2018.8464968', '10.1109/TLA.2021.9827469', '10.1109/ICASS69550.2026.11547618', '10.1109/ICSSCNA68616.2026.11547024', '10.1109/ICoICT66265.2025.11192904', '10.1109/ELECO64362.2024.10847128', '10.1109/InCIT60207.2023.10413152', '10.1109/CSNT64827.2025.10967767', '10.1109/ACCESS.2026.3704368', '10.1109/ICONSTEM65670.2025.11374519', '10.1109/ICTAI.2019.00223', '10.1109/BigData.2015.7364089', '10.1109/ICAAIC56838.2023.10140439', '10.1109/ICESC60852.2024.10689888', '10.1109/TEMSCON-ASPAC65329.2025.11512152', '10.1109/ACCESS.2022.3199008', '10.1109/SIU.2017.7960512', '10.1109/IC3I56241.2022.10072525', '10.1109/ICTBIG68706.2025.11323922', '10.1109/SIU49456.2020.9302107', '10.1109/ICISESSC68634.2026.11542709', '10.1109/TKDE.2021.3108831', '10.1109/ICoICT66265.2025.11193001', '10.1109/ICOCT64433.2025.11118499', '10.1109/AiDAS63860.2024.10730589', '10.1109/ZINC58345.2023.10174252', '10.1109/ICSC56153.2023.00020', '10.1109/RMKMATE59243.2023.10368702', '10.1109/ICIICS67880.2026.11483594', '10.1109/ICIRCA65293.2025.11089539', '10.1109/Blockchain55522.2022.00061', '10.1109/NABIC.2009.5393728', '10.1109/CMCSN.2016.40', '10.1109/ICCITM56309.2022.10031655', '10.1109/CSNT51715.2021.9509730', '10.1109/ICICTA.2012.8', '10.1109/ICTACS59847.2023.10389912', '10.1109/ISDA.2014.7066264', '10.1109/ICICV68925.2026.11554632', '10.1109/ISED67359.2025.11404855', '10.1109/CEC.2008.4630957', '10.1109/IJCNN.2004.1379837', '10.1109/R10-HTC59322.2024.10778666', '10.1109/IIAI-AAI.2016.157', '10.1109/INCET57972.2023.10170592', '10.1109/I2CT51068.2021.9417935', '10.23919/AISE.2025.000018', '10.1109/ICMLA.2011.99', '10.1109/INCET49848.2020.9154061', '10.1109/ICCC51575.2020.9345303', '10.1109/APCIT65661.2025.11411304', '10.1109/ICIRCA54612.2022.9985501', '10.1109/CIMCA.2005.1631572', '10.1109/IC-ICNS68863.2026.11537669', '10.1109/ICCSP68173.2026.11539251', '10.1109/BigData50022.2020.9378054', '10.1109/CICN56167.2022.10008298', '10.1109/IEEM55944.2022.9989878', '10.1109/ICSCNA58489.2023.10370267', '10.1109/IC3IT66137.2025.11340806', '10.1109/ComPE53109.2021.9752138', '10.1109/ICCIAA68481.2026.11543673', '10.1109/ICIT59216.2023.10335889', '10.1109/ICCASIT53235.2021.9633358', '10.1109/ICOEI68323.2026.11541341', '10.1109/ICAC3N53548.2021.9725684', '10.1109/UBMK.2017.8093449', '10.1109/KhPIWeek61434.2024.10878088', '10.1109/CONIT55038.2022.9847963', '10.1109/PEEEC67807.2025.00038', '10.1109/DASA63652.2024.10836371', '10.1109/ICCSAI53272.2021.9609720', '10.1109/ICAII59460.2023.10497212', '10.1109/IEEM58616.2023.10406964', '10.1109/ICIEV.2013.6572570', '10.1109/ICSCSS57650.2023.10169337', '10.1109/ICETCI53161.2021.9563518', '10.1109/DASC-PICom-DataCom-CyberSciTec.2017.169', '10.1109/SITA.2016.7772262', '10.1109/MI-STA68962.2026.11511309', '10.1109/ICIFE.2010.5609262', '10.1109/ICCSIT.2008.128', '10.1109/COMPSAC57700.2023.00175', '10.1109/ICICoS68590.2025.11329893', '10.1109/ICCPEIC.2014.6915414', '10.1109/QPAIN69676.2026.11545577', '10.1109/ICSTEM61137.2024.10560659', '10.1109/ICMLC.2018.8526942', '10.1109/ICCUBEA58933.2023.10392010', '10.1109/CCDC.2008.4598334', '10.1109/ICAICTA59291.2023.10390037', '10.1109/HNICEM64917.2024.11258818', '10.1109/ICONSTEM.2017.8261274', '10.1109/ITNEC.2019.8729026', '10.1109/ICSCTET.2015.7371196', '10.1109/CSITSS67709.2025.11295220', '10.1109/ICSESS.2016.7883081', '10.1109/AIDE69088.2026.11544548', '10.1109/ACCESS.2021.3114809', '10.1109/CSI54720.2022.9924117', '10.1109/ICIEECT.2017.7916583', '10.1109/ICMLA.2011.82', '10.1109/TSMC.2024.3402160', '10.1109/CVMI59935.2023.10465177', '10.1109/AIDE69088.2026.11544719', '10.1109/ICISCN64258.2025.10934450', '10.1109/GCAT62922.2024.10923875', '10.1109/IJCNN.2000.859420', '10.1109/MLSP.2010.5588996', '10.1109/ICMLC.2003.1259702', '10.1109/IJCNN64981.2025.11229220', '10.1109/ICCCNT61001.2024.10724473', '10.1162/neco.1997.9.1.1', '10.1109/TSMCA.2007.904825', '10.1109/CEC.2010.5586284', '10.1109/ACT.2010.1', '10.1109/TNNLS.2025.3584369', '10.1109/ICMLCN59089.2024.10625144', '10.1109/IJCNN64981.2025.11227374', '10.1109/NICS.2016.7725636', '10.1109/IC3I59117.2023.10397816', '10.1109/WI-IAT.2014.91', '10.1109/IJCNN.2015.7280517', '10.1109/ICSCAN49426.2020.9262356', '10.1109/WIIAT.2008.309', '10.1109/ICICT60155.2024.10544766', '10.1109/SIU53274.2021.9477814', '10.1109/ICBDA.2016.7509794', '10.1109/ICSESS.2012.6269415', '10.1109/DASC/PiCom/CBDCom/CyberSciTech.2019.00046', '10.1109/WI-IAT.2012.206', '10.1109/ICCCBDA.2016.7529584', '10.1109/SYNASC.2015.65', '10.1109/IICAIET55139.2022.9936756', '10.1109/SMDS53860.2021.00034', '10.1109/CEC.2016.7744230', '10.23919/CISTI.2017.7975837', '10.1109/WI-IAT.2015.82']

DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)

DOI_EXACT = {
    "doi", "digitalobjectidentifier", "documentdoi", "articledoi",
    "electronicdoi", "digitalobjectid"
}
TITLE_EXACT = {
    "title", "documenttitle", "articletitle", "papertitle", "itemtitle"
}
AUTHORS_EXACT = {
    "authors", "author", "authornames", "authorfullnames",
    "author(s)", "creators"
}
COUNTRY_HINTS = {
    "country", "countries", "affiliationcountry", "authorcountry",
    "countryterritory"
}

SOURCE_HINTS = (
    "dataset_c", "scopus", "wos", "web_of_science", "web of science",
    "ieee", "query_1", "merged", "cleaned"
)


def canonical(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def normalize_doi(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return ""
    text = re.sub(r"^\s*(https?://(dx\.)?doi\.org/|doi\s*:)\s*", "", text, flags=re.I)
    match = DOI_PATTERN.search(text)
    return match.group(0).rstrip(".,;").lower() if match else ""


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "none", "null", "n/a", "na"} else text


def unique_join(values: Iterable[Any], sep: str = "; ") -> str:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = clean_text(value)
        if not text:
            continue
        key = re.sub(r"\s+", " ", text).strip().casefold()
        if key not in seen:
            seen.add(key)
            out.append(re.sub(r"\s+", " ", text).strip())
    return sep.join(out)


def detect_columns(columns: Iterable[Any]) -> dict[str, list[str]]:
    names = [str(c) for c in columns]
    canon = {name: canonical(name) for name in names}

    doi_cols = [
        name for name, c in canon.items()
        if c in DOI_EXACT or c == "doi" or c.endswith("doi")
    ]
    affiliation_cols = [
        name for name, c in canon.items()
        if "affiliation" in c
        and not any(x in c for x in ("affiliationid", "affiliationidentifier"))
    ]
    title_cols = [name for name, c in canon.items() if c in TITLE_EXACT]
    authors_cols = [name for name, c in canon.items() if c in AUTHORS_EXACT]
    country_cols = [
        name for name, c in canon.items()
        if c in COUNTRY_HINTS or c.endswith("country") or c.endswith("countries")
    ]

    return {
        "doi": doi_cols,
        "affiliation": affiliation_cols,
        "title": title_cols,
        "authors": authors_cols,
        "country": country_cols,
    }


def source_priority(path: Path) -> int:
    name = path.name.lower()
    score = 0
    for index, hint in enumerate(SOURCE_HINTS):
        if hint in name:
            score += 100 - index
    if "dataset_c_scopus_wos_ieee_cleaned" in name:
        score += 1000
    if path.suffix.lower() == ".csv":
        score += 5
    return score


def record_from_row(
    row: pd.Series,
    cols: dict[str, list[str]],
    source: str,
    sheet: str,
    priority: int,
) -> dict[str, Any] | None:
    doi = ""
    for col in cols["doi"]:
        doi = normalize_doi(row.get(col))
        if doi:
            break
    if not doi:
        return None

    return {
        "doi": doi,
        "affiliation": unique_join(row.get(c) for c in cols["affiliation"]),
        "country": unique_join(row.get(c) for c in cols["country"]),
        "title": unique_join(row.get(c) for c in cols["title"]),
        "authors": unique_join(row.get(c) for c in cols["authors"]),
        "source": source,
        "sheet": sheet,
        "priority": priority,
    }


def scan_csv(
    path: Path,
    targets: set[str],
    matches: dict[str, list[dict[str, Any]]],
    log: list[dict[str, Any]],
) -> None:
    encodings = ("utf-8-sig", "utf-8", "latin-1")
    last_error = ""
    for encoding in encodings:
        try:
            header = pd.read_csv(
                path, nrows=3, encoding=encoding, low_memory=False,
                on_bad_lines="skip"
            )
            cols = detect_columns(header.columns)
            if not cols["doi"]:
                log.append({
                    "File": str(path), "Sheet": "", "Status": "Skipped",
                    "Rows_Matched": 0, "Message": "No DOI column"
                })
                return

            usecols = list(dict.fromkeys(
                cols["doi"] + cols["affiliation"] + cols["country"]
                + cols["title"] + cols["authors"]
            ))
            count = 0
            for chunk in pd.read_csv(
                path, usecols=usecols, dtype=str, encoding=encoding,
                chunksize=100_000, low_memory=False, on_bad_lines="skip"
            ):
                for _, row in chunk.iterrows():
                    rec = record_from_row(
                        row, cols, str(path), "", source_priority(path)
                    )
                    if rec and rec["doi"] in targets:
                        matches[rec["doi"]].append(rec)
                        count += 1
            log.append({
                "File": str(path), "Sheet": "", "Status": "Scanned",
                "Rows_Matched": count, "Message": f"Encoding={encoding}"
            })
            return
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    log.append({
        "File": str(path), "Sheet": "", "Status": "Error",
        "Rows_Matched": 0, "Message": last_error
    })


def scan_excel(
    path: Path,
    targets: set[str],
    matches: dict[str, list[dict[str, Any]]],
    log: list[dict[str, Any]],
) -> None:
    try:
        xls = pd.ExcelFile(path)
    except Exception as exc:
        log.append({
            "File": str(path), "Sheet": "", "Status": "Error",
            "Rows_Matched": 0, "Message": f"{type(exc).__name__}: {exc}"
        })
        return

    for sheet_name in xls.sheet_names:
        try:
            header = pd.read_excel(path, sheet_name=sheet_name, nrows=3, dtype=str)
            cols = detect_columns(header.columns)
            if not cols["doi"]:
                continue
            usecols = list(dict.fromkeys(
                cols["doi"] + cols["affiliation"] + cols["country"]
                + cols["title"] + cols["authors"]
            ))
            frame = pd.read_excel(
                path, sheet_name=sheet_name, usecols=usecols, dtype=str
            )
            count = 0
            for _, row in frame.iterrows():
                rec = record_from_row(
                    row, cols, str(path), sheet_name, source_priority(path)
                )
                if rec and rec["doi"] in targets:
                    matches[rec["doi"]].append(rec)
                    count += 1
            log.append({
                "File": str(path), "Sheet": sheet_name, "Status": "Scanned",
                "Rows_Matched": count, "Message": ""
            })
        except Exception as exc:
            log.append({
                "File": str(path), "Sheet": sheet_name, "Status": "Error",
                "Rows_Matched": 0, "Message": f"{type(exc).__name__}: {exc}"
            })


def scan_local_files(project_root: Path, targets: set[str]):
    matches: dict[str, list[dict[str, Any]]] = defaultdict(list)
    log: list[dict[str, Any]] = []

    candidates = [
        p for p in project_root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in {".csv", ".xlsx", ".xls"}
        and "Affiliation_Extraction_Output" not in str(p)
        and not p.name.startswith("~$")
    ]
    candidates.sort(key=lambda p: (-source_priority(p), str(p).lower()))

    print(f"Scanning {len(candidates)} local CSV/Excel files...")
    for i, path in enumerate(candidates, start=1):
        try:
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > 500:
                log.append({
                    "File": str(path), "Sheet": "", "Status": "Skipped",
                    "Rows_Matched": 0,
                    "Message": f"File too large ({size_mb:.1f} MB)"
                })
                continue
            print(f"[{i}/{len(candidates)}] {path.name}")
            if path.suffix.lower() == ".csv":
                scan_csv(path, targets, matches, log)
            else:
                scan_excel(path, targets, matches, log)
        except Exception as exc:
            log.append({
                "File": str(path), "Sheet": "", "Status": "Error",
                "Rows_Matched": 0, "Message": f"{type(exc).__name__}: {exc}"
            })

    return matches, log


def consolidate_local(records: list[dict[str, Any]]) -> dict[str, str]:
    if not records:
        return {}
    ordered = sorted(records, key=lambda r: r["priority"], reverse=True)
    affiliation_records = [r for r in ordered if r["affiliation"]]
    chosen = affiliation_records if affiliation_records else ordered

    return {
        "Affiliations": unique_join(r["affiliation"] for r in chosen),
        "Country": unique_join(r["country"] for r in chosen),
        "Title": next((r["title"] for r in ordered if r["title"]), ""),
        "Authors": next((r["authors"] for r in ordered if r["authors"]), ""),
        "Source": unique_join(
            f'{r["source"]}'
            + (f' [{r["sheet"]}]' if r["sheet"] else "")
            for r in chosen
        ),
        "Status": (
            "Recovered from local metadata"
            if any(r["affiliation"] for r in records)
            else "Local record found; affiliation blank"
        ),
    }


def request_json(
    session: requests.Session,
    url: str,
    params: dict[str, Any] | None = None,
    attempts: int = 3,
) -> dict[str, Any] | None:
    for attempt in range(attempts):
        try:
            response = session.get(url, params=params, timeout=40)
            if response.status_code == 404:
                return None
            if response.status_code == 429:
                time.sleep(2 ** (attempt + 1))
                continue
            response.raise_for_status()
            return response.json()
        except Exception:
            if attempt == attempts - 1:
                return None
            time.sleep(1.5 * (attempt + 1))
    return None


def crossref_lookup(session: requests.Session, doi: str) -> dict[str, str]:
    payload = request_json(
        session,
        "https://api.crossref.org/works/" + quote(doi, safe=""),
    )
    if not payload:
        return {}
    message = payload.get("message") or {}
    affiliations: list[str] = []
    author_names: list[str] = []
    author_map: list[str] = []

    for author in message.get("author") or []:
        name = " ".join(
            x for x in [author.get("given", ""), author.get("family", "")] if x
        ).strip()
        affs = [
            clean_text(a.get("name"))
            for a in (author.get("affiliation") or [])
            if isinstance(a, dict)
        ]
        author_names.append(name)
        affiliations.extend(affs)
        if name and any(affs):
            author_map.append(f"{name}: {unique_join(affs, ' | ')}")

    title_value = message.get("title") or []
    title = title_value[0] if isinstance(title_value, list) and title_value else ""

    return {
        "Affiliations": unique_join(affiliations),
        "Author_Affiliation_Map": unique_join(author_map),
        "Title": clean_text(title),
        "Authors": unique_join(author_names),
        "Country": "",
        "Source": f"https://api.crossref.org/works/{quote(doi, safe='')}",
        "Status": (
            "Recovered from Crossref"
            if unique_join(affiliations)
            else "Crossref record found; affiliation blank"
        ),
    }


def openalex_batch_lookup(
    session: requests.Session,
    dois: list[str],
    api_key: str,
) -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    if not api_key or not dois:
        return output

    for start in range(0, len(dois), 40):
        batch = dois[start:start + 40]
        doi_filter = "|".join(f"https://doi.org/{d}" for d in batch)
        payload = request_json(
            session,
            "https://api.openalex.org/works",
            params={
                "filter": f"doi:{doi_filter}",
                "per_page": 50,
                "api_key": api_key,
            },
        )
        if not payload:
            continue

        for work in payload.get("results") or []:
            doi = normalize_doi(work.get("doi"))
            if not doi:
                continue
            affiliations: list[str] = []
            countries: list[str] = []
            authors: list[str] = []
            author_map: list[str] = []

            for authorship in work.get("authorships") or []:
                author = authorship.get("author") or {}
                author_name = clean_text(author.get("display_name"))
                authors.append(author_name)
                raw_affs = authorship.get("raw_affiliation_strings") or []
                inst_names = [
                    clean_text(inst.get("display_name"))
                    for inst in (authorship.get("institutions") or [])
                    if isinstance(inst, dict)
                ]
                author_affs = raw_affs or inst_names
                affiliations.extend(author_affs)
                countries.extend(authorship.get("countries") or [])
                if author_name and author_affs:
                    author_map.append(
                        f"{author_name}: {unique_join(author_affs, ' | ')}"
                    )

            output[doi] = {
                "Affiliations": unique_join(affiliations),
                "Author_Affiliation_Map": unique_join(author_map),
                "Title": clean_text(work.get("title")),
                "Authors": unique_join(authors),
                "Country": unique_join(countries),
                "Source": f"https://api.openalex.org/works/doi:{doi}",
                "Status": (
                    "Recovered from OpenAlex"
                    if unique_join(affiliations)
                    else "OpenAlex record found; affiliation blank"
                ),
            }
        time.sleep(0.15)

    return output


def ieee_lookup(
    session: requests.Session,
    doi: str,
    api_key: str,
) -> dict[str, str]:
    if not api_key:
        return {}
    payload = request_json(
        session,
        "https://ieeexploreapi.ieee.org/api/v1/search/articles",
        params={
            "apikey": api_key,
            "format": "json",
            "max_records": 25,
            "start_record": 1,
            "doi": doi,
        },
    )
    if not payload:
        return {}
    articles = payload.get("articles") or []
    if not articles:
        return {}
    article = articles[0]

    affiliations: list[str] = []
    authors: list[str] = []
    author_map: list[str] = []

    authors_obj = article.get("authors") or {}
    author_rows = (
        authors_obj.get("authors", [])
        if isinstance(authors_obj, dict)
        else authors_obj if isinstance(authors_obj, list) else []
    )
    for author in author_rows:
        if not isinstance(author, dict):
            continue
        name = clean_text(
            author.get("full_name") or author.get("author_name")
            or author.get("name")
        )
        aff = author.get("affiliation")
        aff_values = aff if isinstance(aff, list) else [aff]
        aff_values = [clean_text(x) for x in aff_values if clean_text(x)]
        authors.append(name)
        affiliations.extend(aff_values)
        if name and aff_values:
            author_map.append(f"{name}: {unique_join(aff_values, ' | ')}")

    top_aff = article.get("affiliation") or article.get("affiliations")
    if isinstance(top_aff, list):
        affiliations.extend(top_aff)
    elif top_aff:
        affiliations.append(top_aff)

    return {
        "Affiliations": unique_join(affiliations),
        "Author_Affiliation_Map": unique_join(author_map),
        "Title": clean_text(article.get("title")),
        "Authors": unique_join(authors),
        "Country": "",
        "Source": (
            "https://ieeexploreapi.ieee.org/api/v1/search/articles"
            f"?doi={quote(doi, safe='')}"
        ),
        "Status": (
            "Recovered from IEEE Xplore API"
            if unique_join(affiliations)
            else "IEEE API record found; affiliation blank"
        ),
    }


def merge_result(base: dict[str, str], candidate: dict[str, str]) -> dict[str, str]:
    if not candidate:
        return base
    merged = dict(base)
    for field in ("Affiliations", "Author_Affiliation_Map", "Country"):
        if candidate.get(field):
            merged[field] = unique_join(
                [merged.get(field, ""), candidate.get(field, "")]
            )
    for field in ("Title", "Authors"):
        if not merged.get(field) and candidate.get(field):
            merged[field] = candidate[field]
    if candidate.get("Source"):
        merged["Source"] = unique_join(
            [merged.get("Source", ""), candidate["Source"]]
        )
    if candidate.get("Affiliations"):
        if not merged.get("Status") or "blank" in merged.get("Status", "").lower():
            merged["Status"] = candidate.get("Status", "Recovered")
    elif not merged.get("Status"):
        merged["Status"] = candidate.get("Status", "")
    return merged


def format_workbook(path: Path) -> None:
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    workbook = load_workbook(path)
    widths = {
        "S.No.": 8, "DOI": 42, "Title": 55, "Authors": 45,
        "Affiliations": 70, "Author_Affiliation_Map": 80,
        "Country": 24, "Status": 34, "Source": 65, "Notes": 42,
    }

    for sheet in workbook.worksheets:
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F4E78")
            cell.alignment = Alignment(horizontal="center", vertical="center")
        sheet.row_dimensions[1].height = 26

        header_map = {cell.value: cell.column for cell in sheet[1]}
        for header, col_index in header_map.items():
            sheet.column_dimensions[get_column_letter(col_index)].width = widths.get(
                str(header), 24
            )

        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(
                    vertical="top",
                    wrap_text=True,
                )

        if sheet.title == "Affiliations" and "Status" in header_map:
            status_col = header_map["Status"]
            for row_index in range(2, sheet.max_row + 1):
                cell = sheet.cell(row=row_index, column=status_col)
                value = str(cell.value or "").lower()
                if value.startswith("recovered"):
                    cell.fill = PatternFill("solid", fgColor="C6EFCE")
                elif "blank" in value or "not recovered" in value:
                    cell.fill = PatternFill("solid", fgColor="FFC7CE")

    workbook.save(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_DEFAULT,
        help="Root folder searched recursively for CSV/XLSX metadata files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR_DEFAULT,
        help="Folder for the extracted XLSX and CSV files.",
    )
    parser.add_argument(
        "--no-online",
        action="store_true",
        help="Use local project metadata only.",
    )
    args = parser.parse_args()

    project_root = args.project_root.expanduser().resolve()
    output_dir = args.output_dir.expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not project_root.exists():
        print(f"ERROR: project root does not exist: {project_root}", file=sys.stderr)
        return 2

    normalized_dois = [normalize_doi(d) for d in DOIS]
    target_set = set(normalized_dois)
    if len(target_set) != len(DOIS):
        print("ERROR: duplicate/invalid DOI detected in embedded list.", file=sys.stderr)
        return 2

    local_matches, scan_log = scan_local_files(project_root, target_set)

    results: dict[str, dict[str, str]] = {}
    for doi in normalized_dois:
        local = consolidate_local(local_matches.get(doi, []))
        results[doi] = {
            "DOI": doi,
            "Title": local.get("Title", ""),
            "Authors": local.get("Authors", ""),
            "Affiliations": local.get("Affiliations", ""),
            "Author_Affiliation_Map": "",
            "Country": local.get("Country", ""),
            "Status": local.get("Status", "Not recovered"),
            "Source": local.get("Source", ""),
            "Notes": "",
        }

    if not args.no_online:
        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "AffiliationExtractor/1.0 "
                "(mailto:research-metadata@example.com)"
            )
        })

        missing = [
            doi for doi in normalized_dois
            if not results[doi]["Affiliations"]
        ]
        print(f"Local affiliations recovered: {len(normalized_dois) - len(missing)}")
        print(f"Trying Crossref for {len(missing)} unresolved DOI(s)...")
        for index, doi in enumerate(missing, start=1):
            candidate = crossref_lookup(session, doi)
            results[doi] = merge_result(results[doi], candidate)
            if index % 25 == 0:
                print(f"  Crossref {index}/{len(missing)}")
            time.sleep(0.06)

        missing = [
            doi for doi in normalized_dois
            if not results[doi]["Affiliations"]
        ]
        openalex_key = os.environ.get("OPENALEX_API_KEY", "").strip()
        if openalex_key and missing:
            print(f"Trying OpenAlex for {len(missing)} unresolved DOI(s)...")
            oa_results = openalex_batch_lookup(session, missing, openalex_key)
            for doi, candidate in oa_results.items():
                results[doi] = merge_result(results[doi], candidate)
        elif missing:
            print(
                "OPENALEX_API_KEY is not set; skipping OpenAlex. "
                "A free key can improve recovery."
            )

        missing = [
            doi for doi in normalized_dois
            if not results[doi]["Affiliations"]
        ]
        ieee_key = os.environ.get("IEEE_API_KEY", "").strip()
        if ieee_key and missing:
            print(f"Trying IEEE Xplore API for {len(missing)} unresolved DOI(s)...")
            for index, doi in enumerate(missing, start=1):
                candidate = ieee_lookup(session, doi, ieee_key)
                results[doi] = merge_result(results[doi], candidate)
                if index % 25 == 0:
                    print(f"  IEEE {index}/{len(missing)}")
                time.sleep(0.12)
        elif missing:
            print("IEEE_API_KEY is not set; skipping IEEE Xplore API.")

    rows: list[dict[str, Any]] = []
    for index, doi in enumerate(normalized_dois, start=1):
        row = {"S.No.": index, **results[doi]}
        if not row["Affiliations"]:
            row["Status"] = (
                row["Status"]
                if row["Status"] and row["Status"] != "Not recovered"
                else "Not recovered"
            )
            row["Notes"] = (
                "Do not infer affiliation/country from author names. "
                "Verify using the article first page, Scopus, or IEEE Xplore."
            )
        rows.append(row)

    frame = pd.DataFrame(rows)
    recovered = frame["Affiliations"].fillna("").str.strip().ne("").sum()

    xlsx_path = output_dir / "Affiliations_175_DOIs.xlsx"
    csv_path = output_dir / "Affiliations_175_DOIs.csv"
    log_path = output_dir / "Affiliation_Source_Scan_Log.csv"

    frame.to_csv(csv_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(scan_log).to_csv(log_path, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="Affiliations", index=False)
        unresolved = frame[
            frame["Affiliations"].fillna("").str.strip().eq("")
        ]
        unresolved.to_excel(writer, sheet_name="Unrecovered", index=False)
        pd.DataFrame(scan_log).to_excel(
            writer, sheet_name="Source_Log", index=False
        )
        summary = pd.DataFrame([
            ["Requested DOIs", len(frame)],
            ["Affiliations recovered", int(recovered)],
            ["Not recovered", int(len(frame) - recovered)],
            ["Project root", str(project_root)],
            ["Generated at", pd.Timestamp.now().isoformat()],
            [
                "Rule",
                "Affiliations and countries are never inferred from author names."
            ],
        ], columns=["Item", "Value"])
        summary.to_excel(writer, sheet_name="Summary", index=False)

    format_workbook(xlsx_path)

    print("\nCompleted")
    print(f"Requested DOIs: {len(frame)}")
    print(f"Affiliations recovered: {recovered}")
    print(f"Not recovered: {len(frame) - recovered}")
    print(f"Excel: {xlsx_path}")
    print(f"CSV:   {csv_path}")
    print(f"Log:   {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
