# ruff: noqa: E501
"""Render V3 claims only from traceable aggregate outputs; inherited GDP unchanged."""

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from policy import write_note

from inflation_forecast_nowcast.viz import PALETTE, apply_style

root = Path.cwd()
apply_style()
scores = pd.read_csv(root / "results/inflation_scores.csv")
now = pd.read_csv(root / "results/nowcast_scores.csv")
models = ["RW", "AO", "AR", "BVAR", "Phillips", "LASSO", "Ensemble", "SeasonalMean"]
targets = ["ea_headline", "ea_core", "tr_headline"]
fig, axes = plt.subplots(2, 2, figsize=(12, 7.6))
for ax, h in zip(axes.ravel(), [1, 3, 6, 12], strict=True):
    matrix = np.array(
        [
            [
                scores[(scores.target == target) & (scores.model == model) & (scores.horizon == h)]
                .iloc[0]
                .relative_rmse
                for model in models
            ]
            for target in targets
        ]
    )
    ax.imshow(
        matrix,
        cmap=LinearSegmentedColormap.from_list("loss", [PALETTE[2], "white", PALETTE[3]]),
        vmin=0.5,
        vmax=2,
        aspect="auto",
    )
    for i, target in enumerate(targets):
        for j, model in enumerate(models):
            r = scores[
                (scores.target == target) & (scores.model == model) & (scores.horizon == h)
            ].iloc[0]
            ax.text(
                j,
                i,
                f"{r.relative_rmse:.2f}\n[{r.lo90:.2f},{r.hi90:.2f}]",
                ha="center",
                va="center",
                fontsize=6.5,
            )
    ax.set(
        xticks=range(len(models)),
        xticklabels=["RW", "AO", "AR", "BVAR", "Phillips", "Lasso", "Ensemble", "Seasonal\nmean"],
        yticks=range(3),
        yticklabels=["EA headline", "EA core", "TR"],
        title=f"Fixed target horizon h={h}",
    )
fig.suptitle("Publication-lag-adjusted y/y inflation: RMSE relative to RW")
fig.text(
    0.02,
    0.015,
    "Assumed prices t+1 / unemployment t+2; latest vintage. Brackets: 90% paired loss-block intervals, not prediction intervals.",
    fontsize=8,
)
fig.tight_layout(rect=(0, 0.05, 1, 0.95))
fig.savefig(root / "figures/forecast_heatmap.png", dpi=250)
plt.close(fig)
fig, ax = plt.subplots(figsize=(10, 3.6))
h = 1
matrix = np.array(
    [
        [
            scores[(scores.target == target) & (scores.model == model) & (scores.horizon == h)]
            .iloc[0]
            .relative_rmse
            for model in models
        ]
        for target in targets
    ]
)
ax.imshow(
    matrix,
    cmap=LinearSegmentedColormap.from_list("loss", [PALETTE[2], "white", PALETTE[3]]),
    vmin=0.7,
    vmax=1.8,
    aspect="auto",
)
for i, target in enumerate(targets):
    for j, model in enumerate(models):
        r = scores[
            (scores.target == target) & (scores.model == model) & (scores.horizon == h)
        ].iloc[0]
        ax.text(
            j,
            i,
            f"{r.relative_rmse:.2f}\n[{r.lo90:.2f},{r.hi90:.2f}]",
            ha="center",
            va="center",
            fontsize=8,
        )
ax.set(
    xticks=range(8),
    xticklabels=["RW", "AO", "AR", "BVAR", "Phillips", "Lasso", "Ensemble", "Seasonal\nmean"],
    yticks=range(3),
    yticklabels=["EA headline", "EA core", "TR headline"],
    title="One-month fixed targets under publication lags",
)
fig.text(
    0.02,
    0.01,
    "RW=1; 90% paired-block loss intervals. Same target dates and assumed availability calendar; latest vintage.",
    fontsize=8,
)
fig.tight_layout(rect=(0, 0.1, 1, 1))
fig.savefig(root / "figures/headline.png", dpi=300)
fig.savefig(root / "figures/headline.pdf")
plt.close(fig)


def row(target, model, h=1):
    return scores[(scores.target == target) & (scores.model == model) & (scores.horizon == h)].iloc[
        0
    ]


core = row("ea_core", "BVAR")
head = row("ea_headline", "Ensemble")
tr = row("tr_headline", "SeasonalMean")
tr12 = row("tr_headline", "BVAR", 12)
tr12ar = row("tr_headline", "AR", 12)
n = now[(now.model == "DFM") & (now.info_month == 3) & (~now.exclude_covid)].iloc[0]
nx = now[(now.model == "DFM") & (now.info_month == 3) & now.exclude_covid].iloc[0]
findings = [
    f"The earlier core-inflation gain does not survive the assumed publication calendar: EA core BVAR/RW RMSE is {core.relative_rmse:.3f} (90% loss interval {core.lo90:.3f}, {core.hi90:.3f}).",
    f"The EA headline ensemble/RW ratio is {head.relative_rmse:.3f} ({head.lo90:.3f}, {head.hi90:.3f}). The fixed seasonal-mean benchmark has a Türkiye one-month ratio of {tr.relative_rmse:.3f} ({tr.lo90:.3f}, {tr.hi90:.3f}); this uncertain point gain is not a general forecasting result. At twelve months, Türkiye BVAR/AR ratios are {tr12.relative_rmse:.3f}/{tr12ar.relative_rmse:.3f}; the 2021–23 inflation surge complicates prediction without identifying its separate causal contribution.",
    f"Inherited Germany nowcasts remain sample-sensitive: month-three DFM/bridge RMSE is {n.relative_rmse:.3f} ({n.lo90:.3f}, {n.hi90:.3f}) overall, versus {nx.relative_rmse:.3f} ({nx.lo90:.3f}, {nx.hi90:.3f}) excluding 2020Q1–2021Q2. GDP is q/q log growth, not annualised.",
]
question = (
    "Do fixed inflation models improve on simple rules when we respect assumed publication delays?"
)
method = "We forecast fixed year-on-year targets using final prices with a one-month delay and unemployment with a two-month delay. We retain all model settings and compare RW, AO and one fixed seasonal-mean benchmark outside the ensemble. We report paired loss intervals and fixed-bandwidth DM-HLN tests, alongside inherited German GDP nowcasts."
limitations = [
    "Latest-vintage publication masks do not recreate historical vintages.",
    "The conservative unemployment mask disadvantages unemployment-based models.",
    "HAC and loss-block intervals remain conditional, exploratory approximations.",
    "Seasonal means attenuate past exceptional movements and may lag regime changes.",
    "GDP rankings remain pandemic-sensitive and some fits did not converge.",
]
technical = f"""V3 publication-lag-adjusted, latest-vintage pseudo-real-time evaluation. Origins are end-of-month o; final prices for t assumed available at end t+1, unemployment end t+2. These are assumptions, not actual historical calendars. Targets remain o+h. Target-only models use o−1 and AR h+1 steps; complete-panel BVAR/Phillips/Lasso use o−2 and h+2 steps. The original equal-weight RW/AR/BVAR/Phillips/Lasso ensemble is unchanged; SeasonalMean is excluded. Full model settings are frozen in docs/V3_PROTOCOL.md; no evaluation tuning.

SeasonalMean predicts each unpublished log price change with exactly three most recent published same-calendar-month changes, then compounds the twelve-month sum. Forecasts never enter the averaging history. It is missing if any required three-observation history is unavailable. All target/horizon comparisons retain {int(core.n)} common target dates, {core["first"]}–{core["last"]}; exclusions are recorded in results/v3_evaluation_dates.json. The seasonally naive rule reproduces y/y RW and therefore is not added separately.

DM-HLN retains squared errors, HLN correction and Student-t reference. V3 Bartlett L=h+11 includes autocovariances through L; legacy L=h−1 is also computed on identical V3 errors. results/v3_inference_attribution.csv retains original V2 p-values and both rules on unchanged V2 error pairs, separating information-set effects from inference-only effects. Fixed bandwidth does not guarantee complete dependence coverage. Paired circular blocks of length12,499 draws,seed20261007 are unchanged; intervals concern evaluation loss and are not prediction intervals or validated by HAC changes. No multiplicity or nested-model correction is claimed.

EA core BVAR relative RMSE {core.relative_rmse:.6f}, DM-HLN p={core.dm_pvalue:.6f}; EA headline ensemble {head.relative_rmse:.6f}, p={head.dm_pvalue:.6f}. At h12 Türkiye BVAR/RW is {tr12.relative_rmse:.6f}; AR/RW is {tr12ar.relative_rmse:.6f}; the pattern is compatible with inflation-regime adaptation difficulty but does not identify a separate causal contribution from the 2021–23 surge. Inherited m/m tables and GDP nowcasts are unchanged; full/ex-pandemic month-three GDP ratios remain {n.relative_rmse:.6f}/{nx.relative_rmse:.6f}. Source/run manifests distinguish new inflation forecasts from inherited nowcasts and V2 errors.

Limitations and future work: archived historical vintages and first-release targets; dependence/ACF and full-chain bootstrap validation; predeclared multiple/nested-model inference; rolling windows, priors and training-only combinations; original-target AO replication; GDP AR/mean baselines and indicator information audits; quarterly crisis-loss accounting; convergence-path diagnostics and operational failure rules; properly calibrated predictive distributions. These substantive review findings are deferred, not implemented in V3. No new observations or vintages were acquired."""
sources = "Eurostat/CBRT-TURKSTAT frozen series; V3 aggregate outputs and inherited nowcast_scores.csv. Atkeson & Ohanian (2001), DOI10.21034/qr.2511."
write_note(
    root,
    "Inflation forecasts with publication lags",
    question,
    method,
    findings,
    limitations,
    technical,
    sources,
)
(root / "results/findings.json").write_text(json.dumps(findings, indent=2) + "\n")
(root / "results/findings.md").write_text("\n".join("- " + f for f in findings) + "\n")
(root / "README.md").write_text(
    "# inflation-forecast-nowcast\n\n"
    + question
    + "\n\n"
    + method
    + "\n\n![Headline](figures/headline.png)\n\n[Policy note](report/policy_note.pdf) · [Technical working paper](report/technical_report.pdf)\n\n## Findings\n\n"
    + "\n".join("- " + f for f in findings)
    + "\n\n## Reproduce\n\n`make setup`; `make v3` uses frozen local inputs only; `make v3-outputs report` renders saved results. `make test lint`; offline `make quick`. Original acquisition/estimation commands remain for historical reconstruction, but are not used by V3.\n\n## Technical notes\n\n"
    + technical.split("Limitations and future work:")[0]
    + "\n\n## Limitations and future work\n\n"
    + technical.split("Limitations and future work:")[1]
    + "\n\n## Licence and author\n\nMIT code; data retain source terms and are not redistributed. Hakan Zeki Gülmez | [GitHub](https://github.com/hakangulmez) | [LinkedIn](https://www.linkedin.com/in/hakan-zeki-g%C3%BClmez-088700180/)\n"
)
for name in [
    "inflation_scores_yoy",
    "inflation_scores",
    "v3_inference_attribution",
    "v3_cutoff_summary",
]:
    t = pd.read_csv(root / "results" / (name + ".csv"))
    (root / "results" / (name + ".md")).write_text(
        "# V3 "
        + name
        + "\n\n"
        + "\n".join(
            [
                "| " + " | ".join(t.columns) + " |",
                "| " + " | ".join(["---"] * len(t.columns)) + " |",
            ]
            + ["| " + " | ".join(map(str, x)) + " |" for x in t.itertuples(index=False, name=None)]
        )
        + "\n"
    )
fig, ax = plt.subplots(figsize=(4, 4), dpi=300)
for i, target in enumerate(targets):
    r = row(target, "BVAR")
    ax.errorbar(
        r.relative_rmse,
        i,
        xerr=[[r.relative_rmse - r.lo90], [r.hi90 - r.relative_rmse]],
        fmt="o",
        color=PALETTE[i],
        capsize=4,
    )
ax.axvline(1, color=".5", ls="--")
ax.set(
    yticks=range(3),
    yticklabels=["EA headline", "EA core", "Türkiye"],
    xlabel="BVAR/RW RMSE, h=1",
    title="Publication lags change the comparison",
)
fig.text(
    0.03,
    0.01,
    "90% paired loss-block intervals. Latest vintage;\nassumed price t+1/unemployment t+2; fixed settings.",
    fontsize=7,
)
fig.tight_layout(rect=(0, 0.11, 1, 1))
fig.savefig(root / "figures/linkedin/headline.png", dpi=300)
plt.close(fig)
(root / "figures/linkedin/summary.txt").write_text(" ".join(findings) + "\n")
inputs = [
    "inflation_scores.csv",
    "v3_inference_attribution.csv",
    "nowcast_scores.csv",
    "v3_inflation_manifest.json",
]
(root / "results/policy_note_lineage.json").write_text(
    json.dumps(
        dict(
            inputs={
                "results/" + n: hashlib.sha256((root / "results" / n).read_bytes()).hexdigest()
                for n in inputs
            },
            render_only=True,
            paid_calls=0,
        ),
        indent=2,
    )
    + "\n"
)
print(json.dumps(findings))
