import numpy as np
import pandas as pd
import pytest

from inflation_forecast_nowcast.core import dm_hln
from inflation_forecast_nowcast.v3 import forecasts_at, seasonal_path


def prices():
    index = pd.period_range("1998-01", "2026-12", freq="M")
    increments = 0.002 + 0.0001 * np.arange(len(index)) + 0.003 * np.sin(index.month)
    return pd.Series(100 * np.exp(np.cumsum(increments)), index=index)


def test_publication_mask_invariance_and_fixed_targets():
    price = prices()
    raw = {
        "ea_headline": price,
        "ea_core": price**0.8,
        "ea_unemployment": pd.Series(7 + np.sin(np.arange(len(price)) / 10), index=price.index),
    }
    origin = pd.Period("2015-09", "M")
    a = forecasts_at(raw, list(raw), origin)
    changed = {k: v.copy() for k, v in raw.items()}
    for k, s in changed.items():
        cutoff = origin - (2 if "unemployment" in k else 1)
        s.loc[s.index > cutoff] *= 10
    b = forecasts_at(changed, list(raw), origin)
    np.testing.assert_allclose(
        [r["forecast"] for r in a], [r["forecast"] for r in b], equal_nan=True
    )
    for row in a:
        assert pd.Period(row["date"], "M") == origin + row["horizon"]
        assert row["price_cutoff"] == "2015-08" and row["unemployment_cutoff"] == "2015-07"
        extra = 1 if row["model"] in ["RW", "AO", "AR", "SeasonalMean"] else 2
        assert row["forward_steps"] == row["horizon"] + extra


def test_seasonal_naive_rw_equivalence_extended_horizons():
    p = prices()
    for origin in [pd.Period("2015-01", "M"), pd.Period("2015-09", "M")]:
        latest = origin - 1
        rw = 100 * (p.loc[latest] / p.loc[latest - 12] - 1)
        for h in [1, 3, 6, 12, 13, 24, 30]:
            np.testing.assert_allclose(
                seasonal_path(p, origin, origin + h, rule="naive"), rw, rtol=1e-12
            )


def test_log_averaging_known_unknown_boundary_and_compounding():
    p = prices()
    origin = pd.Period("2015-09", "M")
    target = origin + 1
    observed = np.log(p.loc[: origin - 1]).diff().dropna()
    expected = []
    for t in pd.period_range(target - 11, target, freq="M"):
        expected.append(
            observed.loc[t]
            if t <= origin - 1
            else observed[observed.index.month == t.month].iloc[-3:].mean()
        )
    np.testing.assert_allclose(seasonal_path(p, origin, target), 100 * np.expm1(sum(expected)))
    # September reference observations are not published at September's origin.
    altered = p.copy()
    altered.loc[origin:] *= 100
    assert seasonal_path(p, origin, target) == seasonal_path(altered, origin, target)
    assert not np.isclose(
        seasonal_path(p, origin, target), seasonal_path(p, origin, target, "naive")
    )


def test_missing_three_eligible_observations_is_explicit():
    p = prices().loc["2013-01":]
    assert np.isnan(seasonal_path(p, pd.Period("2015-09", "M"), pd.Period("2015-10", "M")))


def test_hac_keeps_loss_and_hln_but_adds_fixed_dependence():
    rng = np.random.default_rng(12)
    e = rng.normal(size=100)
    b = rng.normal(size=100)
    old = dm_hln(e, b, 3)
    explicit = dm_hln(e, b, 3, bandwidth=2)
    assert old == explicit
    revised = dm_hln(e, b, 3, bandwidth=14)
    assert revised["dm_n"] == old["dm_n"] == 100
    assert revised["dm_pvalue"] != old["dm_pvalue"]


def test_fixed_same_month_history_is_not_replaced_by_prior_predictions():
    p = prices()
    origin = pd.Period("2015-09", "M")
    observed = np.log(p.loc[: origin - 1]).diff().dropna()
    for horizon in [1, 6, 13, 30]:
        target = origin + horizon
        changes = []
        for t in pd.period_range(target - 11, target, freq="M"):
            eligible = observed[observed.index.month == t.month]
            changes.append(observed.loc[t] if t <= origin - 1 else eligible.iloc[-3:].mean())
        assert seasonal_path(p, origin, target) == pytest.approx(100 * np.expm1(sum(changes)))


def test_naive_equivalence_with_various_effective_publication_cutoffs():
    p = prices()
    nominal = pd.Period("2015-01", "M")
    for delay in [0, 1, 2, 5]:
        # Shifting the routine's origin represents the same nominal target with
        # an arbitrary latest published month. The operational V3 delay stays1.
        effective_origin = nominal + 1 - delay
        cutoff = nominal - delay
        expected = 100 * (p.loc[cutoff] / p.loc[cutoff - 12] - 1)
        for h in [1, 12, 15, 30]:
            assert seasonal_path(p, effective_origin, nominal + h, "naive") == pytest.approx(
                expected
            )
