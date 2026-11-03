# =============================================================================
# BEGINNER STEP 1
# THEMATIC ANALYSIS INPUT AND KEYWORD AUDIT
# =============================================================================


# -----------------------------------------------------------------------------
# 1. INSTALL AND LOAD REQUIRED PACKAGES
# -----------------------------------------------------------------------------

required_packages <- c(
  "dplyr",
  "tidyr",
  "stringr",
  "readr",
  "readxl",
  "writexl",
  "tibble"
)

missing_packages <- required_packages[
  !required_packages %in% rownames(
    installed.packages()
  )
]

if (length(missing_packages) > 0) {
  
  install.packages(
    missing_packages,
    repos = "https://cloud.r-project.org",
    dependencies = TRUE
  )
}

suppressPackageStartupMessages({
  
  library(dplyr)
  library(tidyr)
  library(stringr)
  library(readr)
  library(readxl)
  library(writexl)
  library(tibble)
})


# -----------------------------------------------------------------------------
# 2. SELECT THE MAIN PROJECT FOLDER
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 2. SET THE MAIN PROJECT FOLDER
# -----------------------------------------------------------------------------

PROJECT_ROOT <- normalizePath(
  "E:/Supreet Singh/SLR/Stock_Price_Prediction_SLR_ACME",
  winslash = "/",
  mustWork = TRUE
)

cat(
  "\nSelected project folder:\n",
  PROJECT_ROOT,
  "\n",
  sep = ""
)

cat(
  "\nSelected project folder:\n",
  PROJECT_ROOT,
  "\n",
  sep = ""
)


# -----------------------------------------------------------------------------
# 3. CREATE THE OUTPUT FOLDER
# -----------------------------------------------------------------------------

THEMATIC_DIR <- file.path(
  PROJECT_ROOT,
  "12_Bibliometrix_Output",
  "01_Thematic_Map_Evolution"
)

dir.create(
  THEMATIC_DIR,
  recursive = TRUE,
  showWarnings = FALSE
)

cat(
  "\nThematic-analysis output folder:\n",
  THEMATIC_DIR,
  "\n",
  sep = ""
)

cat(
  "\nOutput folder successfully created:",
  dir.exists(THEMATIC_DIR),
  "\n"
)


# -----------------------------------------------------------------------------
# 4. SELECT THE FINAL MERGED AND DEDUPLICATED DATASET
# -----------------------------------------------------------------------------

message(
  paste0(
    "\nSelect the FINAL MERGED AND DEDUPLICATED dataset ",
    "containing approximately 5,022 records."
  )
)

INPUT_FILE <- file.choose()

cat(
  "\nSelected input file:\n",
  INPUT_FILE,
  "\n",
  sep = ""
)


# -----------------------------------------------------------------------------
# 5. LOAD THE SELECTED FILE
# -----------------------------------------------------------------------------

file_extension <- tolower(
  tools::file_ext(
    INPUT_FILE
  )
)

if (file_extension == "csv") {
  
  M <- readr::read_csv(
    INPUT_FILE,
    show_col_types = FALSE,
    progress = FALSE,
    guess_max = 100000
  )
  
} else if (
  file_extension %in% c(
    "xlsx",
    "xls"
  )
) {
  
  M <- readxl::read_excel(
    INPUT_FILE
  )
  
} else if (
  file_extension == "rds"
) {
  
  M <- readRDS(
    INPUT_FILE
  )
  
} else {
  
  stop(
    paste0(
      "Unsupported file type: .",
      file_extension,
      "\nPlease select a CSV, XLSX, XLS, or RDS file."
    )
  )
}

M <- as.data.frame(
  M,
  stringsAsFactors = FALSE
)

names(M) <- trimws(
  names(M)
)

# -----------------------------------------------------------------------------
# CONVERT READABLE COLUMN NAMES TO BIBLIOMETRIX FIELD CODES
# -----------------------------------------------------------------------------

column_name_map <- c(
  "Authors" = "AU",
  "Title" = "TI",
  "Year" = "PY",
  "Source title" = "SO",
  "Cited by" = "TC",
  "DOI" = "DI",
  "Abstract" = "AB",
  "Author Keywords" = "DE",
  "Index Keywords" = "ID"
)

for (original_name in names(column_name_map)) {
  
  if (original_name %in% names(M)) {
    
    names(M)[
      names(M) == original_name
    ] <- column_name_map[[original_name]]
  }
}


# Create a merged keyword field from author and index keywords.
if (
  "DE" %in% names(M) &&
  "ID" %in% names(M)
) {
  
  author_keywords <- ifelse(
    is.na(M$DE),
    "",
    as.character(M$DE)
  )
  
  index_keywords <- ifelse(
    is.na(M$ID),
    "",
    as.character(M$ID)
  )
  
  M$KW_Merged <- paste(
    author_keywords,
    index_keywords,
    sep = "; "
  )
  
  M$KW_Merged <- gsub(
    "^;\\s*|;\\s*$",
    "",
    M$KW_Merged
  )
  
  M$KW_Merged <- gsub(
    ";\\s*;",
    ";",
    M$KW_Merged
  )
  
  M$KW_Merged <- trimws(
    M$KW_Merged
  )
}


cat(
  "\nColumn names after Bibliometrix conversion:\n"
)

print(
  names(M)
)


# -----------------------------------------------------------------------------
# 6. DISPLAY BASIC DATASET INFORMATION
# -----------------------------------------------------------------------------

cat(
  "\n",
  strrep(
    "=",
    100
  ),
  "\n",
  sep = ""
)

cat(
  "DATASET SUCCESSFULLY LOADED\n"
)

cat(
  strrep(
    "=",
    100
  ),
  "\n",
  sep = ""
)

cat(
  "Number of records:",
  nrow(M),
  "\n"
)

cat(
  "Number of columns:",
  ncol(M),
  "\n"
)

cat(
  "\nAvailable column names:\n"
)

print(
  names(M)
)


# -----------------------------------------------------------------------------
# 7. CHECK REQUIRED BIBLIOMETRIC FIELDS
# -----------------------------------------------------------------------------

required_fields <- c(
  "PY",
  "TI",
  "AU"
)

missing_required_fields <- setdiff(
  required_fields,
  names(M)
)

if (length(missing_required_fields) > 0) {
  
  stop(
    paste0(
      "\nRequired columns are missing: ",
      paste(
        missing_required_fields,
        collapse = ", "
      ),
      "\n\nThe selected file may not be the final ",
      "Bibliometrix-compatible merged dataset."
    )
  )
}


keyword_fields <- intersect(
  c(
    "DE",
    "ID",
    "KW_Merged"
  ),
  names(M)
)

if (length(keyword_fields) == 0) {
  
  stop(
    paste0(
      "\nNo keyword field was found.\n",
      "The dataset should contain at least one of:\n",
      "DE, ID, or KW_Merged."
    )
  )
}


# -----------------------------------------------------------------------------
# 8. CLEAN THE PUBLICATION YEAR
# -----------------------------------------------------------------------------

M$PY <- suppressWarnings(
  as.integer(
    as.character(
      M$PY
    )
  )
)

valid_year_rows <- (
  !is.na(M$PY) &
    M$PY >= 1900 &
    M$PY <= 2026
)

M_valid <- M[
  valid_year_rows,
  ,
  drop = FALSE
]


cat(
  "\nRecords with valid publication years:",
  nrow(M_valid),
  "\n"
)

cat(
  "Publication-year range:",
  min(
    M_valid$PY,
    na.rm = TRUE
  ),
  "-",
  max(
    M_valid$PY,
    na.rm = TRUE
  ),
  "\n"
)

cat(
  "Records published in 2026:",
  sum(
    M_valid$PY == 2026,
    na.rm = TRUE
  ),
  "\n"
)


# -----------------------------------------------------------------------------
# 9. KEYWORD COVERAGE
# -----------------------------------------------------------------------------

has_value <- function(x) {
  
  !is.na(x) &
    nzchar(
      trimws(
        as.character(x)
      )
    )
}


coverage_rows <- list()

for (field_name in c(
  "DE",
  "ID",
  "KW_Merged"
)) {
  
  if (field_name %in% names(M_valid)) {
    
    records_with_values <- sum(
      has_value(
        M_valid[[field_name]])
    )
    
    coverage_rows[[field_name]]<- tibble(
      Field = field_name,
      Available = TRUE,
      Records_with_Values = records_with_values,
      Coverage_Percentage = round(
        100 *
          records_with_values /
          nrow(M_valid),
        2
      )
    )
    
  } else {
    
    coverage_rows[[field_name]] <- tibble(
      Field = field_name,
      Available = FALSE,
      Records_with_Values = 0,
      Coverage_Percentage = 0
    )
  }
}

keyword_coverage <- bind_rows(
  coverage_rows
)


# -----------------------------------------------------------------------------
# 10. PUBLICATION COUNTS FOR THEMATIC-EVOLUTION PERIODS
# -----------------------------------------------------------------------------

M_until_2025 <- M_valid %>%
  filter(
    PY <= 2025
  ) %>%
  mutate(
    Period = case_when(
      PY <= 2005 ~ "1985-2005",
      PY <= 2015 ~ "2006-2015",
      PY <= 2020 ~ "2016-2020",
      PY <= 2025 ~ "2021-2025",
      TRUE ~ NA_character_
    )
  )


period_counts <- M_until_2025 %>%
  filter(
    !is.na(Period)
  ) %>%
  group_by(
    Period
  ) %>%
  summarise(
    Documents = n(),
    Percentage = round(
      100 *
        n() /
        nrow(M_until_2025),
      2
    ),
    .groups = "drop"
  )


# -----------------------------------------------------------------------------
# 11. EXTRACT THE TOP AUTHOR KEYWORDS
# -----------------------------------------------------------------------------

if ("DE" %in% names(M_valid)) {
  
  top_author_keywords <- tibble(
    Keywords = as.character(
      M_valid$DE
    )
  ) %>%
    mutate(
      Keywords = ifelse(
        is.na(Keywords),
        "",
        Keywords
      )
    ) %>%
    separate_rows(
      Keywords,
      sep = ";"
    ) %>%
    mutate(
      Keyword = str_to_lower(
        str_squish(
          Keywords
        )
      )
    ) %>%
    filter(
      Keyword != ""
    ) %>%
    count(
      Keyword,
      name = "Frequency",
      sort = TRUE
    ) %>%
    slice_head(
      n = 100
    )
  
} else {
  
  top_author_keywords <- tibble(
    Keyword = character(),
    Frequency = integer()
  )
}


# -----------------------------------------------------------------------------
# 12. SAVE THE AUDITED INPUT
# -----------------------------------------------------------------------------

AUDITED_RDS <- file.path(
  THEMATIC_DIR,
  "Thematic_Analysis_Audited_Input.rds"
)

saveRDS(
  M_valid,
  AUDITED_RDS
)


# -----------------------------------------------------------------------------
# 13. SAVE THE EXCEL AUDIT
# -----------------------------------------------------------------------------

AUDIT_WORKBOOK <- file.path(
  THEMATIC_DIR,
  "Thematic_Analysis_Input_Keyword_Audit.xlsx"
)

writexl::write_xlsx(
  list(
    Keyword_Coverage = keyword_coverage,
    Period_Counts = period_counts,
    Top_Author_Keywords = top_author_keywords
  ),
  path = AUDIT_WORKBOOK
)


# -----------------------------------------------------------------------------
# 14. FINAL CONSOLE OUTPUT
# -----------------------------------------------------------------------------

cat(
  "\n",
  strrep(
    "=",
    100
  ),
  "\n",
  sep = ""
)

cat(
  "THEMATIC ANALYSIS INPUT AUDIT COMPLETED\n"
)

cat(
  strrep(
    "=",
    100
  ),
  "\n",
  sep = ""
)


cat(
  "\nKEYWORD COVERAGE\n"
)

print(
  keyword_coverage
)


cat(
  "\nTHEMATIC-EVOLUTION PERIOD COUNTS\n"
)

print(
  period_counts
)


cat(
  "\nTOP 40 AUTHOR KEYWORDS\n"
)

print(
  top_author_keywords %>%
    slice_head(
      n = 40
    ),
  n = 40
)


cat(
  "\nAudited RDS file:\n",
  AUDITED_RDS,
  "\n",
  sep = ""
)


cat(
  "\nAudit workbook:\n",
  AUDIT_WORKBOOK,
  "\n",
  sep = ""
)


cat(
  "\nFINAL STATUS: SUCCESS\n"
)