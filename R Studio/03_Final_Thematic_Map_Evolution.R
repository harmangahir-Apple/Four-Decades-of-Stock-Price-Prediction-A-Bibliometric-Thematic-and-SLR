# =============================================================================
# FINAL THEMATIC MAP AND THEMATIC EVOLUTION
#
# Primary field:
#   One normalized source-keyword field derived from DE.
#
# Important:
#   DE and ID were found to be exact duplicates. They are therefore not
#   concatenated. KW_Merged is overwritten with one cleaned copy of DE.
#
# Primary analytical period:
#   Complete publication years through 2025.
#
# Thematic evolution periods:
#   1987-2005
#   2006-2015
#   2016-2020
#   2021-2022
#   2023-2024
#   2025
# =============================================================================


# =============================================================================
# 1. INSTALL AND LOAD PACKAGES
# =============================================================================

required_packages <- c(
  "bibliometrix",
  "dplyr",
  "stringr",
  "tibble",
  "writexl",
  "ggplot2",
  "htmlwidgets"
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
  
  library(bibliometrix)
  library(dplyr)
  library(stringr)
  library(tibble)
  library(writexl)
  library(ggplot2)
  library(htmlwidgets)
})


# =============================================================================
# 2. PROJECT PATHS
# =============================================================================

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

dir.create(
  THEMATIC_DIR,
  recursive = TRUE,
  showWarnings = FALSE
)

INPUT_RDS <- file.path(
  THEMATIC_DIR,
  "Thematic_Analysis_Audited_Input.rds"
)

CLEANED_RDS <- file.path(
  THEMATIC_DIR,
  "Thematic_Analysis_Cleaned_Keywords_Through_2025.rds"
)

THEMATIC_MAP_RDS <- file.path(
  THEMATIC_DIR,
  "Thematic_Map_Final_Object.rds"
)

THEMATIC_EVOLUTION_RDS <- file.path(
  THEMATIC_DIR,
  "Thematic_Evolution_Final_Object.rds"
)

AUDIT_WORKBOOK <- file.path(
  THEMATIC_DIR,
  "Thematic_Map_Evolution_Final_Audit.xlsx"
)

MAP_PNG <- file.path(
  THEMATIC_DIR,
  "Fig_Thematic_Map_Final.png"
)

MAP_PDF <- file.path(
  THEMATIC_DIR,
  "Fig_Thematic_Map_Final.pdf"
)

EVOLUTION_HTML <- file.path(
  THEMATIC_DIR,
  "Fig_Thematic_Evolution_Final.html"
)

SETTINGS_FILE <- file.path(
  THEMATIC_DIR,
  "Thematic_Map_Evolution_Settings_Final.txt"
)


if (!file.exists(INPUT_RDS)) {
  
  stop(
    paste0(
      "Audited RDS input was not found:\n",
      INPUT_RDS
    )
  )
}


# =============================================================================
# 3. LOAD THE AUDITED DATASET
# =============================================================================

M <- readRDS(
  INPUT_RDS
)

M <- as.data.frame(
  M,
  stringsAsFactors = FALSE
)

required_fields <- c(
  "PY",
  "DE",
  "ID"
)

missing_fields <- setdiff(
  required_fields,
  names(M)
)

if (length(missing_fields) > 0) {
  
  stop(
    paste0(
      "Required fields are missing: ",
      paste(
        missing_fields,
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
  "FINAL THEMATIC ANALYSIS INPUT\n"
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
  "Valid-year records loaded:",
  nrow(M),
  "\n"
)

cat(
  "Publication-year range:",
  min(
    M$PY,
    na.rm = TRUE
  ),
  "-",
  max(
    M$PY,
    na.rm = TRUE
  ),
  "\n"
)


# =============================================================================
# 4. SYNONYM NORMALIZATION
#
# All names on the left are normalized input variants.
# Values on the right are the canonical forms used in the analysis.
# =============================================================================

synonym_map <- c(
  
  "machine learning" =
    "machine learning",
  
  "deep learning" =
    "deep learning",
  
  "artificial intelligence" =
    "artificial intelligence",
  
  "ai" =
    "artificial intelligence",
  
  "lstm" =
    "long short-term memory",
  
  "long short term memory" =
    "long short-term memory",
  
  "short term memory" =
    "long short-term memory",
  
  "support vector machine" =
    "support vector machine",
  
  "support vector machines" =
    "support vector machine",
  
  "svm" =
    "support vector machine",
  
  "artificial neural network" =
    "artificial neural networks",
  
  "artificial neural networks" =
    "artificial neural networks",
  
  "neural network" =
    "artificial neural networks",
  
  "neural networks" =
    "artificial neural networks",
  
  "ann" =
    "artificial neural networks",
  
  "deep neural network" =
    "deep neural network",
  
  "deep neural networks" =
    "deep neural network",
  
  "convolutional neural network" =
    "convolutional neural network",
  
  "convolutional neural networks" =
    "convolutional neural network",
  
  "cnn" =
    "convolutional neural network",
  
  "recurrent neural network" =
    "recurrent neural network",
  
  "recurrent neural networks" =
    "recurrent neural network",
  
  "rnn" =
    "recurrent neural network",
  
  "gated recurrent unit" =
    "gated recurrent unit",
  
  "gated recurrent units" =
    "gated recurrent unit",
  
  "gru" =
    "gated recurrent unit",
  
  "random forest" =
    "random forest",
  
  "random forests" =
    "random forest",
  
  "genetic algorithm" =
    "genetic algorithm",
  
  "genetic algorithms" =
    "genetic algorithm",
  
  "technical indicator" =
    "technical indicators",
  
  "technical indicators" =
    "technical indicators",
  
  "sentiment analyses" =
    "sentiment analysis",
  
  "sentiment analysis" =
    "sentiment analysis",
  
  "natural language processing" =
    "natural language processing",
  
  "nlp" =
    "natural language processing",
  
  "transformers" =
    "transformer",
  
  "transformer" =
    "transformer",
  
  "attention mechanisms" =
    "attention mechanism",
  
  "attention mechanism" =
    "attention mechanism",
  
  "time series" =
    "time series",
  
  "time series analysis" =
    "time series analysis",
  
  "time series forecasting" =
    "time series forecasting",
  
  "timeseries forecasting" =
    "time series forecasting",
  
  "feature selections" =
    "feature selection",
  
  "feature selection" =
    "feature selection",
  
  "portfolio optimisation" =
    "portfolio optimization",
  
  "portfolio optimization" =
    "portfolio optimization",
  
  "hyperparameter optimisation" =
    "hyperparameter optimization",
  
  "hyper parameter optimization" =
    "hyperparameter optimization",
  
  "hyperparameter optimization" =
    "hyperparameter optimization",
  
  "optimisation" =
    "optimization",
  
  "optimization" =
    "optimization",
  
  "ensemble methods" =
    "ensemble learning",
  
  "ensemble method" =
    "ensemble learning",
  
  "ensemble models" =
    "ensemble learning",
  
  "ensemble model" =
    "ensemble learning",
  
  "ensemble learning" =
    "ensemble learning",
  
  "hybrid models" =
    "hybrid model",
  
  "hybrid model" =
    "hybrid model",
  
  "technical analyses" =
    "technical analysis",
  
  "technical analysis" =
    "technical analysis",
  
  "fundamental analyses" =
    "fundamental analysis",
  
  "fundamental analysis" =
    "fundamental analysis",
  
  "data-mining" =
    "data mining",
  
  "data mining" =
    "data mining",
  
  "wavelet transforms" =
    "wavelet transform",
  
  "wavelet transform" =
    "wavelet transform",
  
  "extreme learning machines" =
    "extreme learning machine",
  
  "extreme learning machine" =
    "extreme learning machine",
  
  "elm" =
    "extreme learning machine",
  
  "principal component analysis" =
    "principal component analysis",
  
  "pca" =
    "principal component analysis",
  
  "autoregressive integrated moving average" =
    "autoregressive integrated moving average",
  
  "arima" =
    "autoregressive integrated moving average",
  
  "generalized autoregressive conditional heteroskedasticity" =
    "generalized autoregressive conditional heteroskedasticity",
  
  "garch" =
    "generalized autoregressive conditional heteroskedasticity",
  
  "extreme gradient boosting" =
    "xgboost",
  
  "xgboost" =
    "xgboost",
  
  "light gradient boosting machine" =
    "lightgbm",
  
  "lightgbm" =
    "lightgbm",
  
  "meta heuristic" =
    "metaheuristic optimization",
  
  "meta heuristic algorithm" =
    "metaheuristic optimization",
  
  "meta heuristic algorithms" =
    "metaheuristic optimization",
  
  "metaheuristic" =
    "metaheuristic optimization",
  
  "metaheuristics" =
    "metaheuristic optimization",
  
  "metaheuristic algorithm" =
    "metaheuristic optimization",
  
  "metaheuristic algorithms" =
    "metaheuristic optimization",
  
  "explainable ai" =
    "explainable artificial intelligence",
  
  "xai" =
    "explainable artificial intelligence",
  
  "explainable artificial intelligence" =
    "explainable artificial intelligence"
)


# =============================================================================
# 5. NON-DISCRIMINATING OR GENERIC TERMS TO REMOVE
#
# These are either:
# - corpus-defining terms that occur throughout the complete dataset, or
# - generic indexing terms that do not identify a meaningful methodology.
# =============================================================================

remove_terms <- c(
  
  "stock",
  "stocks",
  "market",
  "markets",
  "price",
  "prices",
  
  "stock market",
  "stock markets",
  
  "stock price",
  "stock prices",
  
  "stock prediction",
  "stock predictions",
  
  "stock market prediction",
  "stock market forecasting",
  
  "stock price prediction",
  "stock price forecasting",
  
  "price prediction",
  "price forecasting",
  
  "market prediction",
  "market forecasting",
  
  "financial market",
  "financial markets",
  
  "finance",
  
  "prediction",
  "forecasting",
  
  "commerce",
  "costs",
  "investments",
  "decision making",
  "brain",
  "performance",
  "prediction accuracy",
  "electronic trading",
  
  "marketplace",
  "marketplaces"
)

# =============================================================================
# FINAL TARGETED REMOVAL OF GENERIC OR NON-DISCRIMINATING TERMS
# =============================================================================

remove_terms <- unique(
  c(
    remove_terms,
    
    "learning systems",
    "learning system",
    
    "learning algorithms",
    "learning algorithm",
    
    "prediction models",
    "prediction model",
    
    "predictive models",
    "predictive model",
    
    "prediction modelling",
    "prediction modeling",
    
    "predictive modelling",
    "predictive modeling",
    
    "financial forecasting",
    
    "market trends",
    "market trend",
    
    "market research",
    
    "stock exchange",
    "stock exchanges",
    
    "stock data",
    
    "data handling",
    
    "financial data processing",
    
    "mean square error",
    "mean squared error",
    
    "regression analysis",
    
    "predictive analytics",
    
    "stock price movements",
    "stock price movement"
  )
)


# Normalize social-network indexing terms into one substantive theme.
synonym_map["social networking online"] <- "social media"
synonym_map["social network"] <- "social media"
synonym_map["social networks"] <- "social media"
synonym_map["online social networks"] <- "social media"

# =============================================================================
# FINAL RESIDUAL KEYWORD NORMALIZATION
# =============================================================================

synonym_map["times series"] <-
  "time series"

synonym_map["long short term memory lstm"] <-
  "long short-term memory"

synonym_map["support vectors machine"] <-
  "support vector machine"

synonym_map["optimisations"] <-
  "optimization"

synonym_map["particle swarm optimization pso"] <-
  "particle swarm optimization"

synonym_map["machine learning models"] <-
  "machine learning"

synonym_map["machine learning algorithms"] <-
  "machine learning"

synonym_map["machine learning techniques"] <-
  "machine learning"

synonym_map["time series data"] <-
  "time series"

synonym_map["financial time series"] <-
  "time series"

synonym_map["time series prediction"] <-
  "time series forecasting"


remove_terms <- unique(
  c(
    remove_terms,
    "error",
    "errors",
    "stock market prices",
    "stock forecasting",
    "learning models",
    "memory modeling",
    "memory network",
    "classification of information",
    "convolution"
  )
)

# =============================================================================
# 6. KEYWORD CLEANING FUNCTION
# =============================================================================

clean_keyword_record <- function(value) {
  
  if (
    length(value) == 0 ||
    is.na(value) ||
    !nzchar(
      trimws(
        as.character(value)
      )
    )
  ) {
    
    return("")
  }
  
  
  terms <- unlist(
    strsplit(
      as.character(value),
      split = ";",
      fixed = TRUE
    ),
    use.names = FALSE
  )
  
  
  terms <- terms %>%
    str_to_lower() %>%
    str_replace_all(
      "&",
      " and "
    ) %>%
    str_replace_all(
      "[–—−]",
      "-"
    ) %>%
    str_replace_all(
      "[_/]",
      " "
    ) %>%
    str_replace_all(
      "[^a-z0-9+ -]",
      " "
    ) %>%
    str_replace_all(
      "-",
      " "
    ) %>%
    str_squish()
  
  
  terms <- terms[
    terms != ""
  ]
  
  
  mapped_terms <- terms %in% names(
    synonym_map
  )
  
  terms[
    mapped_terms
  ] <- unname(
    synonym_map[
      terms[
        mapped_terms
      ]
    ]
  )
  
  
  terms <- terms[
    !terms %in% remove_terms
  ]
  
  
  terms <- sort(
    unique(
      terms
    )
  )
  
  
  paste(
    terms,
    collapse = ";"
  )
}


# =============================================================================
# 7. CREATE ONE NORMALIZED KEYWORD FIELD
#
# DE and ID were exact duplicates, so only DE is used as the source.
# KW_Merged is the field name required by Bibliometrix.
# =============================================================================

M$KW_Original <- as.character(
  M$DE
)

M$KW_Merged <- vapply(
  M$KW_Original,
  clean_keyword_record,
  character(1)
)


# =============================================================================
# 8. RETAIN COMPLETE PUBLICATION YEARS THROUGH 2025
# =============================================================================

M_complete <- M %>%
  filter(
    !is.na(PY),
    PY <= 2025
  )


records_2026_excluded <- sum(
  M$PY == 2026,
  na.rm = TRUE
)

clean_keyword_records <- sum(
  nzchar(
    trimws(
      M_complete$KW_Merged
    )
  )
)


cat(
  "\nRecords retained through 2025:",
  nrow(M_complete),
  "\n"
)

cat(
  "Records from 2026 excluded:",
  records_2026_excluded,
  "\n"
)

cat(
  "Records with normalized keywords:",
  clean_keyword_records,
  "\n"
)


# =============================================================================
# 9. FINAL THEMATIC-EVOLUTION PERIODS
# =============================================================================

first_year <- min(
  M_complete$PY,
  na.rm = TRUE
)

first_period_label <- paste0(
  first_year,
  "-2005"
)


M_complete$Thematic_Period <- case_when(
  
  M_complete$PY <= 2005 ~
    first_period_label,
  
  M_complete$PY <= 2015 ~
    "2006-2015",
  
  M_complete$PY <= 2020 ~
    "2016-2020",
  
  M_complete$PY <= 2022 ~
    "2021-2022",
  
  M_complete$PY <= 2024 ~
    "2023-2024",
  
  M_complete$PY <= 2025 ~
    "2025",
  
  TRUE ~
    NA_character_
)


period_levels <- c(
  first_period_label,
  "2006-2015",
  "2016-2020",
  "2021-2022",
  "2023-2024",
  "2025"
)


period_counts <- M_complete %>%
  filter(
    !is.na(Thematic_Period)
  ) %>%
  mutate(
    Thematic_Period = factor(
      Thematic_Period,
      levels = period_levels
    )
  ) %>%
  count(
    Thematic_Period,
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


cat(
  "\nFINAL THEMATIC-EVOLUTION PERIOD COUNTS\n"
)

print(
  as.data.frame(
    period_counts
  ),
  row.names = FALSE
)


# =============================================================================
# 10. CLEANED KEYWORD FREQUENCIES
# =============================================================================

cleaned_keyword_frequency <- tibble(
  Keywords = M_complete$KW_Merged
) %>%
  tidyr::separate_rows(
    Keywords,
    sep = ";"
  ) %>%
  mutate(
    Keyword = str_squish(
      Keywords
    )
  ) %>%
  filter(
    Keyword != ""
  ) %>%
  count(
    Keyword,
    name = "Frequency",
    sort = TRUE
  )

# =============================================================================
# 10B. CREATE THE REQUIRED UNIQUE DOCUMENT IDENTIFIER
#
# Bibliometrix requires an SR field to identify each manuscript when
# constructing the document-keyword occurrence matrix.
# =============================================================================

M_complete <- as.data.frame(
  M_complete,
  stringsAsFactors = FALSE
)


# Create a stable, unique identifier for every retained document.
M_complete$SR <- sprintf(
  "DOC_%05d",
  seq_len(
    nrow(M_complete)
  )
)


# Retain an additional full-reference identifier for compatibility.
M_complete$SR_FULL <- M_complete$SR

# =============================================================================
# ADD DATABASE-SOURCE FIELD REQUIRED BY BIBLIOMETRIX
#
# The corpus combines records from multiple bibliographic databases.
# "MIXED" is therefore used rather than incorrectly assigning all records
# to Scopus or Web of Science.
# =============================================================================

M_complete$DB <- rep(
  "MIXED",
  nrow(M_complete)
)


if (
  length(M_complete$DB)
  != nrow(M_complete)
) {
  
  stop(
    "The DB field length differs from the number of documents."
  )
}


if (
  anyNA(M_complete$DB) ||
  any(
    !nzchar(
      trimws(
        M_complete$DB
      )
    )
  )
) {
  
  stop(
    "The DB field contains missing or empty values."
  )
}


cat(
  "DB identifiers:",
  length(M_complete$DB),
  "\n"
)

cat(
  "Database-source designation:",
  unique(M_complete$DB),
  "\n"
)

# Use the same identifiers as data-frame row names.
rownames(M_complete) <- M_complete$SR


# Validate the identifiers.
if (anyNA(M_complete$SR)) {
  
  stop(
    "Missing values were detected in the SR document identifiers."
  )
}


if (anyDuplicated(M_complete$SR) > 0) {
  
  stop(
    "Duplicate SR document identifiers were detected."
  )
}


if (
  length(M_complete$SR)
  != nrow(M_complete)
) {
  
  stop(
    "The number of SR identifiers differs from the number of documents."
  )
}


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
  "BIBLIOMETRIX DOCUMENT IDENTIFIER CHECK\n"
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
  "Documents:",
  nrow(M_complete),
  "\n"
)

cat(
  "SR identifiers:",
  length(M_complete$SR),
  "\n"
)

cat(
  "Unique SR identifiers:",
  length(
    unique(
      M_complete$SR
    )
  ),
  "\n"
)

cat(
  "First SR identifier:",
  M_complete$SR[1],
  "\n"
)

cat(
  "Last SR identifier:",
  M_complete$SR[
    nrow(M_complete)
  ],
  "\n"
)


# Test the document-keyword occurrence matrix before thematic mapping.
KEYWORD_MATRIX_TEST <- bibliometrix::cocMatrix(
  
  M_complete,
  
  Field = "KW_Merged",
  
  type = "sparse",
  
  n = 20,
  
  sep = ";"
)


if (
  nrow(KEYWORD_MATRIX_TEST)
  != nrow(M_complete)
) {
  
  stop(
    paste0(
      "Keyword matrix validation failed. Documents expected: ",
      nrow(M_complete),
      "; rows observed: ",
      nrow(KEYWORD_MATRIX_TEST)
    )
  )
}


if (
  ncol(KEYWORD_MATRIX_TEST)
  == 0
) {
  
  stop(
    "Keyword matrix validation failed: no keyword columns were generated."
  )
}


cat(
  "\nKeyword-matrix test rows:",
  nrow(KEYWORD_MATRIX_TEST),
  "\n"
)

cat(
  "Keyword-matrix test columns:",
  ncol(KEYWORD_MATRIX_TEST),
  "\n"
)

cat(
  "SR AND KEYWORD-MATRIX CHECK: PASS\n"
)


# Save the corrected and cleaned Bibliometrix-compatible dataset.
saveRDS(
  M_complete,
  CLEANED_RDS
)

# =============================================================================
# 11. CREATE THE FINAL THEMATIC MAP
# =============================================================================

set.seed(
  1234
)

THEMATIC_MAP <- bibliometrix::thematicMap(
  
  M_complete,
  
  field = "KW_Merged",
  
  n = 250,
  
  minfreq = 5,
  
  ngrams = 1,
  
  stemming = FALSE,
  
  size = 0.5,
  
  n.labels = 2,
  
  community.repulsion = 0.5,
  
  repel = TRUE,
  
  remove.terms = NULL,
  
  synonyms = NULL,
  
  cluster = "louvain",
  
  subgraphs = FALSE,
  
  alpha = 0.5,
  
  seed = 1234
)


saveRDS(
  THEMATIC_MAP,
  THEMATIC_MAP_RDS
)


ggplot2::ggsave(
  
  filename = MAP_PNG,
  
  plot = THEMATIC_MAP$map,
  
  width = 13,
  
  height = 9,
  
  units = "in",
  
  dpi = 600,
  
  bg = "white"
)


ggplot2::ggsave(
  
  filename = MAP_PDF,
  
  plot = THEMATIC_MAP$map,
  
  width = 13,
  
  height = 9,
  
  units = "in",
  
  device = "pdf",
  
  bg = "white"
)


# Display in the RStudio Plots pane.
print(
  THEMATIC_MAP$map
)


# =============================================================================
# 12. CREATE THE FINAL THEMATIC EVOLUTION
# =============================================================================

evolution_cut_years <- c(
  2005,
  2015,
  2020,
  2022,
  2024
)


set.seed(
  1234
)

THEMATIC_EVOLUTION <- bibliometrix::thematicEvolution(
  
  M_complete,
  
  field = "KW_Merged",
  
  years = evolution_cut_years,
  
  n = 100,
  
  minFreq = 2,
  
  size = 0.5,
  
  ngrams = 1,
  
  stemming = FALSE,
  
  n.labels = 1,
  
  repel = TRUE,
  
  remove.terms = NULL,
  
  synonyms = NULL,
  
  cluster = "louvain",
  
  seed = 1234,
  
  assign.evolution.colors = list(
    assign = TRUE,
    alpha = 0.5
  )
)


saveRDS(
  THEMATIC_EVOLUTION,
  THEMATIC_EVOLUTION_RDS
)


# =============================================================================
# CLEAN THE FINAL PERIOD LABEL FOR PUBLICATION
# =============================================================================

EVOLUTION_NODES_FOR_PLOT <- THEMATIC_EVOLUTION$Nodes

EVOLUTION_NODES_FOR_PLOT$group <- as.character(
  EVOLUTION_NODES_FOR_PLOT$group
)

EVOLUTION_NODES_FOR_PLOT$label <- as.character(
  EVOLUTION_NODES_FOR_PLOT$label
)

EVOLUTION_NODES_FOR_PLOT$group[
  EVOLUTION_NODES_FOR_PLOT$group == "2025-2025"
] <- "2025"

EVOLUTION_NODES_FOR_PLOT$label <- sub(
  "--2025-2025$",
  "--2025",
  EVOLUTION_NODES_FOR_PLOT$label
)


EVOLUTION_PLOT <- bibliometrix::plotThematicEvolution(
  
  EVOLUTION_NODES_FOR_PLOT,
  
  THEMATIC_EVOLUTION$Edges,
  
  min.flow = 0
)


htmlwidgets::saveWidget(
  
  EVOLUTION_PLOT,
  
  file = EVOLUTION_HTML,
  
  selfcontained = TRUE
)





# Display in the RStudio Viewer pane.
print(
  EVOLUTION_PLOT
)


# =============================================================================
# 13. HELPER FOR EXCEL-SAFE DATA FRAMES
# =============================================================================

excel_safe <- function(object) {
  
  result <- as.data.frame(
    object,
    stringsAsFactors = FALSE
  )
  
  for (
    column_index in seq_along(
      result
    )
  ) {
    
    if (
      is.list(result[[column_index]]
      )
    ) {
      
      result[[column_index]] <- vapply(
        
        result[[column_index]],
        
        function(value) {
          
          paste(
            as.character(value),
            collapse = "; "
          )
        },
        
        character(1)
      )
    }
  }
  
  result
}


# =============================================================================
# 14. PREPARE AUDIT TABLES
# =============================================================================

settings_table <- data.frame(
  
  Setting = c(
    
    "Originally loaded records",
    
    "Valid-year records in audited input",
    
    "Records retained through 2025",
    
    "Records from 2026 excluded",
    
    "Records with normalized keywords",
    
    "Primary keyword field",
    
    "DE-ID relationship",
    
    "Thematic-map terms",
    
    "Thematic-map minimum frequency",
    
    "Thematic-evolution terms per period",
    
    "Thematic-evolution minimum frequency",
    
    "Clustering method",
    
    "Random seed",
    
    "Stemming",
    
    "Evolution cut years"
  ),
  
  Value = c(
    
    "5022",
    
    as.character(
      nrow(M)
    ),
    
    as.character(
      nrow(M_complete)
    ),
    
    as.character(
      records_2026_excluded
    ),
    
    as.character(
      clean_keyword_records
    ),
    
    "Normalized source keywords stored in KW_Merged",
    
    "DE and ID were exact duplicates; only one copy was used",
    
    "250",
    
    "5",
    
    "100",
    
    "2",
    
    "Louvain",
    
    "1234",
    
    "FALSE",
    
    paste(
      evolution_cut_years,
      collapse = ", "
    )
  ),
  
  stringsAsFactors = FALSE
)


synonym_table <- data.frame(
  
  Variant = names(
    synonym_map
  ),
  
  Canonical_Term = unname(
    synonym_map
  ),
  
  stringsAsFactors = FALSE
)


removed_term_table <- data.frame(
  
  Removed_Term = remove_terms,
  
  stringsAsFactors = FALSE
)


map_cluster_table <- excel_safe(
  THEMATIC_MAP$clusters
)


evolution_nodes <- excel_safe(
  EVOLUTION_NODES_FOR_PLOT
)


evolution_edges <- excel_safe(
  THEMATIC_EVOLUTION$Edges
)


# =============================================================================
# 15. SAVE FINAL AUDIT WORKBOOK
# =============================================================================

writexl::write_xlsx(
  
  list(
    
    Settings =
      settings_table,
    
    Period_Counts =
      as.data.frame(
        period_counts
      ),
    
    Synonym_Mappings =
      synonym_table,
    
    Removed_Terms =
      removed_term_table,
    
    Top_Cleaned_Keywords =
      as.data.frame(
        head(
          cleaned_keyword_frequency,
          300
        )
      ),
    
    Thematic_Map_Clusters =
      map_cluster_table,
    
    Evolution_Nodes =
      evolution_nodes,
    
    Evolution_Edges =
      evolution_edges
  ),
  
  path = AUDIT_WORKBOOK
)


# =============================================================================
# 16. SAVE FINAL SETTINGS TEXT FILE
# =============================================================================

settings_lines <- c(
  
  "THEMATIC MAP AND THEMATIC EVOLUTION — FINAL SETTINGS",
  
  paste0(
    "Originally loaded records: 5,022"
  ),
  
  paste0(
    "Valid-year records: ",
    nrow(M)
  ),
  
  paste0(
    "Records retained through 2025: ",
    nrow(M_complete)
  ),
  
  paste0(
    "Records from incomplete 2026 excluded: ",
    records_2026_excluded
  ),
  
  paste0(
    "Records with normalized keywords: ",
    clean_keyword_records
  ),
  
  paste0(
    "Keyword field: normalized source keywords stored in KW_Merged"
  ),
  
  paste0(
    "DE-ID field relationship: exact duplicates"
  ),
  
  paste0(
    "Thematic map n: 250"
  ),
  
  paste0(
    "Thematic map minfreq: 5"
  ),
  
  paste0(
    "Thematic evolution n: 100"
  ),
  
  paste0(
    "Thematic evolution minFreq: 2"
  ),
  
  paste0(
    "Evolution cut years: ",
    paste(
      evolution_cut_years,
      collapse = ", "
    )
  ),
  
  paste0(
    "Clustering: Louvain"
  ),
  
  paste0(
    "Random seed: 1234"
  ),
  
  paste0(
    "Stemming: FALSE"
  )
)


writeLines(
  
  settings_lines,
  
  con = SETTINGS_FILE,
  
  useBytes = TRUE
)


# =============================================================================
# 17. FINAL CONSOLE REPORT
# =============================================================================

cat(
  "\n",
  strrep(
    "=",
    115
  ),
  "\n",
  sep = ""
)

cat(
  "FINAL THEMATIC MAP AND THEMATIC EVOLUTION COMPLETED\n"
)

cat(
  strrep(
    "=",
    115
  ),
  "\n",
  sep = ""
)


cat(
  "Records retained through 2025:",
  nrow(M_complete),
  "\n"
)

cat(
  "Records from 2026 excluded:",
  records_2026_excluded,
  "\n"
)

cat(
  "Records with normalized keywords:",
  clean_keyword_records,
  "\n"
)

cat(
  "Thematic-map clusters:",
  THEMATIC_MAP$nclust,
  "\n"
)


cat(
  "\nTHEMATIC MAP CLUSTER TABLE\n"
)

print(
  map_cluster_table,
  row.names = FALSE
)


cat(
  "\nTHEMATIC EVOLUTION\n"
)

cat(
  "Evolution nodes:",
  nrow(
    evolution_nodes
  ),
  "\n"
)

cat(
  "Evolution edges:",
  nrow(
    evolution_edges
  ),
  "\n"
)


cat(
  "\nOutput files:\n"
)

cat(
  MAP_PNG,
  "\n"
)

cat(
  MAP_PDF,
  "\n"
)

cat(
  EVOLUTION_HTML,
  "\n"
)

cat(
  AUDIT_WORKBOOK,
  "\n"
)

cat(
  SETTINGS_FILE,
  "\n"
)


cat(
  "\nFINAL STATUS: SUCCESS\n"
)