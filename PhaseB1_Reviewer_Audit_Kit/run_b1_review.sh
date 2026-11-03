#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(realpath "$0")")/.."
PROJECT="$PWD"
INPUT="$PROJECT/PhaseB1_Review_Inputs"
PACKAGE="$PROJECT/PhaseB1_Signoff_Candidate"
FROZEN="$PROJECT/Supplementary_Data_S1_485_FROZEN.xlsx"
SCRIPT="$PROJECT/PhaseB1_Reviewer_Audit_Kit/review_b1_11_gates.py"
OUT="$PROJECT/PhaseB1_Reviewer_Audit_Results"
required=(
  "$FROZEN"
  "$PACKAGE/B1_AUTHOR_APPROVAL_FORM_FILL_THIS.csv"
  "$INPUT/Manuscript(20261029-083519).pdf"
  "$INPUT/Supplementary(20261029-083517).pdf"
  "$INPUT/Reviewer-1 Comments(2).docx"
  "$INPUT/Reviewer-2 Comments(2).docx"
  "$INPUT/Stock_SLR_Complete_Chat_Workflow_Handover_2026-10-06(1)(1).docx"
  "$INPUT/SLR_Stock_Price_Prediction_Complete_Chat_Handover(1)(1).docx"
  "$INPUT/SLR_Chat_Continuity_Handoff_Complete(1)(1).docx"
  "$INPUT/Section5_Complete_Continuity_Handoff_2026-10-06(1)(1).docx"
  "$INPUT/Four_Decade_SLR_Complete_Chat_Work_Handoff_2026-10-06(1).docx"
)
for file in "${required[@]}"; do
 if [[ ! -f "$file" ]]; then echo "MISSING INPUT: $file" >&2; exit 2; fi
done
python "$SCRIPT" \
 --package-dir "$PACKAGE" \
 --frozen "$FROZEN" \
 --manuscript "$INPUT/Manuscript(20261029-083519).pdf" \
 --supplementary "$INPUT/Supplementary(20261029-083517).pdf" \
 --reviewer1 "$INPUT/Reviewer-1 Comments(2).docx" \
 --reviewer2 "$INPUT/Reviewer-2 Comments(2).docx" \
 --handover \
  "$INPUT/Stock_SLR_Complete_Chat_Workflow_Handover_2026-10-06(1)(1).docx" \
  "$INPUT/SLR_Stock_Price_Prediction_Complete_Chat_Handover(1)(1).docx" \
  "$INPUT/SLR_Chat_Continuity_Handoff_Complete(1)(1).docx" \
  "$INPUT/Section5_Complete_Continuity_Handoff_2026-10-06(1)(1).docx" \
  "$INPUT/Four_Decade_SLR_Complete_Chat_Work_Handoff_2026-10-06(1).docx" \
 --output-dir "$OUT"
