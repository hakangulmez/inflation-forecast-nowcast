# ruff: noqa: E501
"""Frozen-input publication-lag evaluation; no acquisition or model selection changes."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from inflation_forecast_nowcast.core import (
    ar_forecasts,
    bvar_forecasts,
    direct_forecast,
    dm_hln,
    error_scores,
)
from inflation_forecast_nowcast.yoy import annual_targets

HORIZONS = [1, 3, 6, 12]
MODELS = ["RW", "AO", "AR", "BVAR", "Phillips", "LASSO", "Ensemble", "SeasonalMean"]


def seasonal_path(prices, origin, target, rule="mean"):
    """Only published level pairs form changes; predictions never replenish history."""
    published = prices.loc[: origin - 1]
    history = np.log(published).diff().dropna()
    end = pd.Period(target, "M")
    changes = []
    for month in pd.period_range(end - 11, end, freq="M"):
        if month <= origin - 1:
            value = history.get(month, np.nan)
        else:
            eligible = history[history.index.month == month.month]
            need = 3 if rule == "mean" else 1
            value = eligible.iloc[-need:].mean() if len(eligible) >= need else np.nan
        changes.append(value)
    return float(100 * np.expm1(np.sum(changes)))


def forecasts_at(raw, names, origin, horizons=HORIZONS):
    """Fixed targets o+h; complete-panel and target-only cutoffs explicitly differ."""
    price_cutoff, unemployment_cutoff = origin - 1, origin - 2
    annual, ao = {}, {}
    for name in names[:-1]:
        annual[name], ao[name] = annual_targets(raw[name].loc[:price_cutoff])
    panel = pd.concat(
        [
            *(annual[n].rename(n) for n in names[:-1]),
            raw[names[-1]].loc[:unemployment_cutoff].rename(names[-1]),
        ],
        axis=1,
    )
    complete = panel.dropna()
    if complete.empty:
        raise ValueError("No published complete training panel")
    training = panel.loc[complete.index.min() : complete.index.max()]
    if training.isna().any().any():
        raise ValueError("Internal training gap: no date compression/interpolation")
    cutoff = training.index[-1]
    steps = max((origin + h - cutoff).n for h in horizons)
    values = training.to_numpy()
    bvar = bvar_forecasts(values, steps)
    records = []
    for j, name in enumerate(names[:-1]):
        observed = annual[name].dropna()
        target_only = annual[name].loc[observed.index.min() : observed.index.max()]
        if target_only.isna().any():
            raise ValueError("Internal target gap")
        target_cutoff = target_only.index[-1]
        ar, lag = ar_forecasts(
            target_only.to_numpy(), max((origin + h - target_cutoff).n for h in horizons)
        )
        months = training.index.month.to_numpy()
        for h in horizons:
            target = origin + h
            forward = (target - cutoff).n
            predictions = {
                "RW": float(target_only.iloc[-1]),
                "AO": float(ao[name].loc[target_cutoff]),
                "AR": float(ar[(target - target_cutoff).n - 1]),
                "BVAR": float(bvar[forward - 1, j]),
                "Phillips": direct_forecast(values[:, j], values[:, -1], forward, months),
                "LASSO": direct_forecast(values[:, j], values[:, -1], forward, months, lasso=True),
                "SeasonalMean": seasonal_path(raw[name], origin, target),
            }
            predictions["Ensemble"] = float(
                np.mean([predictions[k] for k in ["RW", "AR", "BVAR", "Phillips", "LASSO"]])
            )
            for model, forecast in predictions.items():
                effective = target_cutoff if model in {"RW", "AO", "AR", "SeasonalMean"} else cutoff
                records.append(
                    dict(
                        target=name,
                        model=model,
                        horizon=h,
                        forecast=forecast,
                        ar_lag=lag,
                        origin=str(origin),
                        origin_timestamp=origin.end_time.isoformat(),
                        date=str(target),
                        price_cutoff=str(price_cutoff),
                        unemployment_cutoff=str(unemployment_cutoff),
                        effective_cutoff=str(effective),
                        forward_steps=(target - effective).n,
                        ensemble_component_cutoffs=(
                            f"target-only:{target_cutoff}; panel:{cutoff}"
                            if model == "Ensemble"
                            else ""
                        ),
                    )
                )
    return records


def score_forecasts(forecasts, root):
    scores, accounting = [], []
    for (target, h), group in forecasts.groupby(["target", "horizon"]):
        error_panel = (
            group.pivot(index="date", columns="model", values="error")
            .reindex(columns=MODELS)
            .sort_index()
        )
        common = error_panel.replace([np.inf, -np.inf], np.nan).dropna()
        accounting.append(
            dict(
                target=target,
                horizon=int(h),
                first=str(common.index.min()),
                last=str(common.index.max()),
                n=len(common),
                candidate_n=len(error_panel),
                excluded_dates=sorted(set(error_panel.index) - set(common.index)),
                missing_by_model={
                    k: list(error_panel.index[error_panel[k].isna()]) for k in MODELS
                },
            )
        )
        if len(common) < 8:
            continue
        for benchmark in ["RW", "AO", "SeasonalMean"]:
            for model in MODELS:
                legacy = dm_hln(common[model], common[benchmark], int(h))
                revised = dm_hln(common[model], common[benchmark], int(h), bandwidth=int(h) + 11)
                scores.append(
                    dict(
                        target=target,
                        horizon=int(h),
                        model=model,
                        benchmark=benchmark,
                        first=str(common.index.min()),
                        last=str(common.index.max()),
                        **error_scores(common[model], common[benchmark]),
                        **revised,
                        dm_bandwidth=int(h) + 11,
                        dm_pvalue_legacy=legacy["dm_pvalue"],
                        dm_hln_legacy=legacy["dm_hln"],
                        legacy_bandwidth=int(h) - 1,
                    )
                )
    table = pd.DataFrame(scores)
    table.to_csv(root / "results/inflation_scores_yoy_v3.csv", index=False)
    table.to_csv(root / "results/inflation_scores_yoy.csv", index=False)
    table[table.benchmark == "RW"].to_csv(root / "results/inflation_scores.csv", index=False)
    (root / "results/v3_evaluation_dates.json").write_text(json.dumps(accounting, indent=2) + "\n")
    return table


def inference_attribution(root, forecasts, scores):
    """Both fixed HAC rules on unchanged V2 pairs, separate from V3 forecast changes."""
    oldroot = root / "versions/v2-2026-10-07/results"
    manifest = json.loads((oldroot / "yoy_manifest.json").read_text())
    old = pd.concat(
        [
            pd.read_csv(root / "runs" / manifest["analysis_id"] / (area + "_forecasts.csv"))
            for area in ["EA", "TR"]
        ]
    )
    old_scores = pd.read_csv(oldroot / "inflation_scores_yoy.csv")
    rows = []
    for record in old_scores.itertuples():
        row: Any = record
        group = old[(old.target == row.target) & (old.horizon == row.horizon)]
        panel = group.pivot(index="date", columns="model", values="error").sort_index()
        common = (
            panel[[row.model, row.benchmark]].dropna()
            if row.model != row.benchmark
            else panel[[row.model]].dropna()
        )
        e = common[row.model]
        b = common[row.benchmark]
        legacy = dm_hln(e, b, row.horizon)
        new = dm_hln(e, b, int(row.horizon), int(row.horizon) + 11)
        same = scores[
            (scores.target == row.target)
            & (scores.horizon == row.horizon)
            & (scores.model == row.model)
            & (scores.benchmark == row.benchmark)
        ].iloc[0]
        assert (pd.isna(row.dm_pvalue) and pd.isna(legacy["dm_pvalue"])) or np.isclose(
            float(row.dm_pvalue), legacy["dm_pvalue"], atol=1e-12
        )
        rows.append(
            dict(
                target=row.target,
                horizon=row.horizon,
                model=row.model,
                benchmark=row.benchmark,
                v2_original_p=row.dm_pvalue,
                v2_errors_legacy_p=legacy["dm_pvalue"],
                v2_errors_v3_hac_p=new["dm_pvalue"],
                v2_paired_n=legacy["dm_n"],
                v3_errors_legacy_p=same.dm_pvalue_legacy,
                v3_errors_v3_hac_p=same.dm_pvalue,
                v3_paired_n=same.dm_n,
                legacy_bandwidth=int(row.horizon) - 1,
                v3_bandwidth=int(row.horizon) + 11,
                v2_relative_rmse=row.relative_rmse,
                v3_relative_rmse=same.relative_rmse,
            )
        )
    pd.DataFrame(rows).to_csv(root / "results/v3_inference_attribution.csv", index=False)


def run(root):
    began = time.monotonic()
    deadline = began + 7200
    protocol = root / "docs/V3_PROTOCOL.md"
    raw = {}
    for name in ["ea_headline", "ea_core", "ea_unemployment", "tr_headline", "tr_unemployment"]:
        path = root / "data/processed" / (name + ".csv")
        if not path.exists():
            raise FileNotFoundError("Frozen input required: " + name)
        s = pd.read_csv(path, index_col=0).iloc[:, 0]
        s.index = pd.PeriodIndex(s.index, freq="M")
        raw[name] = s
    code = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path(__file__), Path(__file__).with_name("core.py"), protocol]
    }
    inputs = {
        str((root / "data/processed" / (n + ".csv")).relative_to(root)): hashlib.sha256(
            (root / "data/processed" / (n + ".csv")).read_bytes()
        ).hexdigest()
        for n in raw
    }
    token = hashlib.sha256(json.dumps([code, inputs], sort_keys=True).encode()).hexdigest()[:16]
    private = root / "runs" / ("v3_inflation_" + token)
    private.mkdir(parents=True, exist_ok=True)
    all_rows = []
    failures = []
    for area, names in [
        ("EA", ["ea_headline", "ea_core", "ea_unemployment"]),
        ("TR", ["tr_headline", "tr_unemployment"]),
    ]:
        cache = private / (area + "_forecasts.csv")
        rows = pd.read_csv(cache).to_dict("records") if cache.exists() else []
        done = {r["origin"] for r in rows}
        annual = [annual_targets(raw[n])[0] for n in names[:-1]]
        frame = pd.concat(
            [*(a.rename(n) for a, n in zip(annual, names[:-1], strict=True)), raw[names[-1]]],
            axis=1,
        ).dropna()
        for origin in pd.period_range(frame.index.min() + 60, pd.Period("2026-07", "M"), freq="M"):
            if str(origin) in done or origin + 12 < pd.Period("2015-01", "M"):
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError("V3 2h budget exceeded; resumable cache preserved")
            try:
                predictions = forecasts_at(raw, names, origin)
            except (ValueError, np.linalg.LinAlgError) as exc:
                failures.append(dict(area=area, origin=str(origin), error=str(exc)))
                continue
            for record in predictions:
                date = pd.Period(record["date"], "M")
                if not pd.Period("2015-01", "M") <= date <= pd.Period("2026-08", "M"):
                    continue
                truth = float(annual_targets(raw[record["target"]])[0].get(date, np.nan))
                rows.append(record | dict(truth=truth, error=truth - record["forecast"]))
            temporary = cache.with_suffix(".tmp")
            pd.DataFrame(rows).to_csv(temporary, index=False)
            temporary.replace(cache)
        all_rows.extend(rows)
        print(json.dumps(dict(area=area, forecast_rows=len(rows))), flush=True)
    f = pd.DataFrame(all_rows)
    scores = score_forecasts(f, root)
    inference_attribution(root, f, scores)
    availability = (
        f.groupby(["target", "model", "horizon"])
        .agg(
            first_origin=("origin", "min"),
            last_origin=("origin", "max"),
            count=("origin", "size"),
            min_forward=("forward_steps", "min"),
            max_forward=("forward_steps", "max"),
        )
        .reset_index()
    )
    availability.to_csv(root / "results/v3_cutoff_summary.csv", index=False)
    manifest = dict(
        analysis_id=private.name,
        inputs=inputs,
        code=code,
        protocol_sha256=hashlib.sha256(protocol.read_bytes()).hexdigest(),
        availability="assumed EOM price t+1; unemployment t+2",
        latest_vintage=True,
        horizons=HORIZONS,
        forecast_rows=len(f),
        elapsed_seconds=time.monotonic() - began,
        failures=failures,
        paid_calls=0,
        inherited_nowcast_manifest_sha256=hashlib.sha256(
            (root / "results/manifest.json").read_bytes()
        ).hexdigest(),
        uncertainty="loss-block12/draws499/seed20261007 unchanged; DM Bartlett h+11 with legacy retained",
    )
    (root / "results/yoy_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (root / "results/v3_inflation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (private / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
