# Provenance and reproduction

This document records the forecast vintages, target definitions, inference rules and limits of empirical reproduction. [Methods guide](METHODS.md) links the successive design records; source terms are in [DATA.md](../DATA.md).

## Empirical reruns

`make data` acquires official Eurostat and EVDS series using an ignored .env containing EVDS_API_KEY. `make all` runs the original unmasked empirical pipeline and overwrites aggregate outputs in that working checkout. Run it in a separate clone. The publication-lag-adjusted inflation evaluation uses `make v3` after runtime acquisition and requires the documented input hashes; a refreshed source vintage must not silently stand in for those inputs. The GDP nowcasts are separately preserved. No row-level forecasts or source observations are redistributed.


## Research lineage and detailed disclosures

V3 publication-lag-adjusted, latest-vintage pseudo-real-time evaluation. Origins are end-of-month o; final prices for t assumed available at end t+1, unemployment end t+2. These are assumptions, not actual historical calendars. Targets remain o+h. Target-only models use o−1 and AR h+1 steps; complete-panel BVAR/Phillips/Lasso use o−2 and h+2 steps. The original equal-weight RW/AR/BVAR/Phillips/Lasso ensemble is unchanged; SeasonalMean is excluded. Full model settings are frozen in docs/V3_PROTOCOL.md; no evaluation tuning.

SeasonalMean predicts each unpublished log price change with exactly three most recent published same-calendar-month changes, then compounds the twelve-month sum. Forecasts never enter the averaging history. It is missing if any required three-observation history is unavailable. All target/horizon comparisons retain 140 common target dates, 2015-01–2026-08; exclusions are recorded in results/v3_evaluation_dates.json. The seasonally naive rule reproduces y/y RW and therefore is not added separately.

DM-HLN retains squared errors, HLN correction and Student-t reference. V3 Bartlett L=h+11 includes autocovariances through L; legacy L=h−1 is also computed on identical V3 errors. results/v3_inference_attribution.csv retains original V2 p-values and both rules on unchanged V2 error pairs, separating information-set effects from inference-only effects. Fixed bandwidth does not guarantee complete dependence coverage. Paired circular blocks of length 12,499 draws, seed 20261007 are unchanged; intervals concern evaluation loss and are not prediction intervals or validated by HAC changes. No multiplicity or nested-model correction is claimed.

EA core BVAR relative RMSE 1.076804, DM-HLN p=0.092383; EA headline ensemble 1.070707, p=0.304916. At h12 Türkiye BVAR/RW is 2.389319; AR/RW is 1.949710; the pattern is compatible with inflation-regime adaptation difficulty but does not identify a separate causal contribution from the 2021–23 surge. Inherited m/m tables and GDP nowcasts are unchanged; full/ex-pandemic month-three GDP ratios remain 1.552371/0.822191. Source/run manifests distinguish new inflation forecasts from inherited nowcasts and V2 errors.



## Limitations and future work

 archived historical vintages and first-release targets; dependence/ACF and full-chain bootstrap validation; predeclared multiple/nested-model inference; rolling windows, priors and training-only combinations; original-target AO replication; GDP AR/mean baselines and indicator information audits; quarterly crisis-loss accounting; convergence-path diagnostics and operational failure rules; properly calibrated predictive distributions. These substantive review findings are deferred, not implemented in V3. No new observations or vintages were acquired.

## Licence and author

MIT code; data retain source terms and are not redistributed. Hakan Zeki Gülmez | [GitHub](https://github.com/hakangulmez) | [LinkedIn](https://www.linkedin.com/in/hakan-zeki-g%C3%BClmez-088700180/)


## Public package reproduction boundary

`make setup test lint quick` checks implementations and synthetic examples. `REPORT_OFFLINE=1 make report` rebuilds the technical paper from saved aggregates after the Tectonic cache is populated. `make policy-note`, `make figures`, `make readme-numbers` and `make v3-outputs` also regenerate the README and other presentation files from an older embedded template; use a separate clone for these builds to preserve the current editorial text. `make all` remains the original unmasked empirical pipeline and overwrites output files; run it in a separate clone. Publication-masked re-estimation also requires exact source vintages and the earlier observation-level forecast pairs used for the HAC attribution calculation. Those pairs are not redistributed, so `make v3` is not advertised as a self-contained reconstruction of private run history. The empirical forecast code and complete aggregate diagnostics are included. No fresh empirical estimates were executed for publication.
