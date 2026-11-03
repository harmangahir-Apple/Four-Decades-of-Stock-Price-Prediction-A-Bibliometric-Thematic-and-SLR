from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = Path("Figure15_Output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# CORRECTED DENOMINATORS
# ============================================================

period_order = ["2016–2020", "2021–2022", "2023–2024", "2025–2026"]

period_sizes = pd.Series(
    {
        "2016–2020": 27,
        "2021–2022": 36,
        "2023–2024": 49,
        "2025–2026": 380,
    }
)

# ============================================================
# CORRECTED COUNT MATRIX
# ============================================================

category_order = [
    "Historical market data",
    "Technical indicators",
    "Financial news and textual information",
    "Decomposition or transformed representations",
    "Social media or public-opinion information",
    "Index, sectoral, relational, or cross-market context",
    "Macroeconomic or systemic variables",
    "Fundamental or accounting information",
    "Alternative or attention-related information",
    "Input modality not recoverable",
]

count_matrix = pd.DataFrame(
    {
        "2016–2020": [15, 8, 3, 5, 1, 1, 1, 1, 0, 0],
        "2021–2022": [22, 7, 7, 4, 4, 2, 1, 0, 1, 0],
        "2023–2024": [30, 13, 7, 3, 4, 2, 2, 1, 0, 3],
        "2025–2026": [226, 90, 76, 50, 33, 22, 17, 16, 5, 31],
    },
    index=category_order,
    dtype=int,
)

# ============================================================
# PERCENTAGE MATRIX
# ============================================================

percentage_matrix = (
    count_matrix.div(period_sizes, axis=1) * 100
).round(1)

# ============================================================
# VERIFICATION
# ============================================================

assert int(period_sizes.sum()) == 492, "Period total must be 492"
assert int(period_sizes["2025–2026"]) == 380, "2025–2026 must be 380"

expected_latest = pd.Series(
    [226, 90, 76, 50, 33, 22, 17, 16, 5, 31],
    index=category_order,
    dtype=int,
)

assert count_matrix["2025–2026"].equals(expected_latest), \
    "Latest period counts do not match corrected values"

# ============================================================
# PLOT SETTINGS
# ============================================================

plt.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 12,
        "axes.labelsize": 14,
        "xtick.labelsize": 12,
        "ytick.labelsize": 13,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)

values = percentage_matrix.to_numpy(dtype=float)

fig, ax = plt.subplots(figsize=(11.5, 7.2))

# Same visual feel as attached figure
im = ax.imshow(
    values,
    aspect="auto",
    cmap="viridis",
    vmin=0,
    vmax=100,
)

# ============================================================
# AXES
# ============================================================

top_labels = [
    "2016–2020\n(n=27)",
    "2021–2022\n(n=36)",
    "2023–2024\n(n=49)",
    "2025–2026\n(n=380)",
]

ax.set_xticks(np.arange(len(period_order)))
ax.set_xticklabels(top_labels)

ax.set_yticks(np.arange(len(category_order)))
ax.set_yticklabels(category_order)

# Put x tick labels on top
ax.xaxis.tick_top()
ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False, pad=8)

# Remove tick marks
ax.tick_params(axis="both", length=0)

# Bottom axis label
ax.set_xlabel("Publication period", labelpad=25)
ax.xaxis.set_label_position("bottom")

# ============================================================
# GRIDLINES
# ============================================================

# Major white grid lines
for x in np.arange(-0.5, len(period_order), 1):
    ax.axvline(x, color="white", lw=1.1, alpha=0.65)

for y in np.arange(-0.5, len(category_order), 1):
    ax.axhline(y, color="white", lw=1.1, alpha=0.65)

# Dashed separation above last row
ax.axhline(len(category_order) - 1.5, color="white", lw=1.0, ls="--", alpha=0.8)

# ============================================================
# CELL ANNOTATIONS
# ============================================================

for i in range(values.shape[0]):
    for j in range(values.shape[1]):
        val = values[i, j]

        if val == 0:
            text = "0.0"
        else:
            text = f"{val:.1f}"

        # Contrast similar to attached style
        if val >= 45:
            color = "black"
            weight = "bold"
        elif val >= 18:
            color = "white"
            weight = "normal"
        else:
            color = "white"
            weight = "normal"

        ax.text(
            j, i, text,
            ha="center", va="center",
            color=color,
            fontsize=12,
            fontweight=weight
        )

# ============================================================
# COLORBAR
# ============================================================

cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.02)
cbar.set_label("Studies within period (%)", rotation=90)
cbar.ax.tick_params(labelsize=11)

# ============================================================
# CLEAN SPINES
# ============================================================

for spine in ax.spines.values():
    spine.set_visible(False)

fig.subplots_adjust(left=0.44, right=0.92, top=0.88, bottom=0.12)

# ============================================================
# SAVE
# ============================================================

out_pdf = OUTPUT_DIR / "Figure15_Input_Modality_Period_Heatmap_SCIEQ1.pdf"
out_png = OUTPUT_DIR / "Figure15_Input_Modality_Period_Heatmap_SCIEQ1.png"
out_svg = OUTPUT_DIR / "Figure15_Input_Modality_Period_Heatmap_SCIEQ1.svg"

fig.savefig(out_pdf, bbox_inches="tight")
fig.savefig(out_png, dpi=600, bbox_inches="tight")
fig.savefig(out_svg, bbox_inches="tight")

plt.close(fig)

print("Saved:")
print(out_pdf.resolve())
print(out_png.resolve())
print(out_svg.resolve())
print("\nCorrected percentage matrix:")
print(percentage_matrix)