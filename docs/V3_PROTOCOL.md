# V3 fixed protocol — 7 October 2026

Frozen before fitting or inspecting V3 results. Evidence: economics review dated 7 October 2026; V2 snapshot `versions/v2-2026-10-07/HASHES.json`. Use only existing local processed price/unemployment series; no acquisition or vintage refresh. Original GDP nowcasts and secondary m/m estimates are inherited unchanged.

## Information calendar and targets

Origins are the last calendar day of month o. Assume final EA headline/core HICP and Türkiye CPI for t are available at end of t+1; unemployment at end of t+2. These are conservative assumptions, not historical release calendars. No flash series, interpolation, backfill or unpublished observations. Fixed targets remain o+h, h=1,3,6,12. Common target months: January 2015–August 2026, subject to explicit all-model finite-forecast intersection and exclusions. Preserve expanding training, original 60-month eligibility rule and all estimator settings. Multivariate BVAR/Phillips/Lasso truncate to the latest complete month o−2 and forecast h+2 steps; target-only RW/AO/AR use o−1 and AR forecasts h+1 steps. Record origin timestamp, price/unemployment cutoffs and model effective cutoff; gaps cause explicit missingness, never compression.

## Benchmark and inference rules

Retain RW and AO. Add SeasonalMean outside the existing equal-weight ensemble (RW, AR, BVAR, Phillips, LASSO). At each origin forecast unknown monthly log price changes using exactly the three most recent published observations for the same calendar month. Generated values never enter that averaging set. Three observations missing: benchmark missing with origins recorded. Construct y/y via 100[exp(sum of 12 monthly log changes ending at target)−1], including unpublished denominator cases. No separate seasonal-naive comparator: repeating the latest published same-month changes with compounding reproduces target-only RW, including beyond twelve months.

Preserve AR origin-only BIC cap12, BVAR lag12/own0.2/cross0.1/zero mean, Phillips design and Lasso alpha0.05/max_iter10000. No tuning or ensemble alteration. Evaluate every model/benchmark on a common set of dates within target/horizon. Squared-error DM-HLN retains correction and Student-t reference. V3 Bartlett bandwidth L=h+11 includes lags1..L. Also calculate legacy L=h−1 on identical V3 errors and both rules on frozen V2 errors; preserve original V2 p-values separately. No bandwidth selection. Paired circular loss bootstrap unchanged: block12, draws499, seed20261007; intervals describe evaluation loss, not future forecast uncertainty; HAC changes do not validate these intervals.

## Execution and scope

Seed20261007; deterministic estimators otherwise unchanged. Inflation run cap2h including any pilots; resumable per-origin caches with atomic writes and failures recorded. A timeout remains incomplete, without specification substitution. Source/protocol/frozen-input hashes bind every manifest. No paid APIs, publication or push. Historical vintages, alternate priors/windows/learners, multiple-test methods, new GDP benchmarks and probabilistic forecasts are deferred to Limitations and future work. Protocol amendments are allowed only for explicit user clarification before V3 results, with prior text preserved.
