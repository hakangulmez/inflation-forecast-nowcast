# V2 primary target contract

Primary: point year-on-year inflation at origin+h, 100(P_t/P_(t-12)-1), percentage points, for h=1,3,6,12 months. Monthly origins and common target evaluation months from January 2015 are retained.

RW: the origin's observed year-on-year rate at all horizons. AO: 12 times the arithmetic mean of the last 12 observed simple monthly percentage changes, i.e. their sum. This explicitly requested monthly adaptation of Atkeson-Ohanian is held fixed at the origin at all horizons; it differs from compounded annual inflation and from their original next-year average target. Neither benchmark sees future data.

All model settings remain fixed: AR BIC through 12, BVAR lag12 own0.2/cross0.1, direct Phillips specification, Lasso alpha0.05, and original five-component ensemble (no AO inclusion). Only the dependent inflation transformation changes. No hyperparameters selected on evaluation results.

Paired circular 12-month loss-block bootstrap, 499 draws, seed20261007; DM-HLN against both RW and AO at each horizon, h-1 Bartlett covariance and Student-t p-values; exploratory unadjusted multiple comparisons. Year-on-year overlapping observations can retain serial dependence beyond h-1, an inference limitation to document.

Preserve the original m/m table as secondary, and the GDP results without refitting. GDP is 100 log(Q_t/Q_(t-1)): q/q log growth, not annualised. Original run/source/code manifest stays as its immutable lineage; a separate V2 manifest binds new forecasts to the same source observations and current estimator code.

Reference: Atkeson and Ohanian (2001), Federal Reserve Bank of Minneapolis Quarterly Review 25(1), 2-11; https://www.minneapolisfed.org/article/2001/the-magics-gone (official research summary linking the study).
