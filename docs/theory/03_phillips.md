# The Phillips curve as a forecasting equation

Status: draft for review

## Intuition

The Phillips curve connects inflation pressure to slack and expectations. A forecasting regression is a statistical approximation to this mechanism, not a structural policy experiment. Unemployment is one noisy measure of slack; supply shocks, imported prices and regime changes can dominate its relationship with inflation.

## Model

$\pi_{t+h}=a_h+b_h\pi_t+c_h u_t+\delta_h^\prime M_{t+h}+e_{t+h}$, where M contains known seasonal indicators. A direct h-step fit uses only target observations already available at the estimation origin.

## Assumptions and interpretation

Direct forecasting fits a separate equation for each horizon. This avoids recursively forecasting the entire system, but reduces usable training observations and can lose efficiency. The regression includes known target-month seasonality, not future realised slack. Conditional predictive association does not reveal the causal slope of a policy-induced unemployment change. Revised unemployment data can improve apparent historical performance.

## Application and limits

The benchmark in this project is intentionally parsimonious: inflation lag, observed unemployment and month indicators. It is not tuned until a desired coefficient sign appears. Employment coverage and seasonal adjustment are documented. If the required slack source fails verification, the model is omitted explicitly rather than silently replaced. Forecast evaluation and uncertainty remain separate from coefficient interpretation.

```{=typst}
#pagebreak()
```

## Exam questions and answers

### 1. Why can slack fail to predict inflation?

**Answer.** Supply shocks, expectations and regime changes may dominate.

### 2. What makes a direct forecast direct?

**Answer.** Its target is the outcome at the chosen horizon rather than a recursively iterated one-step prediction.

### 3. Can target-month seasonality be used?

**Answer.** Yes; the calendar is known at the forecast origin.

### 4. May future unemployment be used?

**Answer.** Only if a separate forecast is produced; the realised future value is unavailable.

### 5. Is a fitted unemployment coefficient a policy multiplier?

**Answer.** No; structural identification is absent.

## Reasoning exercise

A direct inflation forecast includes target-month unemployment downloaded from the final data vintage. Why is this invalid even if the target-month seasonal dummy is allowed? Answer: calendar seasonality is known at the origin, whereas realised future unemployment is not. Use the latest released unemployment or a separately estimated origin-bounded unemployment forecast. Then distinguish predictive evaluation from a structural Phillips-curve claim: an apparent slope may reflect supply shocks, expectations or simultaneous policy responses. Forecast the same target with the same information set for every model, state the benchmark and retain weak findings rather than altering the slack measure to obtain a preferred sign.

## Verified reference

https://www.princeton.edu/~mwatson/papers/Stock_Watson_JME_1999.pdf
