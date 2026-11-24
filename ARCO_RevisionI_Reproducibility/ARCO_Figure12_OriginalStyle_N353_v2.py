#!/usr/bin/env python3
"""ARCO Revision-I | Figure 12 in the original serif style (no caption in image).

Panels A and C retain the historical frozen technical register (N=485).
Panel B uses the approved complete-profile Table 10 subset (N=353).

Outputs:
  Fig12_OriginalStyle_A485_B353_C485_NoCaption.pdf
  Fig12_OriginalStyle_A485_B353_C485_NoCaption_preview.png
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

FROZEN_N = 485
APPROVED_COMPLETE_PROFILE_N = 353

PANEL_A = [
    ('Chronological holdout', 59),
    ('Walk-forward', 11),
    ('Rolling window', 6),
    ('Expanding window', 2),
    ('Blocked cross-validation', 1),
    ('Random or shuffled', 6),
]

PANEL_B = [
    ('Chronological split', 129),
    ('Non-stationarity acknowledged', 123),
    ('Shock context mentioned', 69),
    ('Statistical testing', 62),
    ('Economic evaluation', 35),
    ('Shock-period evaluation', 10),
    ('Transaction costs', 9),
    ('Regime-specific evaluation', 17),
    ('Code available', 16),
    ('Data available', 36),
]

PANEL_C = [
    ('At least one passage-verified\nsignal (High)', 34),
    ('No explicit verified signal\nidentified (Low)', 7),
    ('Specific leakage mechanism\nnot classifiable (Unclear)', 444),
]

BLUE = '#3187B5'
GREEN = '#399873'
ORANGE = '#DC995C'
RED = '#D86A64'
GRAY = '#8897AB'
GRID = '#DCE5E8'
TEXT = '#151515'

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Liberation Serif', 'DejaVu Serif', 'Times New Roman'],
    'font.size': 9.0,
    'text.color': TEXT,
    'axes.labelcolor': TEXT,
    'axes.edgecolor': '#707F8C',
    'axes.linewidth': .58,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
    'savefig.facecolor': 'white',
    'savefig.edgecolor': 'white',
})


def style_axis(ax, x_max, tick_step):
    ax.set_xlim(0, x_max)
    ax.set_xticks(np.arange(0, x_max + 1, tick_step))
    ax.grid(axis='x', linestyle=(0, (1.2, 2.4)), color=GRID,
            linewidth=.72, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.spines['bottom'].set_color('#8797A0')
    ax.spines['bottom'].set_linewidth(.6)
    ax.tick_params(axis='x', labelsize=8.1, pad=3, length=2.0, width=.6)
    ax.tick_params(axis='y', length=0, pad=7, labelsize=9.1)
    ax.set_facecolor('white')


def lollipop(ax, data, n, colors, x_max, x_step, label_padding,
             dot_size=14, font_size=8.6):
    ys = np.arange(len(data))[::-1]
    labels = [t for t, _ in data]
    values = [v for _, v in data]
    for yy, value, color in zip(ys, values, colors):
        ax.plot([0, value], [yy, yy], color=color, lw=1.37,
                solid_capstyle='round', zorder=2)
        ax.scatter([value], [yy], s=dot_size, color=color,
                   edgecolors='white', linewidths=.4, zorder=3)
        ax.text(value + label_padding, yy,
                f'{value} ({100.0 * value / n:.1f}%)',
                ha='left', va='center', size=font_size, weight='bold')
    ax.set_yticks(ys, labels)
    ax.set_ylim(-.7, len(data) - .3)
    style_axis(ax, x_max, x_step)


def draw_figure():
    # Wider canvas and slightly taller panel spacing to prevent any overlap.
    fig = plt.figure(figsize=(8.8, 7.1), facecolor='white')
    X0, WIDTH = .30, .54

    a_bottom, a_height = .700, .155
    b_bottom, b_height = .355, .252
    c_bottom, c_height = .095, .145
    title_a, bar_y, tag_y = .955, .918, .882
    title_b, title_c = .650, .290

    # Panel A
    fig.text(X0, title_a, 'A. Validation-design reporting',
             fontsize=11.3, fontweight='bold', ha='left', va='center')
    total_width = WIDTH
    identified_width = total_width * 85 / FROZEN_N
    fig.add_artist(Rectangle((X0, bar_y), identified_width, .021,
                             transform=fig.transFigure, color=BLUE, linewidth=0))
    fig.add_artist(Rectangle((X0 + identified_width, bar_y),
                             total_width - identified_width, .021,
                             transform=fig.transFigure, color=GRAY, linewidth=0))
    fig.text(X0 + identified_width / 2, bar_y + .0105, '85', color='white',
             fontsize=8.5, fontweight='bold', ha='center', va='center')
    fig.text(X0 + identified_width + (total_width - identified_width) / 2,
             bar_y + .0105, '400 (82.5%)', color='white',
             fontsize=8.5, fontweight='bold', ha='center', va='center')
    fig.text(X0, tag_y, 'Design identified (17.5%)', color=BLUE,
             fontsize=8.3, fontweight='bold', va='center')
    fig.text(X0 + WIDTH, tag_y, 'Unclear (82.5%)',
             ha='right', fontsize=8.3, va='center')

    axa = fig.add_axes([X0, a_bottom, WIDTH, a_height])
    lollipop(axa, PANEL_A, FROZEN_N,
             [BLUE, BLUE, BLUE, BLUE, BLUE, ORANGE], 85, 10, 1.4,
             dot_size=16, font_size=8.6)

    # Panel B
    fig.text(X0, title_b,
             'B. Explicitly documented methodological attributes',
             fontsize=10.8, fontweight='bold', ha='left', va='center')
    axb = fig.add_axes([X0, b_bottom, WIDTH, b_height])
    lollipop(axb, PANEL_B, APPROVED_COMPLETE_PROFILE_N,
             [GREEN] * len(PANEL_B), 150, 20, 2.1,
             dot_size=16, font_size=8.6)

    # Panel C
    fig.text(X0, title_c, 'C. Study-level leakage-signal classification',
             fontsize=11.3, fontweight='bold', ha='left', va='center')
    axc = fig.add_axes([X0, c_bottom, WIDTH, c_height])
    lollipop(axc, PANEL_C, FROZEN_N, [RED, RED, GRAY],
             510, 100, 8, dot_size=16, font_size=8.6)
    axc.set_xlabel('Number of studies', fontsize=9.2, labelpad=4)

    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', default='.',
                        help='Folder for the vector PDF and preview PNG')
    args = parser.parse_args()
    outdir = Path(args.output_dir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    assert sum(value for _, value in PANEL_A) == 85
    assert sum(value for _, value in PANEL_C) == FROZEN_N
    assert len(PANEL_B) == 10
    assert all(0 <= value <= APPROVED_COMPLETE_PROFILE_N for _, value in PANEL_B)

    fig = draw_figure()
    pdf = outdir / 'Fig12_OriginalStyle_A485_B353_C485_NoCaption.pdf'
    png = outdir / 'Fig12_OriginalStyle_A485_B353_C485_NoCaption_preview.png'
    fig.savefig(pdf, format='pdf', dpi=300, bbox_inches=None, facecolor='white')
    fig.savefig(png, format='png', dpi=180, bbox_inches=None, facecolor='white')
    plt.close(fig)

    for p in [pdf, png]:
        print(f'CREATED {p} ({p.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
