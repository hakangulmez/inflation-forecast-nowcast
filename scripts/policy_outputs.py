# ruff: noqa: E501
"""Render the employer note from saved aggregate results; no fitting or resampling."""

import hashlib
import json
from pathlib import Path

import pandas as pd
from policy import write_note


def emit_policy(root, scores, now, manifest):
    ea = scores.query('target=="ea_headline" and model=="BVAR" and horizon==1').iloc[0]
    tr = scores.query('target=="tr_headline" and model=="BVAR" and horizon==1').iloc[0]
    now3 = now[(now.model == "DFM") & (now.info_month == 3) & (~now.exclude_covid)].iloc[0]
    now3_ex = now[(now.model == "DFM") & (now.info_month == 3) & now.exclude_covid].iloc[0]
    tr_bvar12 = scores.query('target=="tr_headline" and model=="BVAR" and horizon==12').iloc[0]
    tr_ar12 = scores.query('target=="tr_headline" and model=="AR" and horizon==12').iloc[0]
    core = scores.query('target=="ea_core" and model=="BVAR" and horizon==1').iloc[0]
    ensemble = scores.query('target=="ea_headline" and model=="Ensemble" and horizon==1').iloc[0]
    findings = [
        f"EA core inflation: the Bayesian model's one-month error is {core.relative_rmse:.2f} times the random walk (90% interval {core.lo90:.2f}, {core.hi90:.2f}), a statistically clearer gain.",
        f"EA headline inflation: the ensemble's error is {ensemble.relative_rmse:.2f} times the random walk (90% interval {ensemble.lo90:.2f}, {ensemble.hi90:.2f}); the formal one-month headline and Türkiye gains remain statistically unclear, consistent with the difficulty of beating simple benchmarks (Atkeson and Ohanian, 2001). At twelve months, Türkiye BVAR and AR errors are {tr_bvar12.relative_rmse:.2f} and {tr_ar12.relative_rmse:.2f} times the random walk, consistent with difficulty adapting to the 2021-23 inflation surge.",
        f"Germany: at month three, DFM/bridge RMSE is {now3.relative_rmse:.3f} (90% interval {now3.lo90:.3f}, {now3.hi90:.3f}) in the full sample, versus {now3_ex.relative_rmse:.3f} ({now3_ex.lo90:.3f}, {now3_ex.hi90:.3f}) excluding 2020Q1-2021Q2. The pandemic quarters drive the full-sample result; GDP is q/q log growth, not annualised.",
    ]
    (root / "results/findings.json").write_text(json.dumps(findings, indent=2))
    (root / "results/findings.md").write_text("\n".join("- " + x for x in findings) + "\n")

    question = "Do fixed statistical models improve year-on-year inflation forecasts over simple benchmarks, and does monthly information help nowcast German growth?"
    method = "We forecast year-on-year inflation one, three, six and twelve months ahead using only information available at each simulated origin. We compare fixed models with a random walk and the annualised average of the last twelve monthly inflation rates. We keep the existing German GDP nowcasts and measure forecast errors with paired-block uncertainty and corrected loss comparisons."
    limitations = [
        "Inputs are revised latest vintages with simulated release lags.",
        "Loss tests are exploratory and not adjusted for multiple comparisons.",
        "Overlapping y/y observations complicate loss-test inference.",
        "The monthly AO adaptation is not a compounded annual rate.",
        "Some GDP factor-model fits did not converge.",
    ]
    annual = pd.read_csv(root / "results/inflation_scores_yoy.csv")
    ao_ea = annual.query(
        'target=="ea_headline" and model=="BVAR" and benchmark=="AO" and horizon==1'
    ).iloc[0]
    ao_tr = annual.query(
        'target=="tr_headline" and model=="BVAR" and benchmark=="AO" and horizon==1'
    ).iloc[0]
    technical = f"""Primary target is point y/y inflation100(P_t/P_(t-12)-1), evaluated at origin+h for h1,3,6,12. RW carries forward the origin's y/y rate. AO is12 times the arithmetic mean of the last12 simple m/m percentage rates, held constant at all horizons: the requested monthly adaptation, not the original paper's next-year-average target, nor compounded y/y. Simple monthly inflation and y/y differ markedly at high inflation. Core BVAR/RW relative RMSE is {core.relative_rmse:.6f} (90% {core.lo90:.6f},{core.hi90:.6f}, DM-HLN p={core.dm_pvalue:.6f}); headline ensemble/RW is {ensemble.relative_rmse:.6f} (90% {ensemble.lo90:.6f},{ensemble.hi90:.6f}, p={ensemble.dm_pvalue:.6f}). A loss-block interval below one and a marginal formal DM result are different inference summaries; report both without selecting settings. One-month BVAR/RW RMSE ratios are EA{ea.relative_rmse:.6f} (90% paired-block {ea.lo90:.6f},{ea.hi90:.6f}) and TR{tr.relative_rmse:.6f} ({tr.lo90:.6f},{tr.hi90:.6f}); BVAR/AO ratios are EA{ao_ea.relative_rmse:.6f} (p={ao_ea.dm_pvalue:.6f}) and TR{ao_tr.relative_rmse:.6f} (p={ao_tr.dm_pvalue:.6f}). Poor AO performance at high inflation should not be read as evidence of causality or operational forecast quality.

    All model hyperparameters retained: AR BIC<=12 on training sample, BVAR p12/own0.2/cross0.1, Lasso alpha0.05/training scaling, original direct Phillips equation and original five-component ensemble without AO. No evaluation tuning. Target months January2015-August2026 with140 observations per target/horizon/model; expanding origin fits. results/inflation_scores_yoy.csv contains both benchmarks and DM-HLN results; results/inflation_scores_mm.csv preserves the original NSA m/m comparison as secondary. Primary alias results/inflation_scores.csv uses RW-relative y/y scores. Original manifest remains immutable for inherited nowcasts/m/m; yoy_manifest.json binds new code, same source hashes and inherited manifest hash.

    DM-HLN uses h-1 Bartlett covariance and Student-t p-values as before; y/y overlap can leave dependence beyond this lag, so significance is provisional. 499 paired circular12-month blocks, seed20261007; bands describe evaluation-loss uncertainty, not prediction intervals or parameter-selection uncertainty. Multiple model/horizon tests have no multiplicity adjustment. Benchmark comparisons use matched dates, never future observations; all seasonal indicators are known calendar information.

    GDP target is100 delta log(real GDP index): q/q log growth in percentage points, NOT annualised (no multiplication by4). No nowcast refit in V2. The retained dynamic-factor model has {manifest["dfm_converged"]} converged fits of {manifest["dfm_total"]}; unconverged predictions remain flagged, and matched convergence-only sensitivity plus COVID exclusion are retained. Latest-vintage pseudo-real-time cannot undo revisions. Source IP August2026 is genuinely missing, never interpolated. Bridge/UMIDAS training design means are model assumptions; factor smoothing uses only origin-bounded masked inputs. Target-quarter GDP is always hidden; prior GDP must meet release masks.

    References: Atkeson & Ohanian(2001), verified publisher DOI https://doi.org/10.21034/qr.2511 ; Harvey, Leybourne & Newbold(1997),10.1016/S0169-2070(96)00719-4; Litterman(1986),10.1080/07350015.1986.10509491; Banbura & Modugno(2014),10.1002/jae.2306."""
    technical = "\n\n".join(paragraph.strip() for paragraph in technical.split("\n\n"))
    technical += f"\n\nMonth-three DFM/bridge relative RMSE: full sample {now3.relative_rmse:.6f} (90% {now3.lo90:.6f}, {now3.hi90:.6f}; n={int(now3.n)}); excluding 2020Q1-2021Q2 {now3_ex.relative_rmse:.6f} (90% {now3_ex.lo90:.6f}, {now3_ex.hi90:.6f}; n={int(now3_ex.n)}). The exclusion is the predeclared retained-score sensitivity, not a refit. The pandemic quarters drive the reversal in sample RMSE rankings. Twelve-month Türkiye BVAR/RW and AR/RW RMSE ratios are {tr_bvar12.relative_rmse:.6f} (90% {tr_bvar12.lo90:.6f}, {tr_bvar12.hi90:.6f}) and {tr_ar12.relative_rmse:.6f} (90% {tr_ar12.lo90:.6f}, {tr_ar12.hi90:.6f}). Linking this horizon pattern to the 2021-23 inflation surge is descriptive; the aggregate scores do not identify that episode's separate contribution or a causal mechanism."
    sources = "Sources: Eurostat EA21/Germany and CBRT-TURKSTAT. Author calculations; results/inflation_scores_yoy.csv and unchanged nowcast_scores.csv. Atkeson & Ohanian (2001), DOI:10.21034/qr.2511."
    write_note(
        root,
        "Inflation forecasts: a fairer benchmark test",
        question,
        method,
        findings,
        limitations,
        technical,
        sources,
    )
    (root / "README.md").write_text(
        "# inflation-forecast-nowcast\n\n"
        + question
        + "\n\n"
        + method
        + "\n\n![Headline](figures/headline.png)\n\n[Read the two-page policy note (PDF)](report/policy_note.pdf) · [Technical working paper (PDF)](report/technical_report.pdf)\n\n## Findings\n\n"
        + "\n".join("- " + x for x in findings)
        + "\n\n## Reproduce\n\n`make setup all` with EVDS_API_KEY in local .env; `make quick` is isolated/offline; `make test lint`. For only V2 forecasts: scripts/yoy.py. No raw redistribution.\n\n## Technical notes\n\n"
        + technical
        + "\n\n## Licence\n\nCode is MIT-licensed; third-party source data retain their original terms and are not included. Proposed publication files are listed in docs/PUBLISH_CHECKLIST.md; nothing has been published.\n\nHakan Zeki Gulmez | [GitHub](https://github.com/hakangulmez) | [LinkedIn](https://www.linkedin.com/in/hakan-zeki-g%C3%BClmez-088700180/)\n"
    )
    # Preserve the separate working-paper build documentation in the README.
    with (root / "README.md").open("a") as stream:
        stream.write(
            "\n## Technical working paper\n\nThe academic paper documents the exact implemented equations, aggregate results, declared robustness checks and diagnostic appendices. `make report` compiles its LaTeX source in `report/technical/` from existing G3 outputs without estimation; see [build instructions](report/technical/README.md). `make policy-note` retains the shorter note renderer.\n"
        )
    (root / "figures/linkedin/summary.txt").write_text(" ".join(findings) + "\n")
    inputs = [
        "inflation_scores.csv",
        "inflation_scores_yoy.csv",
        "nowcast_scores.csv",
        "manifest.json",
    ]
    lineage = {
        "inputs": {
            "results/" + name: hashlib.sha256((root / "results" / name).read_bytes()).hexdigest()
            for name in inputs
        },
        "nowcast_month3": {"full": now3.to_dict(), "exclude_2020Q1_2021Q2": now3_ex.to_dict()},
        "tr_h12": {"BVAR": tr_bvar12.to_dict(), "AR": tr_ar12.to_dict()},
        "estimation": False,
        "paid_calls": 0,
    }
    (root / "results/policy_note_lineage.json").write_text(json.dumps(lineage, indent=2) + "\n")
    print(json.dumps(dict(findings=findings, pages_expected=2)))


def main():
    root = Path.cwd()
    scores = pd.read_csv(root / "results/inflation_scores.csv")
    now = pd.read_csv(root / "results/nowcast_scores.csv")
    manifest = json.loads((root / "results/manifest.json").read_text())
    emit_policy(root, scores, now, manifest)


if __name__ == "__main__":
    main()
