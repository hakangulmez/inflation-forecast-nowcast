# Forecast evaluation and the DM test

Status: draft for review

## Intuition

A forecast must be assessed on observations that were not used to estimate or choose it. The origin names what could be known, and the target names what is predicted. An expanding window can still leak future information through preprocessing, revised data, variable selection or publication timing. An honest evaluation states exactly which information set is simulated.

## Model

$e_{t,h}=y_{t+h}-\hat y_{t+h|t}$; $RMSE_h=\sqrt{T^{-1}\sum_t e_{t,h}^2}$. The loss differential is $d_t=e_{A,t,h}^2-e_{B,t,h}^2$. The DM statistic divides its mean by the square root of its estimated long-run variance over T. The HLN multiplier is $\sqrt{(T+1-2h+h(h-1)/T)/T}$.

## Assumptions and interpretation

Loss sequences overlap at multi-step horizons, so their dependence cannot be ignored. A Bartlett HAC estimator and an explicit horizon bandwidth make the variance calculation reproducible. The small-sample correction is not a cure for misspecification, structural breaks or weak benchmark choices. A low p-value describes evidence against equal expected loss under maintained assumptions. It does not establish causality or guarantee future performance.

## Application and limits

Paired resampling keeps each model and benchmark error from the same target date together. Monthly blocks preserve short dependence. Confidence intervals for evaluation ratios differ from prediction intervals for a future observation. Comparing many targets and horizons creates multiplicity; exploratory tests must be labelled. A seasonal monthly target can make a last-observation benchmark weak, so interpret short and annual horizons separately.

```{=typst}
#pagebreak()
```

## Exam questions and answers

### 1. What must be excluded from training?

**Answer.** All observations and transformations using information unavailable at the origin.

### 2. Why pair bootstrap errors?

**Answer.** To preserve the dependence between model and benchmark losses for the same target.

### 3. What is the equal-loss null?

**Answer.** The expected loss differential is zero.

### 4. Does latest-vintage masking create real-time data?

**Answer.** No; revisions remain in the historical inputs.

### 5. Why distinguish evaluation and prediction intervals?

**Answer.** The first describes estimated performance uncertainty; the second describes an unknown future outcome.

## Reasoning exercise

An analyst chooses a forecasting model after inspecting the whole evaluation period and then applies the DM test to the same losses. Explain the problem and a repair. Answer: the loss sample has become a selection sample, so the ordinary comparison ignores model-search uncertainty. Reserve a later untouched period or use nested origin-bounded selection. At each origin, refit scaling and nuisance parameters using released training observations only. A negative loss differential favours model A under the stated loss, not every decision objective. Paired blocks preserve contemporaneous model/benchmark dependence; they do not repair an information leak.

## Verified reference

https://doi.org/10.1016/S0169-2070(96)00719-4
