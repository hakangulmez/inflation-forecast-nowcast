# M2 decisions — overnight draft

G0/G2 human stops overridden by the approved overnight spec. Design written before acquisition.

Preflight verified series selectors govern; no PMI. August DE IP is missing and stays missing. Latest-vintage pseudo-real-time only, with fixed simulated lags (two months for monthly activity/unemployment and quarterly GDP, zero for ESI). GDP release dates use quarter end plus two months; current-quarter target always withheld.

Minimum-first includes all inflation models plus bridge, U-MIDAS and DFM. BVAR equations use independent conjugate normal-inverse-gamma priors: conditional AR coefficients mean zero, variance sigma_y² lambda²/(lag² sigma_x²), own/cross .2/.1, diffuse intercept, shape a0=3 and scale b0=2 sigma_y². Posterior means suffice for point forecasts; no test-period tuning. Twelve lags. This is a diagonal-equation prior, not a full inverse-Wishart covariance model.

Inflation forecast scoring uses target months from January 2015, horizons 1/3/6/12, origin-bounded estimation; NSA EA/TR inflation seasonality is learned by AR/BVAR lags or direct-model month indicators. RW is deliberately unadjusted. Equal-weight ensemble includes AR/BVAR/Phillips/LASSO/RW. LASSO training-only scaling, alpha .05.

Bridge and U-MIDAS use the same ragged pattern in each historical training quarter. Missing design slots use training design means within the estimator only; observed source values are never filled or interpolated. A small fixed .01 ridge penalty resolves collinear slot designs. DFM one AR(1) factor with AR(1) idiosyncratic terms, maximum 100 EM iterations, tolerance 1e-5; non-convergence explicitly counted, not silently called converged.

Loss uncertainty uses paired circular blocks (12 monthly observations; 4 quarters), 499 draws, 90% pointwise intervals. DM two-sided, Bartlett bandwidth h-1 and HLN small-sample correction; many comparisons are exploratory, without multiplicity correction. Evaluation is conditional on fixed fitted forecasts.

Data downloads succeeded on 7 October 2026; total private source/processed cache approximately 328 KiB before model outputs. Output manifests bind every source-series checksum and estimator-code hash.

Audit correction before release: GDP for Q4 is available in February under the two-month release convention (test expectation corrected). DFM nowcasts use origin-bounded **smoothed** state predictions, allowing all released monthly information through the origin, including the after-quarter information month. No observations beyond the origin enter the smoother. EM convergence is computed from the final relative likelihood change because statsmodels EM does not provide a `converged` flag.


## V2 target and benchmark revision, 7 October 2026

Primary point y/y target and the monthly Atkeson-Ohanian adaptation are defined exactly in docs/V2_TARGET.md. Source observations, model hyperparameters and nowcasts unchanged; original m/m table retained as secondary. DM-HLN rerun against both RW and AO for h1/3/6/12. Overlap-induced serial dependence and multiple testing are explicit limitations. GDP units:100 delta log(real GDP), q/q growth, not annualised. Primary forecast manifest is results/yoy_manifest.json; original results/manifest.json continues to bind inherited m/m and GDP results. Official AO study summary: https://www.minneapolisfed.org/article/2001/the-magics-gone .

## V3 benchmark and information-set decision — 7 October 2026

The fixed choices in [V3_PROTOCOL.md](docs/V3_PROTOCOL.md) precede all V3 fits/results. Inflation evaluation now applies assumed end-of-month publication delays (prices one month, unemployment two months), preserves target o+h and fits the extra forward steps from each effective cutoff. This is publication-lag-adjusted, latest-vintage pseudo-real-time evaluation, not reconstructed historical vintages.

We add one assumption-based SeasonalMean benchmark: exactly three most recent published same-calendar-month log changes, correctly compounded. Exceptional movements are attenuated by averaging, not eliminated; a changed inflation regime can make the rule slow to adapt. We keep RW/AO and exclude SeasonalMean from the unchanged ensemble. We do not add seasonal-naive separately: repeating the latest published log change for each calendar month makes every twelve-month predicted log sum equal the latest observed twelve-month sum, hence reproduces y/y RW even when the denominator is unpublished or the target is more than twelve months after the latest observation. Tests cover this identity and the explicit missing-history rule. Bartlett L=h+11 is fixed independently of outcomes; original bandwidth p-values are retained for attribution of information-set versus inference changes.
