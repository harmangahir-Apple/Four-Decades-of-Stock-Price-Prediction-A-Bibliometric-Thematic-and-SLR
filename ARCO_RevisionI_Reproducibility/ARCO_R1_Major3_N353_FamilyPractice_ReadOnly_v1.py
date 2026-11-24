#!/usr/bin/env python3
"""Read-only ARCO Reviewer 1 Major 3 gate: join approved N353 profiles to frozen families.
No input file is modified, no output CSV is created, and no unapproved coding is inferred.
"""
import argparse
import csv
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path

MASTER_SHA = '4992a401f78609c5a9aaf6212b952c7832c7d4adc6d2a240367280558f7af33e'
FROZEN_SHA = '601602179cf2e2655df6f5b13c6cf1442275d46c683665e70f9fb6224511c70f'
EXPECTED = {
    'Nonstationarity_Acknowledged': (123, 203, 27),
    'Regime_Specific_Evaluation': (17, 316, 20),
    'Shock_Context_Mentioned': (69, 278, 6),
    'Shock_Period_Evaluation': (10, 332, 11),
    'Chronological_Split': (129, 24, 200),
    'Economic_Evaluation': (35, 305, 13),
    'Transaction_Costs': (9, 343, 1),
    'Statistical_Testing': (62, 277, 14),
    'Code_Available': (16, 334, 3),
    'Data_Available': (36, 267, 50),
}
SELECTED = (
    'Chronological_Split', 'Nonstationarity_Acknowledged',
    'Statistical_Testing', 'Economic_Evaluation',
    'Transaction_Costs', 'Code_Available', 'Data_Available',
)

def norm(s):
    return re.sub(r'[^a-z0-9]+', '', str(s).lower())

ALIASES = {norm(k): k for k in EXPECTED}
ALIASES.update({
    'nonstationarity': 'Nonstationarity_Acknowledged',
    'nonstationarityacknowledgement': 'Nonstationarity_Acknowledged',
    'statisticaltest': 'Statistical_Testing',
    'formalstatisticaltesting': 'Statistical_Testing',
    'codeavailability': 'Code_Available',
    'dataavailability': 'Data_Available',
    'regimespecificeval': 'Regime_Specific_Evaluation',
    'shockperiodeval': 'Shock_Period_Evaluation',
    'chronologicalholdout': 'Chronological_Split',
})

def state(s):
    x = norm(s)
    if x == 'yes':
        return 'Yes'
    if x in ('noassessednotdocumented', 'assessednotdocumented'):
        return 'No_assessed_not_documented'
    if x in ('unclear', 'unclearambiguousfulltext'):
        return 'Unclear'
    if x == 'notrecoverable':
        return 'Not_recoverable'
    return None

def load(path, sha):
    if not path.is_file():
        raise ValueError(f'MISSING SOURCE: {path}')
    got = hashlib.sha256(path.read_bytes()).hexdigest()
    if got != sha:
        raise ValueError(f'SHA256 MISMATCH for {path}\nExpected {sha}\nObserved {got}')
    with path.open(encoding='utf-8-sig', newline='') as fh:
        rd = csv.DictReader(fh)
        rows = list(rd)
        return (rd.fieldnames or []), rows

def dimension_map(col, rows):
    samples = [ALIASES.get(norm(r.get(col, ''))) for r in rows]
    found = set(x for x in samples if x)
    if found == set(EXPECTED) and all(samples):
        return samples
    return None

def validated_state_column(col, rows, dims, complete):
    records = defaultdict(dict)
    for row, d in zip(rows, dims):
        pid = row['Paper_ID'].strip()
        status = state(row.get(col, ''))
        if pid in complete:
            if status is None or d in records[pid]:
                return None
            records[pid][d] = status
    if any(set(records[pid]) != set(EXPECTED) for pid in complete):
        return None
    for dim, target in EXPECTED.items():
        counts = Counter(records[pid][dim] for pid in complete)
        if (counts['Yes'], counts['No_assessed_not_documented'], counts['Unclear']) != target:
            return None
        if counts['Not_recoverable']:
            return None
    return records

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--master', type=Path, required=True)
    parser.add_argument('--frozen', type=Path, required=True)
    args = parser.parse_args()
    mfields, master = load(args.master, MASTER_SHA)
    ffields, frozen = load(args.frozen, FROZEN_SHA)
    print('PASS: MASTER SHA256', MASTER_SHA)
    print('PASS: FROZEN SHA256', FROZEN_SHA)
    print('MASTER ROWS:', len(master), 'COLUMNS:', mfields)
    if len(master) != 3532 or 'Paper_ID' not in mfields:
        raise ValueError('Master row count or Paper_ID gate failed')
    if len(frozen) != 485 or not {'Paper_ID', 'Principal_Method_Family'} <= set(ffields):
        raise ValueError('Frozen register gate failed')
    dimcols = [(col, dimension_map(col, master)) for col in mfields if col != 'Paper_ID']
    dimcols = [(col, val) for col, val in dimcols if val is not None]
    if len(dimcols) != 1:
        raise ValueError('Cannot uniquely identify exact dimension column; candidates: '
                         + str([x[0] for x in dimcols]))
    dcol, dims = dimcols[0]
    study_dimensions = defaultdict(list)
    for r, d in zip(master, dims):
        study_dimensions[r['Paper_ID'].strip()].append(d)
    complete = {pid for pid, entries in study_dimensions.items()
                if len(entries) == 10 and set(entries) == set(EXPECTED)}
    if len(complete) != 353 or len(master) - len(complete) * 10 != 2:
        raise ValueError('353 complete profiles + 2 extra position gate failed; '
                         f'complete={len(complete)}, extra={len(master)-len(complete)*10}')
    matches = []
    for col in mfields:
        if col in ('Paper_ID', dcol):
            continue
        result = validated_state_column(col, master, dims, complete)
        if result is not None:
            priority = sum(w for term, w in [('approved', 10), ('final', 8),
                       ('decision', 4), ('state', 3), ('status', 2)] if term in col.lower())
            matches.append((priority, col, result))
    if not matches:
        preview = {c: [r.get(c, '')[:45] for r in master[:2]] for c in mfields}
        print('SCHEMA PREVIEW (first two values per column):', preview)
        raise ValueError('Cannot identify a state column matching the author-approved N353 counts')
    matches.sort(key=lambda x: (-x[0], x[1]))
    if len(matches) > 1 and matches[0][0] == matches[1][0]:
        raise ValueError('Ambiguous equally ranked state columns: ' + str([x[1] for x in matches]))
    _, scol, records = matches[0]
    families = {r['Paper_ID'].strip(): r['Principal_Method_Family'].strip() for r in frozen}
    if len(families) != 485 or not complete <= set(families) or any(not families[pid] for pid in complete):
        raise ValueError('Study identity/family join failed')
    print('PASS: AUTHOR-APPROVED 353 complete profiles with 10 four-state decisions each')
    print('DIMENSION COLUMN:', dcol)
    print('STATE COLUMN:', scol)
    print('PASS: ALL TEN DIMENSION TOTALS EXACTLY MATCH AUTHOR-APPROVED TABLE 10')
    family_groups = defaultdict(list)
    for pid in sorted(complete):
        family_groups[families[pid]].append(pid)
    print('\nFAMILY SIZES (N353):')
    for family, ids in sorted(family_groups.items(), key=lambda x: (-len(x[1]), x[0])):
        print(f'  {family}: {len(ids)}')
    print('\nFAMILY x PRACTICE: YES / SUBGROUP N (PERCENT OF ALL SUBGROUP STUDIES)')
    print('Note: denominator includes Unclear; No and Unclear are never conflated.')
    print('FAMILY | N | ' + ' | '.join(SELECTED))
    for family, ids in sorted(family_groups.items(), key=lambda x: (-len(x[1]), x[0])):
        cells = []
        for dim in SELECTED:
            count = sum(records[pid][dim] == 'Yes' for pid in ids)
            cells.append(f'{count}/{len(ids)} ({100*count/len(ids):.1f}%)')
        print(f'{family} | {len(ids)} | ' + ' | '.join(cells))
    print('\nPASS: READ-ONLY; no study recodes; no files changed.')
    print('CAUTION: These are historical single-label family assignments, not validated multi-label families.')
    print('CAUTION: The N353 subset is nonrandom; no field-wide or causal family comparison.')

if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, csv.Error) as exc:
        print('STOP:', exc)
        raise SystemExit(1)
