"""Analytic checks, leakage invariance and a complete isolated pipeline exercise."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.stats import t as student_t

from inflation_forecast_nowcast.core import (
    ar_forecasts,
    bridge_predict,
    bvar_forecasts,
    direct_forecast,
    dm_hln,
    error_scores,
    lag_matrix,
    ragged,
)
from inflation_forecast_nowcast.pipeline import run
from inflation_forecast_nowcast.sources import eurostat, evds, load, transform


def synthetic():
    path = Path(__file__).parents[1] / "scripts/research.py"
    spec = importlib.util.spec_from_file_location("exercise", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.synthetic()


def test_estimators_constant_and_oracle_ar():
    rng = np.random.default_rng(2)
    y = np.zeros(400)
    for i in range(1, len(y)):
        y[i] = 0.7 * y[i - 1] + rng.normal(scale=0.2)
    x, t = lag_matrix(y, 2)
    assert np.array_equal(x[0], [1, y[1], y[0]]) and t[0, 0] == y[2]
    with pytest.raises(ValueError):
        lag_matrix(y[:2], 2)
    f, p = ar_forecasts(y, 3)
    assert p == 1
    b = np.linalg.lstsq(np.c_[np.ones(399), y[:-1]], y[1:], rcond=None)[0]
    assert f[0] == pytest.approx(b[0] + b[1] * y[-1])
    constant = np.full((100, 2), 2.0)
    assert np.allclose(bvar_forecasts(constant, 4, p=2), 2, atol=1e-5)
    u = rng.normal(size=len(y))
    months = np.arange(len(y)) % 12 + 1
    assert np.isfinite(direct_forecast(y, u, 3, months))
    assert np.isfinite(direct_forecast(y, u, 3, months, lasso=True))
    u[-1] = np.nan
    assert np.isnan(direct_forecast(y, u, 3, months))
    assert np.isnan(direct_forecast(y[:30], np.ones(30), 1, months[:30]))


def test_dm_and_paired_block_scores_reference():
    rng = np.random.default_rng(1)
    b = rng.normal(size=90)
    e = 0.5 * b
    out = dm_hln(e, b, 1)
    d = e * e - b * b
    stat = d.mean() / np.sqrt(np.mean((d - d.mean()) ** 2) / 90) * np.sqrt(89 / 90)
    assert out["dm_hln"] == pytest.approx(stat)
    assert out["dm_pvalue"] == pytest.approx(2 * student_t.sf(abs(stat), 89))
    assert np.isnan(dm_hln(b, b, 1)["dm_hln"])
    assert np.isnan(dm_hln(e[:5], b[:5], 3)["dm_hln"])
    assert dm_hln(e, b, 6)["dm_pvalue"] < 0.01
    scores = error_scores(e, b, draws=20)
    assert scores["relative_rmse"] == pytest.approx(0.5)
    assert scores["lo90"] == pytest.approx(0.5) and scores["hi90"] == pytest.approx(0.5)
    with pytest.raises(ValueError):
        error_scores(e[:4], b[:4])


def test_publication_masks_and_future_invariance():
    data = transform(synthetic())
    m = pd.concat([data[k].rename(k) for k in ["ip", "retail", "unemployment", "esi"]], axis=1)
    q = data["de_gdp"].dropna()
    quarter = pd.Period("2020Q1", "Q")
    origin = pd.Period("2020-02", "M")
    masked, g = ragged(m, q, origin, quarter)
    assert masked.loc["2020-01", "ip"] != masked.loc["2020-01", "ip"]
    assert pd.isna(g.loc[quarter]) and not pd.isna(g.loc["2019Q4"])
    assert pd.isna(ragged(m, q, origin - 1, quarter)[1].loc["2019Q4"])
    assert not pd.isna(masked.loc[origin, "esi"])
    altered = m.copy()
    altered.loc[altered.index > origin] = 100000
    changed = q.copy()
    changed.loc[changed.index >= quarter] = 100000
    for slots in [False, True]:
        first = bridge_predict(m, q, origin, quarter, unrestricted=slots)
        second = bridge_predict(altered, changed, origin, quarter, unrestricted=slots)
        assert first == pytest.approx(second)
    assert m.loc["2020-01", "ip"] == data["ip"].loc["2020-01"]


def test_offline_pipeline_and_resume(tmp_path):
    summary = run(tmp_path, quick=True, series=synthetic())
    again = run(tmp_path, quick=True, series=synthetic())
    assert summary["analysis_id"] == again["analysis_id"] and summary["paid_calls"] == 0
    scores = pd.read_csv(tmp_path / "results/inflation_scores.csv")
    assert set(scores.model) == {"RW", "AR", "Phillips", "LASSO", "BVAR", "Ensemble"}
    assert set(scores.target) == {"ea_headline", "ea_core", "tr_headline"}
    ns = pd.read_csv(tmp_path / "results/nowcast_scores.csv")
    assert set(ns.model) == {"Bridge", "UMIDAS", "DFM"}


def test_strict_parsers_and_private_loading(tmp_path):
    import json

    payload = {
        "id": ["freq", "geo", "time"],
        "dimension": {
            "freq": {"category": {"index": {"Q": 0}}},
            "geo": {"category": {"index": {"DE": 0}}},
            "time": {"category": {"index": {"2020-Q1": 0, "2020-Q2": 1}}},
        },
        "value": {"0": 100},
    }
    series = eurostat(json.dumps(payload).encode(), {"freq": "Q", "geo": "DE"})
    assert series.index.freqstr.startswith("Q") and pd.isna(series.iloc[1])
    with pytest.raises(ValueError):
        eurostat(json.dumps(payload).encode(), {"freq": "Q", "geo": "FR"})
    payload["id"] = ["time", "freq", "geo"]
    with pytest.raises(ValueError):
        eurostat(json.dumps(payload).encode(), {"freq": "Q", "geo": "DE"})
    payload = {"items": [{"Tarih": "2020-01", "TP_TIG08": "10"}], "totalCount": 1}
    assert evds(json.dumps(payload).encode(), "TP.TIG08").iloc[0] == 10
    payload["totalCount"] = 2
    with pytest.raises(ValueError):
        evds(json.dumps(payload).encode(), "TP.TIG08")
    p = tmp_path / "data/processed"
    p.mkdir(parents=True)
    for name, s in synthetic().items():
        s.to_csv(p / (name + ".csv"), header=[name])
    assert set(load(tmp_path)) == set(synthetic())


def test_dfm_future_invariance():
    from inflation_forecast_nowcast.pipeline import dfm_predict

    data = transform(synthetic())
    m = pd.concat(
        [data[k].rename(k) for k in ["ip", "retail", "unemployment", "esi"]], axis=1
    ).iloc[1:]
    q = data["de_gdp"].dropna()
    quarter = pd.Period("2005Q1", "Q")
    origin = pd.Period("2005-03", "M")
    first, meta = dfm_predict(m, q, origin, quarter, maxiter=5)
    altered = m.copy()
    altered.loc[altered.index > origin] = 1e5
    g = q.copy()
    g.loc[g.index >= quarter] = 1e5
    second, _ = dfm_predict(altered, g, origin, quarter, maxiter=5)
    assert first == pytest.approx(second) and meta["iterations"] <= 5
