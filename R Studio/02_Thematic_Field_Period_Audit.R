# =============================================================================
# THEMATIC FIELD-INTEGRITY AND PERIOD-BALANCE AUDIT
#
# This script:
# 1. Compares DE and ID keyword fields.
# 2. Checks whether the fields were duplicated.
# 3. Compares their top terms.
# 4. identifies suspicious generic terms.
# 5. calculates data-balanced thematic-evolution periods.
# 6. creates an Excel audit workbook.
# =============================================================================


# -----------------------------------------------------------------------------
# 1. LOAD REQUIRED PACKAGES
# -----------------------------------------------------------------------------

required_packages <- c(
  "dplyr",
  "tidyr",
  "stringr",
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
  library(writexl)
  library(tibble)
})


# -----------------------------------------------------------------------------
# 2. PROJECT PATHS
# -----------------------------------------------------------------------------

PROJECT_ROOT <- normalizePath(
  "E:/Supreet Singh/SLR/Stock_Price_Prediction_SLR_ACME",
  winslash = "/",
  mustWork = TRUE
)

THEMATIC_DIR <- file.path(
  PROJECT_ROOT,
  "12_Bibliometrix_Output",
  "01_Thematic_Map_Evolution"
)

INPUT_RDS <- file.path(
  THEMATIC_DIR,
  "Thematic_Analysis_Audited_Input.rds"
)

OUTPUT_WORKBOOK <- file.path(
  THEMATIC_DIR,
  "Thematic_Field_Integrity_and_Period_Audit.xlsx"
)

OUTPUT_REPORT <- file.path(
  THEMATIC_DIR,
  "Thematic_Field_Integrity_and_Period_Audit.txt"
)

if (!file.exists(INPUT_RDS)) {
  
  stop(
    paste0(
      "Audited RDS input was not found:\n",
      INPUT_RDS
    )
  )
}


# -----------------------------------------------------------------------------
# 3. READ THE AUDITED DATASET
# -----------------------------------------------------------------------------

M <- readRDS(
  INPUT_RDS
)

M <- as.data.frame(
  M,
  stringsAsFactors = FALSE
)

if (!all(c(
  "PY",
  "DE",
  "ID"
) %in% names(M))) {
  
  stop(
    paste0(
      "The dataset must contain PY, DE, and ID.\n",
      "Available columns:\n",
      paste(
        names(M),
        collapse = ", "
      )
    )
  )
}

M$PY <- suppressWarnings(
  as.integer(
    as.character(
      M$PY
    )
  )
)


# -----------------------------------------------------------------------------
# 4. KEYWORD-CLEANING FUNCTION
# -----------------------------------------------------------------------------

keyword_set <- function(value) {
  
  if (
    length(value) == 0 ||
    is.na(value) ||
    !nzchar(trimws(as.character(value)))
  ) {
    
    return(
      character(0)
    )
  }
  
  terms <- unlist(
    strsplit(
      as.character(value),
      split = ";",
      fixed = TRUE
    )
  )
  
  terms <- terms %>%
    str_to_lower() %>%
    str_replace_all(
      "&",
      " and "
    ) %>%
    str_replace_all(
      "[–—]",
      "-"
    ) %>%
    str_replace_all(
      "[^a-z0-9+ -]",
      " "
    ) %>%
    str_squish()
  
  terms <- terms[
    terms != ""
  ]
  
  sort(
    unique(
      terms
    )
  )
}


DE_sets <- lapply(
  M$DE,
  keyword_set
)

ID_sets <- lapply(
  M$ID,
  keyword_set
)


# -----------------------------------------------------------------------------
# 5. ROW-LEVEL DE–ID COMPARISON
# -----------------------------------------------------------------------------

jaccard_similarity <- function(
    first_set,
    second_set
) {
  
  union_terms <- union(
    first_set,
    second_set
  )
  
  if (length(union_terms) == 0) {
    return(NA_real_)
  }
  
  length(
    intersect(
      first_set,
      second_set
    )
  ) / length(
    union_terms
  )
}


exact_equal <- mapply(
  function(first_set, second_set) {
    
    identical(
      first_set,
      second_set
    )
  },
  DE_sets,
  ID_sets
)


jaccard_values <- mapply(
  jaccard_similarity,
  DE_sets,
  ID_sets
)


DE_nonempty <- lengths(
  DE_sets
) > 0

ID_nonempty <- lengths(
  ID_sets
) > 0

both_nonempty <- (
  DE_nonempty &
    ID_nonempty
)


both_nonempty_count <- sum(
  both_nonempty
)

exact_equal_both_count <- sum(
  exact_equal &
    both_nonempty
)

exact_equal_percentage <- round(
  100 *
    exact_equal_both_count /
    both_nonempty_count,
  2
)

median_jaccard <- round(
  median(
    jaccard_values[
      both_nonempty
    ],
    na.rm = TRUE
  ),
  4
)

mean_jaccard <- round(
  mean(
    jaccard_values[
      both_nonempty
    ],
    na.rm = TRUE
  ),
  4
)

high_similarity_percentage <- round(
  100 *
    mean(
      jaccard_values[
        both_nonempty
      ] >= 0.90,
      na.rm = TRUE
    ),
  2
)


field_comparison_summary <- tibble(
  Metric = c(
    "Total records",
    "Records with non-empty DE",
    "Records with non-empty ID",
    "Records with both DE and ID",
    "Rows with exactly equal DE and ID sets",
    "Exact-equality percentage among non-empty pairs",
    "Mean DE–ID Jaccard similarity",
    "Median DE–ID Jaccard similarity",
    "Rows with Jaccard similarity at least 0.90"
  ),
  Value = as.character(
    c(
      nrow(M),
      sum(DE_nonempty),
      sum(ID_nonempty),
      both_nonempty_count,
      exact_equal_both_count,
      exact_equal_percentage,
      mean_jaccard,
      median_jaccard,
      high_similarity_percentage
    )
  )
)


# -----------------------------------------------------------------------------
# 6. KEYWORD-FREQUENCY FUNCTION
# -----------------------------------------------------------------------------

keyword_frequency <- function(values) {
  
  tibble(
    Raw_Keywords = ifelse(
      is.na(values),
      "",
      as.character(values)
    )
  ) %>%
    separate_rows(
      Raw_Keywords,
      sep = ";"
    ) %>%
    mutate(
      Keyword = Raw_Keywords %>%
        str_to_lower() %>%
        str_replace_all(
          "&",
          " and "
        ) %>%
        str_replace_all(
          "[–—]",
          "-"
        ) %>%
        str_replace_all(
          "[^a-z0-9+ -]",
          " "
        ) %>%
        str_squish()
    ) %>%
    filter(
      Keyword != ""
    ) %>%
    count(
      Keyword,
      name = "Frequency",
      sort = TRUE
    )
}


DE_frequency <- keyword_frequency(
  M$DE
)

ID_frequency <- keyword_frequency(
  M$ID
)


top_100_DE <- head(
  DE_frequency$Keyword,
  100
)

top_100_ID <- head(
  ID_frequency$Keyword,
  100
)

top_100_overlap <- intersect(
  top_100_DE,
  top_100_ID
)


top_term_overlap_summary <- tibble(
  Metric = c(
    "Top-100 DE terms",
    "Top-100 ID terms",
    "Terms appearing in both top-100 lists",
    "Top-100 overlap percentage"
  ),
  Value = c(
    length(top_100_DE),
    length(top_100_ID),
    length(top_100_overlap),
    round(
      100 *
        length(top_100_overlap) /
        100,
      2
    )
  )
)


# -----------------------------------------------------------------------------
# 7. SUSPICIOUS GENERIC TERMS
# -----------------------------------------------------------------------------

terms_for_review <- c(
  "commerce",
  "costs",
  "investments",
  "decision making",
  "brain",
  "performance",
  "prediction accuracy",
  "financial markets",
  "forecasting",
  "electronic trading"
)


generic_term_review <- tibble(
  Keyword = terms_for_review
) %>%
  left_join(
    DE_frequency %>%
      rename(
        DE_Frequency = Frequency
      ),
    by = "Keyword"
  ) %>%
  left_join(
    ID_frequency %>%
      rename(
        ID_Frequency = Frequency
      ),
    by = "Keyword"
  ) %>%
  mutate(
    DE_Frequency = replace_na(
      DE_Frequency,
      0L
    ),
    ID_Frequency = replace_na(
      ID_Frequency,
      0L
    )
  )


# -----------------------------------------------------------------------------
# 8. CURRENT PERIOD COUNTS
# -----------------------------------------------------------------------------

M_complete <- M %>%
  filter(
    !is.na(PY),
    PY <= 2025
  )


current_period_counts <- M_complete %>%
  mutate(
    Period = case_when(
      PY <= 2005 ~ "1985-2005",
      PY <= 2015 ~ "2006-2015",
      PY <= 2020 ~ "2016-2020",
      PY <= 2025 ~ "2021-2025",
      TRUE ~ NA_character_
    )
  ) %>%
  filter(
    !is.na(Period)
  ) %>%
  count(
    Period,
    name = "Documents"
  ) %>%
  mutate(
    Percentage = round(
      100 *
        Documents /
        sum(Documents),
      2
    )
  )


# -----------------------------------------------------------------------------
# 9. CALCULATE DATA-BALANCED CUT YEARS
# -----------------------------------------------------------------------------

annual_counts <- M_complete %>%
  count(
    PY,
    name = "Documents"
  ) %>%
  arrange(
    PY
  ) %>%
  mutate(
    Cumulative_Documents = cumsum(
      Documents
    ),
    Cumulative_Percentage = round(
      100 *
        Cumulative_Documents /
        sum(Documents),
      2
    )
  )


target_counts <- c(
  0.25,
  0.50,
  0.75
) * nrow(
  M_complete
)


balanced_cut_years <- integer(
  0
)

previous_cut <- min(
  annual_counts$PY
) - 1

maximum_year <- max(
  annual_counts$PY
)


for (target_count in target_counts) {
  
  eligible_years <- annual_counts %>%
    filter(
      PY > previous_cut,
      PY < maximum_year
    )
  
  selected_index <- which.min(
    abs(
      eligible_years$Cumulative_Documents -
        target_count
    )
  )
  
  selected_year <- eligible_years$PY[
    selected_index
  ]
  
  balanced_cut_years <- c(
    balanced_cut_years,
    selected_year
  )
  
  previous_cut <- selected_year
}


minimum_year <- min(
  M_complete$PY
)

period_lower_bounds <- c(
  minimum_year,
  balanced_cut_years + 1
)

period_upper_bounds <- c(
  balanced_cut_years,
  maximum_year
)

balanced_period_labels <- paste0(
  period_lower_bounds,
  "-",
  period_upper_bounds
)


M_complete$Balanced_Period <- cut(
  M_complete$PY,
  breaks = c(
    minimum_year - 1,
    balanced_cut_years,
    maximum_year
  ),
  labels = balanced_period_labels,
  include.lowest = TRUE,
  right = TRUE
)


balanced_period_counts <- M_complete %>%
  count(
    Balanced_Period,
    name = "Documents"
  ) %>%
  mutate(
    Percentage = round(
      100 *
        Documents /
        sum(Documents),
      2
    )
  )


balanced_cutpoint_table <- tibble(
  Cut_Number = 1:3,
  Cut_Year = balanced_cut_years,
  Target_Cumulative_Percentage = c(
    25,
    50,
    75
  )
)


# -----------------------------------------------------------------------------
# 10. FIELD DECISION
# -----------------------------------------------------------------------------

field_decision <- if (
  exact_equal_percentage >= 90 ||
  median_jaccard >= 0.90
) {
  
  paste(
    "REVIEW REQUIRED:",
    "DE and ID appear substantially duplicated.",
    "Do not describe DE as an independent author-keyword field."
  )
  
} else {
  
  paste(
    "PASS:",
    "DE and ID are sufficiently distinct.",
    "DE may be retained as the primary thematic field."
  )
}


decision_table <- tibble(
  Item = c(
    "Field-integrity decision",
    "Current period decision",
    "Recommended next action"
  ),
  Decision = c(
    field_decision,
    paste(
      "Do not freeze the current periods because",
      "2021-2025 contains 72.60% of the complete-year corpus."
    ),
    paste(
      "Review the automatically calculated balanced periods",
      "before generating thematic evolution."
    )
  )
)


# -----------------------------------------------------------------------------
# 11. SAVE EXCEL WORKBOOK
# -----------------------------------------------------------------------------

write_xlsx(
  list(
    Field_Comparison = field_comparison_summary,
    Field_Decision = decision_table,
    Current_Periods = current_period_counts,
    Balanced_Cutpoints = balanced_cutpoint_table,
    Balanced_Periods = balanced_period_counts,
    Annual_Counts = annual_counts,
    Generic_Term_Review = generic_term_review,
    Top_100_Overlap = tibble(
      Keyword = top_100_overlap
    ),
    Top_DE_Keywords = head(
      DE_frequency,
      250
    ),
    Top_ID_Keywords = head(
      ID_frequency,
      250
    ),
    Row_Level_Comparison = tibble(
      Row_Number = seq_len(
        nrow(M)
      ),
      DE_Nonempty = DE_nonempty,
      ID_Nonempty = ID_nonempty,
      Exact_Set_Equality = exact_equal,
      Jaccard_Similarity = jaccard_values
    )
  ),
  path = OUTPUT_WORKBOOK
)


# -----------------------------------------------------------------------------
# 12. SAVE TEXT REPORT
# -----------------------------------------------------------------------------

report_lines <- c(
  "THEMATIC FIELD-INTEGRITY AND PERIOD-BALANCE AUDIT",
  strrep(
    "=",
    100
  ),
  "",
  capture.output(
    print(
      field_comparison_summary,
      n = Inf
    )
  ),
  "",
  "FIELD DECISION",
  field_decision,
  "",
  "CURRENT PERIOD COUNTS",
  capture.output(
    print(
      current_period_counts,
      n = Inf
    )
  ),
  "",
  "DATA-BALANCED CUT YEARS",
  paste(
    balanced_cut_years,
    collapse = ", "
  ),
  "",
  "DATA-BALANCED PERIOD COUNTS",
  capture.output(
    print(
      balanced_period_counts,
      n = Inf
    )
  ),
  "",
  "GENERIC TERM REVIEW",
  capture.output(
    print(
      generic_term_review,
      n = Inf
    )
  )
)

writeLines(
  report_lines,
  OUTPUT_REPORT
)


# -----------------------------------------------------------------------------
# 13. CONSOLE OUTPUT
# -----------------------------------------------------------------------------

cat(
  "\n",
  strrep(
    "=",
    110
  ),
  "\n",
  sep = ""
)

cat(
  "THEMATIC FIELD-INTEGRITY AND PERIOD-BALANCE AUDIT\n"
)

cat(
  strrep(
    "=",
    110
  ),
  "\n",
  sep = ""
)


cat(
  "\nFIELD COMPARISON\n"
)

print(
  field_comparison_summary,
  n = Inf
)


cat(
  "\nFIELD DECISION\n"
)

cat(
  field_decision,
  "\n"
)


cat(
  "\nTOP-100 TERM OVERLAP\n"
)

print(
  top_term_overlap_summary,
  n = Inf
)


cat(
  "\nCURRENT PERIOD COUNTS\n"
)

print(
  current_period_counts,
  n = Inf
)


cat(
  "\nAUTOMATICALLY CALCULATED BALANCED CUT YEARS\n"
)

print(
  balanced_cutpoint_table,
  n = Inf
)


cat(
  "\nBALANCED PERIOD COUNTS\n"
)

print(
  balanced_period_counts,
  n = Inf
)


cat(
  "\nGENERIC TERM REVIEW\n"
)

print(
  generic_term_review,
  n = Inf
)


cat(
  "\nAudit workbook:\n",
  OUTPUT_WORKBOOK,
  "\n",
  sep = ""
)

cat(
  "\nAudit report:\n",
  OUTPUT_REPORT,
  "\n",
  sep = ""
)

cat(
  "\nFINAL STATUS: AUDIT COMPLETED\n"
)

# =============================================================================
# REPAIR FINAL PRINTING AND COMPLETE THE AUDIT
#
# The calculations have already completed. This block safely prints standard
# data frames, rewrites the workbook, and creates the text report.
# =============================================================================


# -----------------------------------------------------------------------------
# 1. SAFE PRINTING FUNCTIONS
# -----------------------------------------------------------------------------

print_table <- function(data_object) {
  
  printable_object <- as.data.frame(
    data_object,
    stringsAsFactors = FALSE
  )
  
  print(
    printable_object,
    row.names = FALSE
  )
}


capture_table <- function(data_object) {
  
  capture.output(
    print_table(
      data_object
    )
  )
}


# -----------------------------------------------------------------------------
# 2. REWRITE THE AUDIT WORKBOOK
# -----------------------------------------------------------------------------

writexl::write_xlsx(
  list(
    Field_Comparison = as.data.frame(
      field_comparison_summary
    ),
    
    Field_Decision = as.data.frame(
      decision_table
    ),
    
    Current_Periods = as.data.frame(
      current_period_counts
    ),
    
    Balanced_Cutpoints = as.data.frame(
      balanced_cutpoint_table
    ),
    
    Balanced_Periods = as.data.frame(
      balanced_period_counts
    ),
    
    Annual_Counts = as.data.frame(
      annual_counts
    ),
    
    Generic_Term_Review = as.data.frame(
      generic_term_review
    ),
    
    Top_100_Overlap = data.frame(
      Keyword = top_100_overlap,
      stringsAsFactors = FALSE
    ),
    
    Top_DE_Keywords = as.data.frame(
      head(
        DE_frequency,
        250
      )
    ),
    
    Top_ID_Keywords = as.data.frame(
      head(
        ID_frequency,
        250
      )
    ),
    
    Row_Level_Comparison = data.frame(
      Row_Number = seq_len(
        nrow(M)
      ),
      DE_Nonempty = DE_nonempty,
      ID_Nonempty = ID_nonempty,
      Exact_Set_Equality = exact_equal,
      Jaccard_Similarity = jaccard_values
    )
  ),
  path = OUTPUT_WORKBOOK
)


# -----------------------------------------------------------------------------
# 3. REWRITE THE TEXT REPORT
# -----------------------------------------------------------------------------

report_lines <- c(
  "THEMATIC FIELD-INTEGRITY AND PERIOD-BALANCE AUDIT",
  strrep(
    "=",
    100
  ),
  "",
  "FIELD COMPARISON",
  capture_table(
    field_comparison_summary
  ),
  "",
  "FIELD DECISION",
  field_decision,
  "",
  "TOP-100 TERM OVERLAP",
  capture_table(
    top_term_overlap_summary
  ),
  "",
  "CURRENT PERIOD COUNTS",
  capture_table(
    current_period_counts
  ),
  "",
  "AUTOMATICALLY CALCULATED BALANCED CUT YEARS",
  capture_table(
    balanced_cutpoint_table
  ),
  "",
  "BALANCED PERIOD COUNTS",
  capture_table(
    balanced_period_counts
  ),
  "",
  "GENERIC TERM REVIEW",
  capture_table(
    generic_term_review
  )
)

writeLines(
  report_lines,
  con = OUTPUT_REPORT,
  useBytes = TRUE
)


# -----------------------------------------------------------------------------
# 4. FINAL CONSOLE OUTPUT
# -----------------------------------------------------------------------------

cat(
  "\n",
  strrep(
    "=",
    110
  ),
  "\n",
  sep = ""
)

cat(
  "THEMATIC FIELD-INTEGRITY AND PERIOD-BALANCE AUDIT\n"
)

cat(
  strrep(
    "=",
    110
  ),
  "\n",
  sep = ""
)


cat(
  "\nFIELD COMPARISON\n"
)

print_table(
  field_comparison_summary
)


cat(
  "\nFIELD DECISION\n"
)

cat(
  field_decision,
  "\n"
)


cat(
  "\nTOP-100 TERM OVERLAP\n"
)

print_table(
  top_term_overlap_summary
)


cat(
  "\nCURRENT PERIOD COUNTS\n"
)

print_table(
  current_period_counts
)


cat(
  "\nAUTOMATICALLY CALCULATED BALANCED CUT YEARS\n"
)

print_table(
  balanced_cutpoint_table
)


cat(
  "\nBALANCED PERIOD COUNTS\n"
)

print_table(
  balanced_period_counts
)


cat(
  "\nGENERIC TERM REVIEW\n"
)

print_table(
  generic_term_review
)


cat(
  "\nAudit workbook:\n",
  OUTPUT_WORKBOOK,
  "\n",
  sep = ""
)

cat(
  "\nAudit report:\n",
  OUTPUT_REPORT,
  "\n",
  sep = ""
)

cat(
  "\nFINAL STATUS: AUDIT COMPLETED SUCCESSFULLY\n"
)

cat("\nFIELD COMPARISON\n")
print(as.data.frame(field_comparison_summary), row.names = FALSE)

cat("\nFIELD DECISION\n")
cat(field_decision, "\n")

cat("\nTOP-100 TERM OVERLAP\n")
print(as.data.frame(top_term_overlap_summary), row.names = FALSE)

cat("\nBALANCED CUT YEARS\n")
print(as.data.frame(balanced_cutpoint_table), row.names = FALSE)

cat("\nBALANCED PERIOD COUNTS\n")
print(as.data.frame(balanced_period_counts), row.names = FALSE)

cat("\nGENERIC TERM REVIEW\n")
print(as.data.frame(generic_term_review), row.names = FALSE)

cat("\nFINAL STATUS: RESULTS PRINTED SUCCESSFULLY\n")
