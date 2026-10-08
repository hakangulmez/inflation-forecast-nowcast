# ruff: noqa: E501
"""Generate the paper exclusively from saved forecast-score aggregates."""


def generate(csv, js, macro, table, fmt):
    contract = js("technical_model_contract.json")
    for name, value in [
        ("ARCap", contract["ar"]["maxlag"]),
        ("BVARLag", contract["bvar"]["p"]),
        ("OwnShrink", contract["bvar"]["own"]),
        ("CrossShrink", contract["bvar"]["cross"]),
        ("LassoPenalty", contract["direct_forecast"]["alpha"]),
        ("BridgeRidge", contract["bridge_predict"]["ridge"]),
        ("EMCap", contract["dfm"]["maxiter"]),
        ("EMTolerance", contract["dfm"]["tolerance"]),
        ("LossDraws", contract["error_scores"]["draws"]),
        ("LossBlock", contract["error_scores"]["block"]),
    ]:
        macro(name, value)
    inv = js("data_inventory.json")
    m = js("manifest.json")
    js("yoy_manifest.json")
    f = csv("inflation_scores_yoy.csv")
    n = csv("nowcast_scores.csv")
    mm = csv("inflation_scores_mm.csv")
    conv = csv("dfm_convergence_sensitivity.csv")
    from pandas import Period

    macro("EvalEnd", inv["ea_unemployment"]["last"])
    macro("EvalStart", str(Period(inv["ea_unemployment"]["last"], "M") - int(f.n.iloc[0]) + 1))
    macro("GDPStart", str(Period(inv["de_gdp"]["last"], "Q") - int(n.n.max()) + 1))
    macro("GDPEnd", inv["de_gdp"]["last"])
    macro("EvalN", int(f.n.iloc[0]))
    macro("DFMTotal", m["dfm_total"])
    macro("DFMConverged", m["dfm_converged"])
    macro("DFMFailed", m["dfm_total"] - m["dfm_converged"])
    macro("Seed", m["seed"])
    for pre, target, model in [
        ("Core", "ea_core", "BVAR"),
        ("Headline", "ea_headline", "Ensemble"),
        ("TR", "tr_headline", "BVAR"),
    ]:
        a = f[
            (f.target == target) & (f.model == model) & (f.benchmark == "RW") & (f.horizon == 1)
        ].iloc[0]
        for suffix, col in [
            ("Ratio", "relative_rmse"),
            ("Low", "lo90"),
            ("High", "hi90"),
            ("P", "dm_pvalue"),
            ("RMSE", "rmse"),
        ]:
            macro(pre + suffix, a[col], 3)
    a = n[(n.model == "DFM") & (n.info_month == 3) & (~n.exclude_covid)].iloc[0]
    macro("NowcastRMSE", a.rmse, 3)
    macro("NowcastRatio", a.relative_rmse, 2)
    names = {
        "ea_headline": "EA headline prices",
        "ea_core": "EA core prices",
        "ea_unemployment": "EA unemployment",
        "de_gdp": "DE real GDP",
        "ip": "DE production",
        "retail": "DE retail volume",
        "unemployment": "DE unemployment",
        "esi": "DE sentiment",
        "tr_headline": "TR headline prices",
        "tr_unemployment": "TR unemployment",
    }
    transforms = {
        "ea_headline": "100(P/P lag12 – 1); secondary 100 Δlog",
        "ea_core": "Same price transforms",
        "tr_headline": "Same price transforms",
        "de_gdp": "100 Δlog; q/q, not annualised",
        "ip": "100 Δlog; m/m",
        "retail": "100 Δlog; m/m",
        "unemployment": "First difference, pp",
        "ea_unemployment": "Level, percent",
        "tr_unemployment": "Level, percent",
        "esi": "Level index",
    }
    from urllib.parse import parse_qs, urlparse

    rows = []
    for key, label in names.items():
        info = inv[key]
        url = inv["sources"][key]["url"]
        q = parse_qs(urlparse(url).query)
        if key.startswith("tr_"):
            identifier = url.split("series=")[1].split("&")[0]
            identity = "EVDS: " + identifier
        else:
            identifier = urlparse(url).path.rsplit("/", 1)[-1]
            selectors = "; ".join(
                k + "=" + v[0]
                for k, v in q.items()
                if k not in ["lang", "sinceTimePeriod", "untilTimePeriod", "freq"]
            )
            identity = "Eurostat: " + identifier + "; " + selectors
        rows.append([label, identity, transforms[key], info["first"] + " / " + info["last"]])
    table(
        "data",
        ["Variable", "Source / exact ID and selectors", "Transform", "Source coverage"],
        rows,
        "Official source definitions and observed coverage",
        (
            "Source: author's calculations from the documented inputs. "
            "Coverage is source availability, not "
            "an identical estimation sample. Missing observations are not interpolated; "
            "source countries and seasonality follow the exact selectors."
        ),
        layout="p{0.18\\linewidth}p{0.36\\linewidth}p{0.23\\linewidth}X",
        size="footnotesize",
    )
    rows = []
    for target in ["ea_core", "ea_headline", "tr_headline"]:
        for model in ["RW", "AO", "AR", "BVAR", "Phillips", "LASSO", "Ensemble", "SeasonalMean"]:
            a = f[
                (f.target == target) & (f.model == model) & (f.benchmark == "RW") & (f.horizon == 1)
            ].iloc[0]
            rows.append(
                [
                    target.replace("ea_", "EA ").replace("tr_", "TR "),
                    model,
                    fmt(a.rmse),
                    fmt(a.relative_rmse),
                    f"[{fmt(a.lo90)}, {fmt(a.hi90)}]",
                    fmt(a.dm_pvalue),
                ]
            )
    table(
        "horizon_one",
        ["Target", "Model", "RMSE", "Rel. RMSE", "90% ratio interval", "DM p"],
        rows,
        "Primary year-on-year forecast evaluation at the shortest horizon",
        (
            "Source: results/inflation_scores_yoy.csv; h=1, matched target dates, RW "
            "denominator. Bands are paired evaluation-loss bootstrap intervals, not "
            "prediction intervals. All methods are reported."
        ),
        layout="XlrrXr",
        size="footnotesize",
    )
    rows = []
    for target in ["ea_core", "ea_headline", "tr_headline"]:
        for h in [1, 3, 6, 12]:
            for model in ["BVAR", "Ensemble", "SeasonalMean"]:
                a = f[
                    (f.target == target)
                    & (f.model == model)
                    & (f.benchmark == "RW")
                    & (f.horizon == h)
                ].iloc[0]
                rows.append(
                    [
                        target.replace("ea_", "EA ").replace("tr_", "TR "),
                        h,
                        model,
                        fmt(a.relative_rmse),
                        f"[{fmt(a.lo90)}, {fmt(a.hi90)}]",
                        fmt(a.dm_pvalue),
                    ]
                )
    table(
        "horizons",
        ["Target", "h", "Model", "Rel. RMSE", "90% interval", "DM p"],
        rows,
        "Fixed BVAR, ensemble and seasonal mean across all declared horizons",
        (
            "Source: results/inflation_scores_yoy.csv, RW benchmark; ratios below one "
            "indicate smaller RMSE. Tests are unadjusted exploratory comparisons."
        ),
        layout="XrlrXr",
        size="footnotesize",
    )
    rows = []
    for target in ["ea_core", "ea_headline", "tr_headline"]:
        for h in [1, 12]:
            for model in ["RW", "BVAR", "Ensemble"]:
                a = f[
                    (f.target == target)
                    & (f.model == model)
                    & (f.benchmark == "AO")
                    & (f.horizon == h)
                ].iloc[0]
                rows.append(
                    [
                        target.replace("ea_", "EA ").replace("tr_", "TR "),
                        h,
                        model,
                        fmt(a.relative_rmse),
                        f"[{fmt(a.lo90)}, {fmt(a.hi90)}]",
                        fmt(a.dm_pvalue),
                    ]
                )
    table(
        "ao",
        ["Target", "h", "Model", "Rel. RMSE", "90% interval", "DM p"],
        rows,
        "Sensitivity to the monthly AO benchmark",
        (
            "Source: results/inflation_scores_yoy.csv; AO denominator. The AO monthly "
            "adaptation sums simple monthly percentage rates; it is not compounded y/y "
            "inflation."
        ),
        layout="XrlrXr",
        size="footnotesize",
    )
    rows = []
    for _, a in n[~n.exclude_covid].iterrows():
        rows.append(
            [
                a.model,
                int(a.info_month),
                int(a.n),
                fmt(a.rmse),
                fmt(a.relative_rmse),
                f"[{fmt(a.lo90)}, {fmt(a.hi90)}]",
            ]
        )
    table(
        "nowcast",
        ["Model", "Info month", "n", "RMSE", "Rel. RMSE", "90% interval"],
        rows,
        "German GDP nowcast scores by information month",
        (
            "Source: results/nowcast_scores.csv, full sample. GDP is q/q log growth in "
            "percentage points, not annualised. Bridge is the matched benchmark; months "
            "count from the target quarter start."
        ),
        layout="XrrrrX",
        size="footnotesize",
    )
    rows = []
    for target in ["ea_core", "ea_headline", "tr_headline"]:
        for model in ["RW", "AR", "BVAR", "Ensemble"]:
            a = mm[(mm.target == target) & (mm.model == model) & (mm.horizon == 1)].iloc[0]
            rows.append(
                [
                    target.replace("ea_", "EA ").replace("tr_", "TR "),
                    model,
                    fmt(a.rmse),
                    fmt(a.relative_rmse),
                    f"[{fmt(a.lo90)}, {fmt(a.hi90)}]",
                    fmt(a.dm_pvalue),
                ]
            )
    table(
        "monthly",
        ["Target", "Model", "RMSE", "Rel. RMSE", "90% interval", "DM p"],
        rows,
        "Secondary monthly-inflation comparison",
        (
            "Source: results/inflation_scores_mm.csv; h=1. NSA monthly log inflation and"
            " a plain random walk are not the primary fair benchmark test. Original "
            "estimates are preserved without refitting."
        ),
        layout="XlrrXr",
        size="footnotesize",
    )
    rows = []
    for _, a in n[n.exclude_covid].iterrows():
        rows.append(
            [
                a.model,
                int(a.info_month),
                int(a.n),
                fmt(a.relative_rmse),
                f"[{fmt(a.lo90)}, {fmt(a.hi90)}]",
            ]
        )
    table(
        "covid",
        ["Model", "Info month", "n", "Rel. RMSE", "90% interval"],
        rows,
        "Declared pandemic-window exclusion sensitivity",
        (
            "Source: results/nowcast_scores.csv, exclude_covid=True. The source excludes"
            " the specified pandemic quarter window; it does "
            "not retune any model."
        ),
        layout="XrrrX",
        size="footnotesize",
    )
    table(
        "convergence",
        ["Info month", "n", "RMSE", "Rel. RMSE", "90% interval"],
        [
            [
                int(a.info_month),
                int(a.n),
                fmt(a.rmse),
                fmt(a.relative_rmse),
                f"[{fmt(a.lo90)}, {fmt(a.hi90)}]",
            ]
            for _, a in conv.iterrows()
        ],
        "DFM convergence-only matched evaluation",
        (
            "Source: author's calculations from the documented inputs. "
            "Only previously flagged "
            "converged predictions enter; no model is refitted. Bridge errors are "
            "matched to the same retained dates."
        ),
        layout="XrrrX",
        size="footnotesize",
    )
    rows = [
        [
            "Target",
            "Primary y/y; secondary NSA monthly log inflation",
            "Both reported; monthly table secondary",
        ],
        ["Benchmark", "RW y/y; AO monthly adaptation", "Matched forecast errors for both"],
        [
            "Inflation model",
            "AR, Phillips, LASSO, BVAR, fixed ensemble",
            "All declared methods, all horizons",
        ],
        ["Nowcast method", "Bridge, unrestricted MIDAS, DFM", "Fixed information-month masks"],
        [
            "Pandemic window",
            "All quarters; fixed COVID exclusion",
            "Scores retained without refitting",
        ],
        [
            "Convergence",
            "All flagged DFM fits; converged-only matched sample",
            "Failed fits retained in primary scores",
        ],
        [
            "Hyperparameters",
            "Origin-only AR BIC; other fixed settings",
            "No evaluation-based search",
        ],
        [
            "Missing inputs",
            "DFM masking; bridge design-mean replacement",
            "No source interpolation",
        ],
        [
            "Unavailable extensions",
            "Historical-vintage reconstruction; additional model families",
            "Not executed; no invented results",
        ],
    ]
    table(
        "robustness",
        ["Alternative", "Definition", "Status"],
        rows,
        "Complete declared-alternative ledger",
        (
            "Sources: forecast evaluation tables and fixed modelling specifications."
            " Alternatives are compared using the reported evaluation samples."
        ),
        layout="p{0.19\\linewidth}p{0.43\\linewidth}X",
        size="footnotesize",
    )
    table(
        "availability",
        ["Series", "Observed n", "First", "Last", "Missing dates"],
        [
            [
                names[k],
                inv[k]["n"],
                inv[k]["first"],
                inv[k]["last"],
                ", ".join(inv[k]["missing"])
                if len(inv[k]["missing"]) < 4
                else str(len(inv[k]["missing"])) + " early months",
            ]
            for k in names
        ],
        "Saved input availability and ragged-edge diagnostics",
        (
            "Source: author's calculations from the documented inputs. "
            "Missing dates follow the requested "
            "retrieval window. Early unavailable history and current ragged edges are "
            "distinguished; no calendar compression or interpolation."
        ),
        layout="Xrllp{0.26\\linewidth}",
        size="footnotesize",
    )

    for name, model in [("TRLongBVAR", "BVAR"), ("TRLongAR", "AR")]:
        a = f[
            (f.target == "tr_headline")
            & (f.model == model)
            & (f.benchmark == "RW")
            & (f.horizon == 12)
        ].iloc[0]
        macro(name, a.relative_rmse, 3)
    attr = csv("v3_inference_attribution.csv")
    selected = attr[
        (attr.horizon == 1) & attr.model.isin(["BVAR", "Ensemble"]) & (attr.benchmark == "RW")
    ]
    table(
        "inference_changes",
        ["Target", "Model", "n", "Unmasked A", "Unmasked B", "Masked A", "Masked B"],
        [
            [
                a.target,
                a.model,
                int(a.v3_paired_n),
                fmt(a.v2_original_p),
                fmt(a.v2_errors_v3_hac_p),
                fmt(a.v3_errors_legacy_p),
                fmt(a.v3_errors_v3_hac_p),
            ]
            for _, a in selected.iterrows()
        ],
        "Information-set and HAC changes separated on identical error pairs",
        "Source: author calculations. A: L = h - 1; B: L = h + 11. Unmasked and publication-masked forecasts use the same latest-vintage data. Each information-set comparison across HAC rules uses identical paired errors. No bootstrap interval is changed by HAC.",
        layout="Xlrrrrr",
        size="footnotesize",
    )

    seasonal = f[
        (f.target == "tr_headline")
        & (f.model == "SeasonalMean")
        & (f.benchmark == "RW")
        & (f.horizon == 1)
    ].iloc[0]
    macro("SeasonalTRRatio", seasonal.relative_rmse, 3)
    macro("SeasonalTRLow", seasonal.lo90, 3)
    macro("SeasonalTRHigh", seasonal.hi90, 3)
