"""Original two-page theory drafts, rendered from maintained Markdown."""

import subprocess
from pathlib import Path

root = Path.cwd()
target = root / "docs/theory"
target.mkdir(parents=True, exist_ok=True)
notes = [
    (
        "01_forecast_evaluation",
        "Forecast evaluation and the DM test",
        "A forecast must be assessed on observations that were not used to estimate or choose it. The origin names what could be known, and the target names what is predicted. An expanding window can still leak future information through preprocessing, revised data, variable selection or publication timing. An honest evaluation states exactly which information set is simulated.",  # noqa: E501
        r"$e_{t,h}=y_{t+h}-\hat y_{t+h|t}$; $RMSE_h=\sqrt{T^{-1}\sum_t e_{t,h}^2}$. The loss differential is $d_t=e_{A,t,h}^2-e_{B,t,h}^2$. The DM statistic divides its mean by the square root of its estimated long-run variance over T. The HLN multiplier is $\sqrt{(T+1-2h+h(h-1)/T)/T}$.",  # noqa: E501
        "Loss sequences overlap at multi-step horizons, so their dependence cannot be ignored. A Bartlett HAC estimator and an explicit horizon bandwidth make the variance calculation reproducible. The small-sample correction is not a cure for misspecification, structural breaks or weak benchmark choices. A low p-value describes evidence against equal expected loss under maintained assumptions. It does not establish causality or guarantee future performance.",  # noqa: E501
        "Paired resampling keeps each model and benchmark error from the same target date together. Monthly blocks preserve short dependence. Confidence intervals for evaluation ratios differ from prediction intervals for a future observation. Comparing many targets and horizons creates multiplicity; exploratory tests must be labelled. A seasonal monthly target can make a last-observation benchmark weak, so interpret short and annual horizons separately.",  # noqa: E501
        [
            (
                "What must be excluded from training?",
                "All observations and transformations using information unavailable at the origin.",
            ),
            (
                "Why pair bootstrap errors?",
                "To preserve the dependence between model and benchmark losses for the same target.",  # noqa: E501
            ),
            ("What is the equal-loss null?", "The expected loss differential is zero."),
            (
                "Does latest-vintage masking create real-time data?",
                "No; revisions remain in the historical inputs.",
            ),
            (
                "Why distinguish evaluation and prediction intervals?",
                "The first describes estimated performance uncertainty; the second describes an unknown future outcome.",  # noqa: E501
            ),
        ],
        "https://doi.org/10.1016/S0169-2070(96)00719-4",
    ),
    (
        "02_bvar",
        "BVAR and the Minnesota prior",
        "An unrestricted VAR can require many coefficients relative to the observed sample. Bayesian shrinkage trades some potential misspecification for less estimation variance. A Minnesota prior shrinks longer lags more strongly and expresses beliefs about own versus other-variable dynamics. Forecasting skill is empirical; shrinkage does not identify structural shocks.",  # noqa: E501
        r"$Y=X B+U$. For equation j, $\beta_j|\sigma_j^2\sim N(b_{0j},\sigma_j^2 V_{0j})$ and $\sigma_j^2\sim IG(a_0,b_0)$. The posterior mean is $(X^\prime X+V_{0j}^{-1})^{-1}(X^\prime y_j+V_{0j}^{-1}b_{0j})$. A lag coefficient prior variance scales as $\lambda^2/(l^2 s_x^2)$ conditionally on outcome variance.",  # noqa: E501
        "The matrix formula separates information from observed data and prior precision. Smaller prior variance produces stronger shrinkage. A diffuse intercept allows a nonzero long-run mean even with a zero coefficient prior. Own and cross shrinkage need not be equal. Inflation growth need not receive the unit-root prior commonly used for persistent levels. Priors should match transformations and be declared before evaluation.",  # noqa: E501
        "This project uses independent conjugate equations and fixed hyperparameters, not a joint inverse-Wishart covariance prior. It recursively forecasts unemployment together with inflation; future observed unemployment is never supplied. Training-only innovation scales keep prior calibration inside the expanding window. A posterior-mean recursive path is a point forecast, not a simulated predictive distribution. A favourable test score cannot justify retroactively changing prior tightness.",  # noqa: E501
        [
            ("Why shrink a VAR?", "To reduce estimation variance in a parameter-rich model."),
            ("What does lag decay do?", "It imposes stronger shrinkage on more distant dynamics."),
            (
                "Why scale by predictor innovation variance?",
                "To make prior tightness less sensitive to measurement units.",
            ),
            (
                "Does this model identify policy causality?",
                "No; it is a predictive reduced-form model.",
            ),
            (
                "What is forbidden tuning?",
                "Choosing hyperparameters using the held-out evaluation losses and then presenting them as prespecified.",  # noqa: E501
            ),
        ],
        "https://doi.org/10.1080/07350015.1986.10509491",
    ),
    (
        "03_phillips",
        "The Phillips curve as a forecasting equation",
        "The Phillips curve connects inflation pressure to slack and expectations. A forecasting regression is a statistical approximation to this mechanism, not a structural policy experiment. Unemployment is one noisy measure of slack; supply shocks, imported prices and regime changes can dominate its relationship with inflation.",  # noqa: E501
        r"$\pi_{t+h}=a_h+b_h\pi_t+c_h u_t+\delta_h^\prime M_{t+h}+e_{t+h}$, where M contains known seasonal indicators. A direct h-step fit uses only target observations already available at the estimation origin.",  # noqa: E501
        "Direct forecasting fits a separate equation for each horizon. This avoids recursively forecasting the entire system, but reduces usable training observations and can lose efficiency. The regression includes known target-month seasonality, not future realised slack. Conditional predictive association does not reveal the causal slope of a policy-induced unemployment change. Revised unemployment data can improve apparent historical performance.",  # noqa: E501
        "The benchmark in this project is intentionally parsimonious: inflation lag, observed unemployment and month indicators. It is not tuned until a desired coefficient sign appears. Employment coverage and seasonal adjustment are documented. If the required slack source fails verification, the model is omitted explicitly rather than silently replaced. Forecast evaluation and uncertainty remain separate from coefficient interpretation.",  # noqa: E501
        [
            (
                "Why can slack fail to predict inflation?",
                "Supply shocks, expectations and regime changes may dominate.",
            ),
            (
                "What makes a direct forecast direct?",
                "Its target is the outcome at the chosen horizon rather than a recursively iterated one-step prediction.",  # noqa: E501
            ),
            (
                "Can target-month seasonality be used?",
                "Yes; the calendar is known at the forecast origin.",
            ),
            (
                "May future unemployment be used?",
                "Only if a separate forecast is produced; the realised future value is unavailable.",  # noqa: E501
            ),
            (
                "Is a fitted unemployment coefficient a policy multiplier?",
                "No; structural identification is absent.",
            ),
        ],
        "https://www.princeton.edu/~mwatson/papers/Stock_Watson_JME_1999.pdf",
    ),
    (
        "04_mixed_frequency",
        "Mixed frequency, MIDAS and dynamic factors",
        "Monthly indicators and quarterly GDP do not share a calendar. A nowcast asks what the available monthly releases imply for the still-unpublished quarter. Missing recent observations form a ragged edge. The correct procedure models this information set; interpolating unpublished observations pretends information exists.",  # noqa: E501
        r"A bridge uses $g_q=a+b^\prime\bar x_q+e_q$. U-MIDAS uses separate coefficients for month slots. A factor model writes $x_t=\Lambda f_t+\epsilon_t$, $f_t=A f_{t-1}+v_t$ with quarterly aggregation restrictions linking GDP to monthly latent growth.",  # noqa: E501
        "A bridge aggregates monthly information, while an unrestricted MIDAS design retains within-quarter timing. Both need a rule for unavailable slots. State-space filtering and smoothing condition on released observations and can accommodate missing entries. Smoothing is legitimate for a nowcast if the entire supplied observation set is bounded by the origin; smoothing with later released information leaks the future.",  # noqa: E501
        "Fixed release delays are a transparent approximation, not a reconstructed calendar. Training GDP targets must also satisfy release timing. Convergence must be checked rather than inferred from a returned result object. One factor can miss sector-specific information; more factors increase variance and computational burden. COVID-sensitive GDP errors should be reported with a declared exclusion comparison, without choosing a preferred period after looking at scores.",  # noqa: E501
        [
            (
                "What is a ragged edge?",
                "Different indicators end at different dates because releases have different delays or gaps.",  # noqa: E501
            ),
            (
                "How does U-MIDAS differ from a bridge?",
                "It estimates separate month-slot effects rather than a single within-quarter average.",  # noqa: E501
            ),
            (
                "When does smoothing leak?",
                "When observations released after the simulated origin are included.",
            ),
            (
                "Why hide GDP after quarter end?",
                "The quarter may have ended before its GDP estimate is published.",
            ),
            (
                "Does a finite forecast prove convergence?",
                "No; likelihood and iteration diagnostics must be inspected.",
            ),
        ],
        "https://doi.org/10.1002/jae.2306",
    ),
]
cases = {
    "01_forecast_evaluation": (
        "An analyst chooses a forecasting model after inspecting the whole evaluation "
        "period and then applies the DM test to the same losses. Explain the problem and "
        "a repair. Answer: the loss sample has become a selection sample, so the ordinary "
        "comparison ignores model-search uncertainty. Reserve a later untouched period or "
        "use nested origin-bounded selection. At each origin, refit scaling and nuisance "
        "parameters using released training observations only. A negative loss "
        "differential favours model A under the stated loss, not every decision "
        "objective. Paired blocks preserve contemporaneous model/benchmark dependence; "
        "they do not repair an information leak."
    ),
    "02_bvar": (
        "An analyst switches the inflation prior mean from zero to one after observing "
        "poor annual-horizon forecasts. Is this an innocuous implementation correction? "
        "Answer: the change alters the predictive specification and is outcome-informed "
        "tuning. A unit-root prior can be natural for persistent levels but is a distinct "
        "assumption for monthly inflation. Keep the original result, describe the "
        "alternative as exploratory and evaluate it on new targets. Own and cross lag "
        "shrinkage should be justified by scale and persistence, with innovation "
        "variances estimated within training windows. Posterior shrinkage reduces "
        "variance at the possible cost of bias; it guarantees neither superior forecasts "
        "nor causal identification."
    ),
    "03_phillips": (
        "A direct inflation forecast includes target-month unemployment downloaded from "
        "the final data vintage. Why is this invalid even if the target-month seasonal "
        "dummy is allowed? Answer: calendar seasonality is known at the origin, whereas "
        "realised future unemployment is not. Use the latest released unemployment or a "
        "separately estimated origin-bounded unemployment forecast. Then distinguish "
        "predictive evaluation from a structural Phillips-curve claim: an apparent slope "
        "may reflect supply shocks, expectations or simultaneous policy responses. "
        "Forecast the same target with the same information set for every model, state "
        "the benchmark and retain weak findings rather than altering the slack measure to "
        "obtain a preferred sign."
    ),
    "04_mixed_frequency": (
        "A quarter has ended, but its GDP estimate is unpublished and the most recent "
        "industrial-production month is missing. Is filling that month by linear "
        "interpolation compatible with the information set? Answer: a future endpoint is "
        "unavailable, and a filled value would conceal genuine uncertainty. Keep the "
        "source gap, use a declared training-only design rule for bridge/MIDAS, and let "
        "the state-space model condition on the actually released series. An "
        "origin-bounded smoother may use all releases already available; it must not "
        "ingest later observations. Check numerical convergence separately from whether a "
        "finite nowcast was returned. Compare methods on common quarters and retain a "
        "declared pandemic sensitivity."
    ),
}
for name, title, intro, formula, mechanism, application, qa, reference in notes:
    text = f"# {title}\n\nStatus: draft for review\n\n## Intuition\n\n{intro}\n\n## Model\n\n{formula}\n\n## Assumptions and interpretation\n\n{mechanism}\n\n## Application and limits\n\n{application}\n\n```{{=typst}}\n#pagebreak()\n```\n\n## Exam questions and answers\n\n"  # noqa: E501
    for i, (q, a) in enumerate(qa, 1):
        text += f"### {i}. {q}\n\n**Answer.** {a}\n\n"
    text += (
        "## Reasoning exercise\n\n"
        + cases[name]
        + "\n\n## Verified reference\n\n"
        + reference
        + "\n"
    )  # noqa: E501
    p = target / (name + ".md")
    p.write_text(text)
    subprocess.run(
        [
            "pandoc",
            str(p),
            "--pdf-engine=typst",
            "--metadata-file=docs/render.yaml",
            "-o",
            str(p.with_suffix(".pdf")),
        ],
        check=True,
    )
