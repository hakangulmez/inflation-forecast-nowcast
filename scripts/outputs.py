# ruff: noqa: E501
"""Generate publication artifacts directly from aggregate result tables."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from policy_outputs import emit_policy

from inflation_forecast_nowcast.core import error_scores
from inflation_forecast_nowcast.viz import PALETTE, apply_style

root = Path.cwd()
apply_style()
figdir = root / "figures"
figdir.mkdir(exist_ok=True)
scores = pd.read_csv(root / "results/inflation_scores.csv")
now = pd.read_csv(root / "results/nowcast_scores.csv")
manifest = json.loads((root / "results/manifest.json").read_text())
methods = ["RW", "AO", "AR", "Phillips", "BVAR", "LASSO", "Ensemble"]
targets = ["ea_headline", "ea_core", "tr_headline"]
fig, ax = plt.subplots(figsize=(10, 3.7))
matrix = []
for target in targets:
    matrix.append(
        [
            float(
                scores.query("target==@target and model==@name and horizon==1").relative_rmse.iloc[
                    0
                ]
            )
            for name in methods
        ]
    )
image = ax.imshow(
    matrix,
    cmap=LinearSegmentedColormap.from_list("okabe", [PALETTE[2], "#FFFFFF", PALETTE[3]]),
    vmin=0.3,
    vmax=1.7,
    aspect="auto",
)
for i, target in enumerate(targets):
    for j, name in enumerate(methods):
        r = scores.query("target==@target and model==@name and horizon==1").iloc[0]
        ax.text(
            j,
            i,
            f"{r.relative_rmse:.2f}\n[{r.lo90:.2f}, {r.hi90:.2f}]",
            ha="center",
            va="center",
            fontsize=9,
        )
ax.set(
    xticks=range(len(methods)),
    xticklabels=methods,
    yticks=range(3),
    yticklabels=["EA headline", "EA core", "TR headline"],
    title="One-month y/y inflation forecasts: error vs random walk",
)
fig.colorbar(image, ax=ax, label="Lower is better; RW = 1")
fig.text(
    0.02,
    0.02,
    "Latest-vintage pseudo-real-time; evaluation target months from January 2015.\n90% paired-block intervals in brackets. Eurostat / CBRT-TURKSTAT; author calculations.",  # noqa: E501
    fontsize=8,
)
fig.tight_layout(rect=(0, 0.13, 1, 1))
fig.savefig(figdir / "headline.png", dpi=300)
fig.savefig(figdir / "headline.pdf")
plt.close(fig)
# Full horizon table is also visualized, with uncertainty in every cell.
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for ax, h in zip(axes.ravel(), [1, 3, 6, 12], strict=True):
    values = np.array(
        [
            [
                scores.query("target==@target and model==@name and horizon==@h").relative_rmse.iloc[
                    0
                ]
                for name in methods
            ]
            for target in targets
        ]
    )
    ax.imshow(
        values,
        cmap=LinearSegmentedColormap.from_list("oi", [PALETTE[2], "#FFFFFF", PALETTE[3]]),
        vmin=0.3,
        vmax=2,
        aspect="auto",
    )
    for i, target in enumerate(targets):
        for j, name in enumerate(methods):
            r = scores.query("target==@target and model==@name and horizon==@h").iloc[0]
            ax.text(
                j,
                i,
                f"{r.relative_rmse:.2f}\n[{r.lo90:.2f},{r.hi90:.2f}]",
                ha="center",
                va="center",
                fontsize=6,
            )
    ax.set(
        xticks=range(len(methods)),
        xticklabels=methods,
        yticks=range(3),
        yticklabels=["EA headline", "EA core", "TR"],
        title=f"Horizon {h} months",
    )
fig.text(
    0.02,
    0.01,
    "RW=1; brackets: 90% paired-block intervals. Latest vintage; Eurostat/CBRT-TURKSTAT. Target: point y/y inflation. Benchmarks use origin information only.",  # noqa: E501
    fontsize=8,
)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(figdir / "forecast_heatmap.png", dpi=300)
fig.savefig(figdir / "forecast_heatmap.pdf")
plt.close(fig)
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, exclude in zip(axes, [False, True], strict=True):
    for j, name in enumerate(["Bridge", "UMIDAS", "DFM"]):
        x = now[(now.model == name) & (now.exclude_covid == exclude)].sort_values("info_month")
        ax.plot(x.info_month, x.rmse, color=PALETTE[j], label=name)
        ax.fill_between(x.info_month, x.rmse_lo90, x.rmse_hi90, color=PALETTE[j], alpha=0.14)
    ax.set(
        title="Without COVID" if exclude else "All quarters",
        xlabel="Information month (4 = after quarter)",
        ylabel="GDP q/q log-growth RMSE (pp; not annualised)",
        xticks=[1, 2, 3, 4],
    )
    ax.legend(fontsize=8)
fig.text(
    0.02,
    0.01,
    "2012Q1 onward; simulated fixed release lags; 90% quarterly-block intervals. Eurostat; author calculations.",  # noqa: E501
    fontsize=7,
)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(figdir / "nowcast.png", dpi=300)
fig.savefig(figdir / "nowcast.pdf")
plt.close(fig)
# Convergence-only sensitivity uses matched evaluation quarters, with no retuning.

private = pd.read_csv(root / "runs" / manifest["analysis_id"] / "nowcasts.csv")
sensitivity = []
for info in range(1, 5):
    a = (
        private[
            (private.model == "DFM") & (private.info_month == info) & private.converged.eq(True)
        ]
        .set_index("quarter")
        .error
    )
    b = (
        private[(private.model == "Bridge") & (private.info_month == info)]
        .set_index("quarter")
        .error
    )
    common = pd.concat([a.rename("e"), b.rename("b")], axis=1).dropna()
    sensitivity.append(dict(info_month=info, **error_scores(common.e, common.b, block=4)))
pd.DataFrame(sensitivity).to_csv(root / "results/dfm_convergence_sensitivity.csv", index=False)

for name in [
    "inflation_scores",
    "inflation_scores_yoy",
    "inflation_scores_mm",
    "nowcast_scores",
    "dfm_convergence_sensitivity",
]:
    t = pd.read_csv(root / "results" / f"{name}.csv")
    lines = [
        "| " + " | ".join(t.columns) + " |",
        "| " + " | ".join(["---"] * len(t.columns)) + " |",
    ]
    lines += [
        "| " + " | ".join(map(str, row)) + " |" for row in t.itertuples(index=False, name=None)
    ]
    (root / "results" / f"{name}.md").write_text("\n".join(lines) + "\n")
(figdir / "linkedin").mkdir(exist_ok=True)
fig, ax = plt.subplots(figsize=(4, 4), dpi=300)
for j, (target, model_name, label) in enumerate(
    [
        ("ea_core", "BVAR", "EA core / BVAR"),
        ("ea_headline", "Ensemble", "EA headline / ensemble"),
    ]
):
    x = scores[(scores.target == target) & (scores.model == model_name)].sort_values("horizon")
    ax.plot(x.horizon, x.relative_rmse, label=label, color=PALETTE[j])
    ax.fill_between(x.horizon, x.lo90, x.hi90, color=PALETTE[j], alpha=0.14)
ax.axhline(1, color=".5", lw=0.7)
ax.set(
    title="What improves inflation forecasts?",
    xlabel="Horizon (months)",
    ylabel="Error relative to random walk",
)
ax.legend(fontsize=7)
fig.text(
    0.02,
    0.01,
    "90% block intervals; latest vintage. Official sources.\nLocal draft for review; RW=1.",
    fontsize=6,
)
fig.tight_layout(rect=(0, 0.09, 1, 1))
fig.savefig(figdir / "linkedin/headline.png", dpi=300)
plt.close(fig)
emit_policy(root, scores, now, manifest)
