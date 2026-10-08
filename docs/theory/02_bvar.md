# BVAR and the Minnesota prior

Status: draft for review

## Intuition

An unrestricted VAR can require many coefficients relative to the observed sample. Bayesian shrinkage trades some potential misspecification for less estimation variance. A Minnesota prior shrinks longer lags more strongly and expresses beliefs about own versus other-variable dynamics. Forecasting skill is empirical; shrinkage does not identify structural shocks.

## Model

$Y=X B+U$. For equation j, $\beta_j|\sigma_j^2\sim N(b_{0j},\sigma_j^2 V_{0j})$ and $\sigma_j^2\sim IG(a_0,b_0)$. The posterior mean is $(X^\prime X+V_{0j}^{-1})^{-1}(X^\prime y_j+V_{0j}^{-1}b_{0j})$. A lag coefficient prior variance scales as $\lambda^2/(l^2 s_x^2)$ conditionally on outcome variance.

## Assumptions and interpretation

The matrix formula separates information from observed data and prior precision. Smaller prior variance produces stronger shrinkage. A diffuse intercept allows a nonzero long-run mean even with a zero coefficient prior. Own and cross shrinkage need not be equal. Inflation growth need not receive the unit-root prior commonly used for persistent levels. Priors should match transformations and be declared before evaluation.

## Application and limits

This project uses independent conjugate equations and fixed hyperparameters, not a joint inverse-Wishart covariance prior. It recursively forecasts unemployment together with inflation; future observed unemployment is never supplied. Training-only innovation scales keep prior calibration inside the expanding window. A posterior-mean recursive path is a point forecast, not a simulated predictive distribution. A favourable test score cannot justify retroactively changing prior tightness.

```{=typst}
#pagebreak()
```

## Exam questions and answers

### 1. Why shrink a VAR?

**Answer.** To reduce estimation variance in a parameter-rich model.

### 2. What does lag decay do?

**Answer.** It imposes stronger shrinkage on more distant dynamics.

### 3. Why scale by predictor innovation variance?

**Answer.** To make prior tightness less sensitive to measurement units.

### 4. Does this model identify policy causality?

**Answer.** No; it is a predictive reduced-form model.

### 5. What is forbidden tuning?

**Answer.** Choosing hyperparameters using the held-out evaluation losses and then presenting them as prespecified.

## Reasoning exercise

An analyst switches the inflation prior mean from zero to one after observing poor annual-horizon forecasts. Is this an innocuous implementation correction? Answer: the change alters the predictive specification and is outcome-informed tuning. A unit-root prior can be natural for persistent levels but is a distinct assumption for monthly inflation. Keep the original result, describe the alternative as exploratory and evaluate it on new targets. Own and cross lag shrinkage should be justified by scale and persistence, with innovation variances estimated within training windows. Posterior shrinkage reduces variance at the possible cost of bias; it guarantees neither superior forecasts nor causal identification.

## Verified reference

https://doi.org/10.1080/07350015.1986.10509491
