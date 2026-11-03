# G03/G11 12-case calibration (synthetic rules test)
**No original study was assessed, no quotation or page number generated, no author approval recorded.**

| Case | Domain | Expected | Automated result | Test |
|---|---|---|---|---|
| CAL01 | ST01 | YES | YES | PASS |
| CAL02 | EC02 | EXPLICIT_NO | EXPLICIT_NO | PASS |
| CAL03 | ST01 | NOT_REPORTED | NOT_REPORTED | PASS |
| CAL04 | TV02 | AMBIGUOUS | AMBIGUOUS | PASS |
| CAL05 | PL01 | INSUFFICIENT_ACCESS | INSUFFICIENT_ACCESS | PASS |
| CAL06 | ST01 | YES | YES | PASS |
| CAL07 | TV02 | INSUFFICIENT_ACCESS | INSUFFICIENT_ACCESS | PASS |
| CAL08 | EC01 | INSUFFICIENT_ACCESS | INSUFFICIENT_ACCESS | PASS |
| CAL09 | EC02 | NOT_APPLICABLE | NOT_APPLICABLE | PASS |
| CAL10 | PL11 | LOW | LOW | PASS |
| CAL11 | RP01 | INSUFFICIENT_ACCESS | INSUFFICIENT_ACCESS | PASS |
| CAL12 | PL11 | CROSSWALK_PROHIBITED | CROSSWALK_PROHIBITED | PASS |

## Synthetic 485-record reporting conservation (TEST DATA ONLY)
n = 485; applicable = 475; N/A = 10; No explicitly negative = 5; No not documented = 200.

## Publication guards
- Unassessed values rejected: Unassessed records block publication
- Ordinal leakage risk rejected from YES/NO crosswalk: Forbidden aggregation for PL11

**Next gate:** independent author review of the proposed rules; any real-paper calibration requires authentic full texts, pages, and exact source locations. Phase B1 is not signed.
