"""Resumable expanding forecasts and simulated publication-lag nowcasts."""

import hashlib
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.dynamic_factor_mq import DynamicFactorMQ

from inflation_forecast_nowcast.core import (
    ar_forecasts,
    bridge_predict,
    bvar_forecasts,
    direct_forecast,
    dm_hln,
    error_scores,
    ragged,
)
from inflation_forecast_nowcast.sources import load, transform

SEED = 20261007


def dfm_predict(monthly, gdp, origin, quarter, maxiter=100):
    m, q = ragged(monthly, gdp, origin, quarter)
    # Extend the observation calendar through the target quarter, entirely missing
    # after origin; filter/predict may use only the released origin observations.
    end = max(origin, quarter.asfreq("M", "end"))
    m = m.reindex(pd.period_range(m.index.min(), end, freq="M"))
    q = q.loc[:quarter]
    with warnings.catch_warnings(record=True) as notices:
        model = DynamicFactorMQ(
            m,
            endog_quarterly=q.rename("gdp").to_frame(),
            factors=1,
            factor_orders=1,
            idiosyncratic_ar1=True,
            standardize=True,
        )
        result = model.fit(maxiter=maxiter, disp=False, tolerance=1e-5)
        prediction = float(
            result.get_prediction(information_set="smoothed").predicted_mean.loc[
                quarter.asfreq("M", "end"), "gdp"
            ]
        )
    llf = np.asarray(result.mle_retvals["llf"])
    delta = 2 * abs(llf[-1] - llf[-2]) / max(abs(llf[-1]) + abs(llf[-2]), 1e-12)
    converged = bool(delta <= 1e-5)
    return prediction, dict(
        converged=converged, warnings=len(notices), iterations=result.mle_retvals.get("iter", None)
    )


def run(root: Path, quick=False, series=None):
    began = time.monotonic()
    raw = load(root) if series is None else series
    data = transform(raw)
    code = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (root / "src").rglob("*.py")
    }
    payload = {k: hashlib.sha256(v.to_csv().encode()).hexdigest() for k, v in raw.items()}
    token = hashlib.sha256(json.dumps([code, payload, quick], sort_keys=True).encode()).hexdigest()[
        :16
    ]
    runpath = root / "runs" / token
    runpath.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    score_rows = []
    horizons = [1, 3] if quick else [1, 3, 6, 12]
    for area in ["EA", "TR"]:
        names = (
            ["ea_headline", "ea_core", "ea_unemployment"]
            if area == "EA"
            else ["tr_headline", "tr_unemployment"]
        )
        frame = pd.concat([data[n].rename(n) for n in names], axis=1)
        # Explicit shorter contiguous complete sample: refuse any internal missing row.
        frame = frame.loc[frame.dropna().index.min() : frame.dropna().index.max()]
        if frame.isna().any().any():
            raise ValueError("Internal inflation input gap; no interpolation")
        targets = names[:-1]
        unemployment = frame.iloc[:, -1].to_numpy()
        stop = len(frame) - 1
        origins = [
            i
            for i in range(60, stop)
            if frame.index[min(i + max(horizons), stop)] >= pd.Period("2015-01", "M")
        ]
        if quick:
            origins = origins[-10:]
        cached = runpath / (area + "_forecasts.csv")
        if cached.exists():
            rows += pd.read_csv(cached).to_dict("records")
            continue
        local = []
        for i in origins:
            values = frame.iloc[: i + 1].to_numpy()
            bvar = bvar_forecasts(values, max(horizons))
            for j, name in enumerate(targets):
                y = values[:, j]
                ar, p = ar_forecasts(y, max(horizons))
                months = frame.index[: i + 1].month.to_numpy()
                for h in horizons:
                    if i + h >= len(frame) or frame.index[i + h] < pd.Period("2015-01", "M"):
                        continue
                    forecast_values = {
                        "RW": y[-1],
                        "AR": ar[h - 1],
                        "BVAR": bvar[h - 1, j],
                        "Phillips": direct_forecast(y, unemployment[: i + 1], h, months),
                        "LASSO": direct_forecast(y, unemployment[: i + 1], h, months, lasso=True),
                    }
                    forecast_values["Ensemble"] = float(np.mean(list(forecast_values.values())))
                    for name_model, value in forecast_values.items():
                        local.append(
                            dict(
                                target=name,
                                model=name_model,
                                horizon=h,
                                origin=str(frame.index[i]),
                                date=str(frame.index[i + h]),
                                truth=frame.iloc[i + h, j],
                                forecast=value,
                                error=frame.iloc[i + h, j] - value,
                                ar_lag=p,
                            )
                        )
        pd.DataFrame(local).to_csv(cached, index=False)
        rows += local
        print(json.dumps({"forecast_area": area, "rows": len(local)}), flush=True)
    forecasts = pd.DataFrame(rows)
    for (target_key, horizon_key), group in forecasts.groupby(["target", "horizon"]):
        target = str(target_key)
        horizon = int(str(horizon_key))
        base = group[group.model == "RW"].set_index("date").error
        for model_label, part in group.groupby("model"):
            part = part.set_index("date")
            common = pd.concat([part.error.rename("e"), base.rename("b")], axis=1).dropna()
            score_rows.append(
                dict(
                    target=target,
                    model=str(model_label),
                    horizon=horizon,
                    **error_scores(common.e, common.b, draws=49 if quick else 499),
                    **dm_hln(common.e, common.b, horizon),
                )
            )
    monthly = pd.concat(
        [data[n].rename(n) for n in ["ip", "retail", "unemployment", "esi"]], axis=1
    )
    # Earliest common calendar; keep ragged edge and all internal NaNs.
    first = max(data[n].first_valid_index() for n in ["ip", "retail", "unemployment", "esi"])
    monthly = monthly.loc[first:]
    gdp = data["de_gdp"].dropna()
    quarters = list(gdp.index[gdp.index >= pd.Period("2012Q1", "Q")])
    if quick:
        quarters = quarters[-2:]
    nowcasts = []
    failures = []
    cache = runpath / "nowcasts.csv"
    if cache.exists():
        nowcasts = pd.read_csv(cache).to_dict("records")
    done = {(r["quarter"], int(r["info_month"]), r["model"]) for r in nowcasts}
    for q in quarters:
        for month in range(1, 5):
            origin = q.asfreq("M", "start") + month - 1
            # Do not pretend future information months have occurred.
            if origin > raw["esi"].index.max():
                continue
            for model in ["Bridge", "UMIDAS", "DFM"]:
                if (str(q), month, model) in done:
                    continue
                try:
                    meta = {}
                    if model == "DFM":
                        prediction, meta = dfm_predict(
                            monthly, gdp, origin, q, maxiter=5 if quick else 100
                        )
                    else:
                        prediction = bridge_predict(
                            monthly, gdp, origin, q, unrestricted=model == "UMIDAS"
                        )
                    nowcasts.append(
                        dict(
                            quarter=str(q),
                            info_month=month,
                            model=model,
                            truth=gdp.loc[q],
                            forecast=prediction,
                            error=gdp.loc[q] - prediction,
                            **meta,
                        )
                    )
                except (ValueError, np.linalg.LinAlgError, RuntimeError) as e:
                    failures.append(
                        dict(
                            quarter=str(q),
                            month=month,
                            model=model,
                            error=type(e).__name__ + ": " + str(e)[:180],
                        )
                    )
            pd.DataFrame(nowcasts).to_csv(cache, index=False)
        print(json.dumps({"nowcast_quarter": str(q), "rows": len(nowcasts)}), flush=True)
    ns = pd.DataFrame(nowcasts)
    now_scores = []
    for exclude in [False, True]:
        part = ns[~ns.quarter.between("2020Q1", "2021Q2")] if exclude else ns
        for (model_key, month_key), group in part.groupby(["model", "info_month"]):
            model = str(model_key)
            month = int(str(month_key))
            common = (
                group.set_index("quarter")
                .error.to_frame("e")
                .join(
                    part[(part.model == "Bridge") & (part.info_month == month)]
                    .set_index("quarter")
                    .error.rename("b")
                )
                .dropna()
            )
            if len(common) >= 8:
                metrics = error_scores(common.e, common.b, draws=49 if quick else 499, block=4)
            else:
                metrics = dict(
                    n=len(common),
                    rmse=float(np.sqrt(np.mean(common.e**2))),
                    mae=float(np.mean(abs(common.e))),
                    relative_rmse=np.nan,
                    relative_mae=np.nan,
                    lo90=np.nan,
                    hi90=np.nan,
                )
            now_scores.append(dict(model=model, info_month=month, exclude_covid=exclude, **metrics))
    (root / "results").mkdir(exist_ok=True)
    pd.DataFrame(score_rows).to_csv(root / "results/inflation_scores.csv", index=False)
    pd.DataFrame(now_scores).to_csv(root / "results/nowcast_scores.csv", index=False)
    manifest = dict(
        analysis_id=token,
        seed=SEED,
        quick=quick,
        code=code,
        input_sha256=payload,
        elapsed_seconds=time.monotonic() - began,
        paid_calls=0,
        forecast_rows=len(forecasts),
        nowcast_rows=len(ns),
        failures=failures,
        dfm_converged=int(ns[ns.model == "DFM"].converged.fillna(False).sum())
        if "converged" in ns
        else 0,
        dfm_total=int((ns.model == "DFM").sum()),
        information="Latest vintage; simulated fixed publication lags; no interpolation",
        scope="minimum models and all three nowcast methods; conditional evaluation bootstrap",
    )
    (runpath / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    (root / "results/manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    return manifest
