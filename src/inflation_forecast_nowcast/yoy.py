"""V2 point year-on-year forecasts; fixed estimators and two origin-only benchmarks."""

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from inflation_forecast_nowcast.core import (
    ar_forecasts,
    bvar_forecasts,
    direct_forecast,
    dm_hln,
    error_scores,
)
from inflation_forecast_nowcast.sources import load


def annual_targets(prices):
    """Exact y/y percent rate and annualized mean of 12 simple m/m rates."""
    monthly = 100 * (prices / prices.shift(1) - 1)
    return 100 * (prices / prices.shift(12) - 1), monthly.rolling(12).sum()


def forecasts_at(frame, ao, i, horizons):
    """The fitting contract sees rows through origin i only."""
    values = frame.iloc[: i + 1].to_numpy()
    bvar = bvar_forecasts(values, max(horizons))
    records = []
    for j, target in enumerate(frame.columns[:-1]):
        y = values[:, j]
        ar, lag = ar_forecasts(y, max(horizons))
        months = frame.index[: i + 1].month.to_numpy()
        for h in horizons:
            predictions = {
                "RW": y[-1],
                "AO": float(ao[target].iloc[i]),
                "AR": ar[h - 1],
                "BVAR": bvar[h - 1, j],
                "Phillips": direct_forecast(y, values[:, -1], h, months),
                "LASSO": direct_forecast(y, values[:, -1], h, months, lasso=True),
            }
            predictions["Ensemble"] = float(
                np.mean([predictions[k] for k in ["RW", "AR", "BVAR", "Phillips", "LASSO"]])
            )
            for model, forecast in predictions.items():
                records.append(
                    dict(target=target, model=model, horizon=h, forecast=forecast, ar_lag=lag)
                )
    return records


def run(root: Path, raw=None, quick=False):
    started = time.monotonic()
    raw = load(root) if raw is None else raw
    code = {
        f"src/inflation_forecast_nowcast/{p.name}": hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [
            Path(__file__),
            Path(__file__).with_name("core.py"),
            Path(__file__).with_name("sources.py"),
        ]
    }
    inputs = {k: hashlib.sha256(v.to_csv().encode()).hexdigest() for k, v in raw.items()}
    token = hashlib.sha256(json.dumps([code, inputs, quick], sort_keys=True).encode()).hexdigest()[
        :16
    ]
    private = root / "runs" / ("yoy_" + token)
    private.mkdir(parents=True, exist_ok=True)
    all_rows = []
    for area, names in [
        ("EA", ["ea_headline", "ea_core", "ea_unemployment"]),
        ("TR", ["tr_headline", "tr_unemployment"]),
    ]:
        annual, ao = {}, {}
        for name in names[:-1]:
            annual[name], ao[name] = annual_targets(raw[name])
        frame = pd.concat(
            [*(annual[n].rename(n) for n in names[:-1]), raw[names[-1]].rename(names[-1])], axis=1
        )
        complete = frame.dropna()
        frame = frame.loc[complete.index.min() : complete.index.max()]
        if frame.isna().any().any():
            raise ValueError("Internal inflation gap: no interpolation")
        aoframe = pd.concat(ao, axis=1).reindex(frame.index)
        cache = private / (area + "_forecasts.csv")
        rows = pd.read_csv(cache).to_dict("records") if cache.exists() else []
        done = {str(r["origin"]) for r in rows}
        origins = list(range(60, len(frame) - 1))
        if quick:
            origins = origins[-22:-12]
        for i in origins:
            origin = str(frame.index[i])
            if origin in done or frame.index[min(i + 12, len(frame) - 1)] < pd.Period(
                "2015-01", "M"
            ):
                continue
            for record in forecasts_at(frame, aoframe, i, [1, 3, 6, 12]):
                h = record["horizon"]
                if i + h >= len(frame) or frame.index[i + h] < pd.Period("2015-01", "M"):
                    continue
                truth = float(frame[record["target"]].iloc[i + h])
                rows.append(
                    record
                    | dict(
                        origin=origin,
                        date=str(frame.index[i + h]),
                        truth=truth,
                        error=truth - record["forecast"],
                    )
                )
            pd.DataFrame(rows).to_csv(cache, index=False)
        all_rows.extend(rows)
        print(json.dumps(dict(area=area, rows=len(rows))), flush=True)
    forecasts = pd.DataFrame(all_rows)
    scores = []
    for (target, h), group in forecasts.groupby(["target", "horizon"]):
        for benchmark in ["RW", "AO"]:
            baseline = group[group.model == benchmark].set_index("date").error
            for model, part in group.groupby("model"):
                common = (
                    pd.concat(
                        [part.set_index("date").error.rename("e"), baseline.rename("b")], axis=1
                    )
                    .dropna()
                    .sort_index()
                )
                scores.append(
                    dict(
                        target=target,
                        horizon=int(str(h)),
                        model=model,
                        benchmark=benchmark,
                        **error_scores(common.e, common.b, draws=49 if quick else 499),
                        **dm_hln(common.e, common.b, int(str(h))),
                    )
                )
    result = pd.DataFrame(scores)
    (root / "results").mkdir(exist_ok=True)
    result.to_csv(root / "results/inflation_scores_yoy.csv", index=False)
    result[result.benchmark == "RW"].to_csv(root / "results/inflation_scores.csv", index=False)
    manifest = dict(
        analysis_id="yoy_" + token,
        code=code,
        inputs=inputs,
        target="100*(P_t/P_t-12 - 1); point y/y at origin+h; percent",
        AO="sum of last 12 simple m/m percent changes at origin; monthly adaptation",
        horizons=[1, 3, 6, 12],
        fixed_settings="docs/V2_TARGET.md; no evaluation tuning",
        forecast_rows=len(forecasts),
        paid_calls=0,
        quick=quick,
        elapsed_seconds=time.monotonic() - started,
        inherited_nowcast_manifest_sha256=hashlib.sha256(
            (root / "results/manifest.json").read_bytes()
        ).hexdigest()
        if (root / "results/manifest.json").exists()
        else None,
    )
    (root / "results/yoy_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
