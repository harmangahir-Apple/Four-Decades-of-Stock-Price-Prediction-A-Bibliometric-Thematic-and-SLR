#!/usr/bin/env python3
"""Publication-ready, provenance-checked application-area heatmap (n=4,975).

Phase A: 5,022 indexed records -> 47 omissions -> 4,975 application-area
records. P05017 (Yuelong Zhang, 2024 UCLA MSc thesis) is RETAINED once:
High-frequency & market microstructure, year 2024.

Usage on existing workstation:
 python regenerate_figure4_4975_q1.py
or explicitly:
 python regenerate_figure4_4975_q1.py --matrix /path/to/Application_Area_Year_Matrix.csv \
     --audit /path/to/Application_Area_Record_Level_Audit_4975.csv \
     --outdir /path/to/08_Figures/Figure5_Application_Area_Heatmap

Requires numpy, pandas, matplotlib. PDF and SVG are vector graphics; PNG and
TIFF are exported at 600 dpi. The original input is never overwritten.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.patches import Rectangle
from matplotlib.ticker import ScalarFormatter
import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_MATRIX = PROJECT_DIR / 'World_Map_Heatmap_Output' / 'Application_Area_Year_Matrix.csv'
DEFAULT_OUTDIR = PROJECT_DIR / '08_Figures' / 'Figure5_Application_Area_Heatmap'
EXPECTED_N = 4_975
THESIS_ID, THESIS_YEAR = 'P05017', 2024
PARTIAL_YEAR = 2026

# Abbreviations are for readability only; they do not alter classifications.
DISPLAY = {
    'Price & index forecasting': 'Price and index forecasting',
    'Direction, trend & regime': 'Direction, trend, and regime',
    'Return forecasting': 'Return forecasting',
    'Volatility, risk & uncertainty': 'Volatility, risk, and uncertainty',
    'Sentiment, news & social media': 'Sentiment, news, and social media',
    'Trading, portfolio & decision support': 'Trading, portfolio, and\ndecision support',
    'High-frequency & market microstructure': 'High-frequency and\nmarket microstructure',
    'Multi-asset & cross-market': 'Multi-asset and cross-market',
    'General, multi-target & other': 'General, multi-target, and other',
}
HF_LABEL = 'High-frequency & market microstructure'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--matrix', type=Path, default=DEFAULT_MATRIX,
                   help='Original 4,974-row or updated 4,975-row year matrix')
    p.add_argument('--audit', type=Path, default=None,
                   help='Optional 4,975-row study-level audit with P05017 ID')
    p.add_argument('--outdir', type=Path, default=DEFAULT_OUTDIR)
    p.add_argument('--dpi', type=int, default=600)
    return p.parse_args()


def load_and_validate(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f'Matrix missing: {path}')
    frame = pd.read_csv(path, encoding='utf-8-sig')
    if 'Application_Area' not in frame.columns:
        raise ValueError('Input matrix needs an Application_Area column')
    ycols = sorted((c for c in frame.columns if str(c).isdigit()), key=int)
    years = [int(c) for c in ycols]
    if years != list(range(1987, 2027)):
        raise AssertionError('Expected exactly 1987–2026, one column for each year')
    if frame['Application_Area'].duplicated().any():
        raise AssertionError('Duplicate application-area category')
    if frame.shape[0] != 9:
        raise AssertionError(f'Expected nine application areas; found {frame.shape[0]}')
    for c in ycols:
        v = pd.to_numeric(frame[c], errors='raise')
        if (v < 0).any() or not np.all(np.isclose(v, np.rint(v))):
            raise AssertionError(f'Invalid nonnegative count in {c}')
        frame[c] = v.astype(int)
    mask = frame['Application_Area'].eq(HF_LABEL)
    if int(mask.sum()) != 1:
        raise AssertionError(f'Missing or duplicated category: {HF_LABEL}')
    old_total = int(frame[ycols].to_numpy().sum())
    original_hf_2024 = int(frame.loc[mask, '2024'].iloc[0])
    if old_total == 4_974:
        if original_hf_2024 != 2:
            raise AssertionError('4,974 matrix unexpected 2024 high-frequency count: refusing patch')
        frame.loc[mask, '2024'] += 1
        procedure = 'Added P05017 exactly once (2024 high-frequency 2→3)'
    elif old_total == EXPECTED_N:
        if original_hf_2024 != 3:
            raise AssertionError('4,975 matrix does not show expected P05017 cell')
        procedure = 'P05017 was already included; no additional count added'
    else:
        raise AssertionError(f'Unexpected input total {old_total:,}; expected 4,974 or 4,975')
    total = int(frame[ycols].to_numpy().sum())
    hf_total = int(frame.loc[mask, ycols].sum(axis=1).iloc[0])
    assert total == EXPECTED_N and hf_total == 62 and int(frame.loc[mask, '2024'].iloc[0]) == 3
    return frame, ycols, years, old_total, procedure


def validate_study_audit(audit: Path | None, frame: pd.DataFrame, ycols: list[str]):
    if audit is None:
        return 'Not supplied; matrix checks and primary thesis PDF support the update'
    if not audit.is_file():
        raise FileNotFoundError(f'--audit does not exist: {audit}')
    ids = pd.read_csv(audit, dtype=str, encoding='utf-8-sig').fillna('')
    required = {'Paper_ID', 'Year', 'Application_Area'}
    if not required.issubset(ids.columns):
        raise ValueError(f'Study-level audit needs columns {sorted(required)}')
    if len(ids) != EXPECTED_N or ids['Paper_ID'].nunique() != EXPECTED_N:
        raise AssertionError('Study-level audit must contain 4,975 distinct Paper_ID values')
    thesis = ids.loc[ids['Paper_ID'] == THESIS_ID]
    if len(thesis) != 1 or thesis['Year'].iloc[0] != '2024' or thesis['Application_Area'].iloc[0] != HF_LABEL:
        raise AssertionError('P05017 must occur exactly once in 2024 high-frequency category')
    pivot = (ids.groupby(['Application_Area', 'Year']).size().unstack(fill_value=0)
             .reindex(index=frame['Application_Area'], columns=ycols, fill_value=0))
    matrix = frame[ycols].to_numpy(dtype=int)
    if not np.array_equal(pivot.to_numpy(dtype=int), matrix):
        different = int(np.count_nonzero(pivot.to_numpy(dtype=int) != matrix))
        raise AssertionError(f'Study-level area/year counts disagree in {different} cells')
    return f'PASS: {EXPECTED_N:,} unique IDs; P05017 included once; all 9 x 40 area/year cells match' 


def main():
    a = parse_args()
    outdir = a.outdir.expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    frame, ycols, years, original_total, procedure = load_and_validate(a.matrix.expanduser())
    audit_status = validate_study_audit(a.audit, frame, ycols)
    matrix_out = outdir / 'Application_Area_Year_Matrix_4975_VERIFIED.csv'
    frame.to_csv(matrix_out, index=False)
    values = frame[ycols].to_numpy(dtype=int)
    nr = len(frame)
    recent_years = list(range(2021, PARTIAL_YEAR + 1))
    recent_cols = [years.index(x) for x in recent_years]
    recent = values[:, recent_cols]
    labels = []
    for name, n in zip(frame['Application_Area'], values.sum(axis=1)):
        label = DISPLAY.get(str(name), str(name).replace('&', 'and'))
        labels.append(f'{label}  (n={n:,})')

    mpl.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'STIXGeneral', 'DejaVu Serif'],
        'font.size': 10.2,
        'axes.labelsize': 10.2,
        'axes.titlesize': 11.0,
        'xtick.labelsize': 9.0,
        'ytick.labelsize': 10.0,
        'axes.linewidth': 0.5,
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
        'svg.fonttype': 'none',
        'figure.facecolor': 'white',
        'savefig.facecolor': 'white',
    })
    cmap = mpl.colormaps.get_cmap('viridis').copy()
    cmap.set_bad('#F1F3F5')
    norm = LogNorm(vmin=1, vmax=values.max())
    fig = plt.figure(figsize=(11.25, 5.95), facecolor='white')
    # Main historical panel is unannotated; detailed recent panel supplies readable values.
    gs = fig.add_gridspec(1, 2, left=.29, right=.968, bottom=.245, top=.875,
                          width_ratios=[1.8, 1.0], wspace=.095)
    ax_all = fig.add_subplot(gs[0, 0])
    ax_new = fig.add_subplot(gs[0, 1], sharey=ax_all)

    for ax, array, this_years in [(ax_all, values, years), (ax_new, recent, recent_years)]:
        masked = np.ma.masked_equal(array, 0)
        im = ax.imshow(masked, origin='upper', aspect='auto', interpolation='nearest', cmap=cmap, norm=norm)
        ax.set_xlim(-.5, len(this_years) - .5)
        ax.set_ylim(nr - .5, -.5)
        ax.set_xticks(np.arange(-.5, len(this_years), 1), minor=True)
        ax.set_yticks(np.arange(-.5, nr, 1), minor=True)
        ax.grid(which='minor', color='white', lw=.5, alpha=.85)
        ax.tick_params(which='minor', bottom=False, left=False)
        ax.tick_params(axis='both', which='major', length=0, pad=5)
        for sp in ax.spines.values():
            sp.set_visible(False)
        if PARTIAL_YEAR in this_years:
            k = this_years.index(PARTIAL_YEAR)
            ax.add_patch(Rectangle((k-.5, -.5), 1, nr, fill=False, edgecolor='#424854',
                                   linestyle=(0, (3, 2)), linewidth=1.1, zorder=6))

    # Separate y-axis category labels without repeating them inside each panel.
    ax_all.set_yticks(np.arange(nr))
    ax_all.set_yticklabels(labels, ha='right', fontsize=10.2)
    ax_new.tick_params(axis='y', labelleft=False, left=False)
    wanted = [1987, 1995, 2000, 2005, 2010, 2015, 2020, 2026]
    ax_all.set_xticks([years.index(y) for y in wanted], [str(y)+'*' if y == 2026 else str(y) for y in wanted], fontsize=9.0)
    ax_new.set_xticks(range(len(recent_years)), [str(y)+'*' if y == 2026 else str(y) for y in recent_years], fontsize=9.3)
    ax_all.set_title('A   Full period (1987–2026)', loc='left', pad=13, weight='semibold')
    ax_new.set_title('B   Recent years (2021–2026)', loc='left', pad=13, weight='semibold')

    # All positive recent-year counts are legible in the zoomed panel; historical heatmap is uncluttered.
    for r in range(nr):
        for c, val in enumerate(recent[r]):
            if val == 0:
                continue
            rgba = cmap(norm(val))
            luminance = .2126*rgba[0]+.7152*rgba[1]+.0722*rgba[2]
            color = 'white' if luminance < .48 else '#17212B'
            ax_new.text(c, r, f'{val:,}', ha='center', va='center', color=color,
                        fontsize=9.1, fontweight='bold' if val >= 100 else 'medium',
                        zorder=8)

    # Shared horizontal colorbar: numbers denote actual counts, colors follow log normalization.
    cb_ax = fig.add_axes([.41, .125, .45, .024])
    bar = fig.colorbar(im, cax=cb_ax, orientation='horizontal')
    ticks = [1, 2, 5, 10, 20, 50, 100, 200, 500]
    bar.set_ticks([x for x in ticks if x <= values.max()])
    bar.ax.xaxis.set_major_formatter(ScalarFormatter())
    bar.ax.tick_params(labelsize=8.6, length=2)
    bar.outline.set_linewidth(.55)
    cb_ax.set_title('Publications per year (logarithmic colour scale)', fontsize=9.2, pad=8)
    fig.text(.29, .038, 'Grey: zero records.  *2026: incomplete publication year.  Row totals sum to n = 4,975.',
             ha='left', va='center', fontsize=9.4, color='#3C4650')

    stem = outdir / 'Fig5_Application_Area_Annual_Heatmap_Q1'
    rendered = []
    for ext, kw in [('.pdf', {}), ('.svg', {}), ('.png', {'dpi': a.dpi}),
                    ('.tiff', {'dpi': a.dpi, 'pil_kwargs': {'compression':'tiff_lzw'}})]:
        fn = stem.with_suffix(ext)
        fig.savefig(fn, facecolor='white', bbox_inches='tight', pad_inches=.09, **kw)
        rendered.append(fn)
    plt.close(fig)

    metrics = {
        'input_path': str(a.matrix.resolve()),
        'input_SHA256': sha256(a.matrix),
        'input_total': original_total,
        'revision': procedure,
        'reconciled_total': int(values.sum()),
        'P05017': {'decision':'RETAIN', 'year':2024, 'application_area':HF_LABEL,
                   '2024_cell_count': int(recent[frame['Application_Area'].eq(HF_LABEL).to_numpy(), recent_years.index(2024)][0]),
                   'row_total': int(values[frame['Application_Area'].eq(HF_LABEL).to_numpy(), :].sum()),
                   'source': 'UCLA eScholarship https://escholarship.org/uc/item/2pz9p0dc'},
        'study_level_audit':audit_status,
        'year_range':[min(years),max(years)],
        '2026_is_partial':True,
        'row_totals': dict(zip(frame['Application_Area'], values.sum(axis=1).astype(int).tolist())),
        'output_matrix_SHA256': sha256(matrix_out),
        'figure_outputs': [str(fn) for fn in rendered]
    }
    report = outdir / 'Figure4_4975_Provenance_Check.json'
    report.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding='utf-8')
    print('AUDIT:', audit_status)
    print('REVISION:', procedure)
    print('TOTAL:', values.sum())
    print('HF_2024:', metrics['P05017']['2024_cell_count'], 'HF_ALL:', metrics['P05017']['row_total'])
    print('OUTPUTS:')
    for fn in [*rendered, matrix_out, report]:
        print(' -', fn)


if __name__ == '__main__':
    main()
