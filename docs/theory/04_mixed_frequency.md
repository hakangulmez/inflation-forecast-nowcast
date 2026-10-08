# Mixed frequency, MIDAS and dynamic factors

Status: draft for review

## Intuition

Monthly indicators and quarterly GDP do not share a calendar. A nowcast asks what the available monthly releases imply for the still-unpublished quarter. Missing recent observations form a ragged edge. The correct procedure models this information set; interpolating unpublished observations pretends information exists.

## Model

A bridge uses $g_q=a+b^\prime\bar x_q+e_q$. U-MIDAS uses separate coefficients for month slots. A factor model writes $x_t=\Lambda f_t+\epsilon_t$, $f_t=A f_{t-1}+v_t$ with quarterly aggregation restrictions linking GDP to monthly latent growth.

## Assumptions and interpretation

A bridge aggregates monthly information, while an unrestricted MIDAS design retains within-quarter timing. Both need a rule for unavailable slots. State-space filtering and smoothing condition on released observations and can accommodate missing entries. Smoothing is legitimate for a nowcast if the entire supplied observation set is bounded by the origin; smoothing with later released information leaks the future.

## Application and limits

Fixed release delays are a transparent approximation, not a reconstructed calendar. Training GDP targets must also satisfy release timing. Convergence must be checked rather than inferred from a returned result object. One factor can miss sector-specific information; more factors increase variance and computational burden. COVID-sensitive GDP errors should be reported with a declared exclusion comparison, without choosing a preferred period after looking at scores.

```{=typst}
#pagebreak()
```

## Exam questions and answers

### 1. What is a ragged edge?

**Answer.** Different indicators end at different dates because releases have different delays or gaps.

### 2. How does U-MIDAS differ from a bridge?

**Answer.** It estimates separate month-slot effects rather than a single within-quarter average.

### 3. When does smoothing leak?

**Answer.** When observations released after the simulated origin are included.

### 4. Why hide GDP after quarter end?

**Answer.** The quarter may have ended before its GDP estimate is published.

### 5. Does a finite forecast prove convergence?

**Answer.** No; likelihood and iteration diagnostics must be inspected.

## Reasoning exercise

A quarter has ended, but its GDP estimate is unpublished and the most recent industrial-production month is missing. Is filling that month by linear interpolation compatible with the information set? Answer: a future endpoint is unavailable, and a filled value would conceal genuine uncertainty. Keep the source gap, use a declared training-only design rule for bridge/MIDAS, and let the state-space model condition on the actually released series. An origin-bounded smoother may use all releases already available; it must not ingest later observations. Check numerical convergence separately from whether a finite nowcast was returned. Compare methods on common quarters and retain a declared pandemic sensitivity.

## Verified reference

https://doi.org/10.1002/jae.2306
