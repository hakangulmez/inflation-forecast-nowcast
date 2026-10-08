"""Benchmark accounting, future-data invariance and reproducible primary-target runs."""

import numpy as np
import pandas as pd

from inflation_forecast_nowcast.yoy import annual_targets, forecasts_at, run


def synthetic():
    index = pd.period_range("2000-01", "2016-12", freq="M")
    rng = np.random.default_rng(71)
    raw = {
        n: pd.Series(100 * np.exp(np.cumsum(rng.normal(0.003, 0.002, len(index)))), index=index)
        for n in ["ea_headline", "ea_core", "tr_headline"]
    }
    raw.update(
        {
            n: pd.Series(6 + rng.normal(size=len(index)), index=index)
            for n in ["ea_unemployment", "tr_unemployment"]
        }
    )
    return raw


def test_rw_and_ao_have_distinct_exact_accounting():
    prices = pd.Series(100 * 1.02 ** np.arange(30))
    annual, ao = annual_targets(prices)
    assert np.isclose(annual.iloc[-1], 100 * (1.02**12 - 1))
    assert np.isclose(ao.iloc[-1], 24)
    assert annual.iloc[:12].isna().all() and ao.iloc[:12].isna().all()


def test_future_information_does_not_change_forecasts():
    raw = synthetic()
    y, ao = annual_targets(raw["tr_headline"])
    frame = pd.concat([y.rename("tr_headline"), raw["tr_unemployment"]], axis=1).dropna()
    aoframe = ao.to_frame("tr_headline").reindex(frame.index)
    i = 150
    before = forecasts_at(frame, aoframe, i, [1, 3, 6, 12])
    frame.iloc[i + 1 :] = 9000
    aoframe.iloc[i + 1 :] = 9000
    assert before == forecasts_at(frame, aoframe, i, [1, 3, 6, 12])
    rw = [r for r in before if r["model"] == "RW"]
    a = [r for r in before if r["model"] == "AO"]
    assert all(r["forecast"] == frame.tr_headline.iloc[i] for r in rw)
    assert all(r["forecast"] == aoframe.tr_headline.iloc[i] for r in a)


def test_run_has_matched_dual_benchmarks_and_resumes(tmp_path):
    first = run(tmp_path, raw=synthetic(), quick=True)
    table = pd.read_csv(tmp_path / "results/inflation_scores_yoy.csv")
    assert set(table.benchmark) == {"RW", "AO"} and set(table.horizon) == {1, 3, 6, 12}
    assert table.n.eq(10).all() and table.dm_n.eq(10).all()
    assert first["forecast_rows"] == 840
    second = run(tmp_path, raw=synthetic(), quick=True)
    assert first["analysis_id"] == second["analysis_id"]
    pd.testing.assert_frame_equal(table, pd.read_csv(tmp_path / "results/inflation_scores_yoy.csv"))
