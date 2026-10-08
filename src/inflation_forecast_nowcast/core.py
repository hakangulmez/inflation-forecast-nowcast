"""Forecast estimators and evaluation: every fit uses an origin-bounded sample."""

import numpy as np
from scipy.stats import t as student_t
from sklearn.linear_model import Lasso


def lag_matrix(y, p):
    y = np.asarray(y, dtype=float)
    if y.ndim == 1:
        y = y[:, None]
    if len(y) <= p:
        raise ValueError("Insufficient lag history")
    return np.column_stack(
        [np.ones(len(y) - p)] + [y[p - i : len(y) - i] for i in range(1, p + 1)]
    ), y[p:]


def ar_forecasts(y, horizon, maxlag=12):
    y = np.asarray(y, dtype=float)
    cap = min(maxlag, (len(y) - 12) // 3)
    candidates = []
    for p in range(1, cap + 1):
        x, target = lag_matrix(y, p)
        # Common candidate comparison window.
        x, target = x[cap - p :], target[cap - p :, 0]
        b = np.linalg.lstsq(x, target, rcond=None)[0]
        rss = max(float(np.sum((target - x @ b) ** 2)), 1e-12)
        candidates.append(
            (len(target) * np.log(rss / len(target)) + (p + 1) * np.log(len(target)), p)
        )
    p = min(candidates)[1]
    x, target = lag_matrix(y, p)
    b = np.linalg.lstsq(x, target[:, 0], rcond=None)[0]
    values = list(y)
    for _ in range(horizon):
        values.append(float(np.r_[1, values[-p:][::-1]] @ b))
    return np.asarray(values[-horizon:]), p


def bvar_forecasts(y, horizon, p=12, own=0.2, cross=0.1):
    """Independent normal-inverse-gamma equations; Minnesota posterior means."""
    y = np.asarray(y, dtype=float)
    x, target = lag_matrix(y, p)
    k = y.shape[1]
    # AR innovation variances use this training history only.
    scales = []
    for j in range(k):
        a = np.column_stack([np.ones(len(y) - 1), y[:-1, j]])
        e = y[1:, j] - a @ np.linalg.lstsq(a, y[1:, j], rcond=None)[0]
        scales.append(max(float(np.mean(e * e)), 1e-6))
    betas = []
    for j in range(k):
        # Conditional prior covariance sigma_j^2 V_j; own/cross and lag decay.
        variance = [1e6] + [
            ((own if predictor == j else cross) ** 2) / (lag**2 * scales[predictor])
            for lag in range(1, p + 1)
            for predictor in range(k)
        ]
        precision = np.diag(1 / np.asarray(variance))
        betas.append(np.linalg.solve(x.T @ x + precision, x.T @ target[:, j]))
    beta = np.column_stack(betas)
    values = list(y)
    for _ in range(horizon):
        reg = np.r_[1, np.asarray(values[-p:][::-1]).ravel()]
        values.append(reg @ beta)
    return np.asarray(values[-horizon:])


def direct_forecast(y, u, h, month, lasso=False):
    # Forecast y_(t+h) from lags/info at t; future unemployment never enters.
    y, u = np.asarray(y), np.asarray(u)
    p = 12
    times = np.arange(p - 1, len(y) - h)

    def design(t):
        season = np.eye(12)[(month[t] + h - 1) % 12][:11]
        return np.r_[y[t - p + 1 : t + 1][::-1], u[t], season]

    x = np.array([design(t) for t in times])
    target = y[times + h]
    valid = np.isfinite(x).all(axis=1) & np.isfinite(target)
    x, target = x[valid], target[valid]
    now = design(len(y) - 1)
    if not np.isfinite(now).all() or len(target) < 30:
        return np.nan
    if lasso:
        mean = x.mean(axis=0)
        scale = x.std(axis=0)
        scale[scale < 1e-8] = 1
        model = Lasso(alpha=0.05, max_iter=10000).fit((x - mean) / scale, target)
        return float(model.predict(((now - mean) / scale)[None, :])[0])
    # Parsimonious Phillips equation: inflation lag, unemployment, seasonality.
    cols = [0, 12] + list(range(13, x.shape[1]))
    xx = np.column_stack([np.ones(len(x)), x[:, cols]])
    b = np.linalg.lstsq(xx, target, rcond=None)[0]
    return float(np.r_[1, now[cols]] @ b)


def dm_hln(errors, benchmark, h, bandwidth=None):
    d = np.asarray(errors) ** 2 - np.asarray(benchmark) ** 2
    d = d[np.isfinite(d)]
    n = len(d)
    if n <= 2 * h or np.var(d) < 1e-15:
        return {"dm_hln": np.nan, "dm_pvalue": np.nan, "dm_n": n}
    centered = d - d.mean()
    variance = float(centered @ centered / n)
    bandwidth = h - 1 if bandwidth is None else bandwidth
    for lag in range(1, min(bandwidth, n - 1) + 1):
        variance += 2 * (1 - lag / (bandwidth + 1)) * float(centered[lag:] @ centered[:-lag] / n)
    if variance <= 0:
        return {"dm_hln": np.nan, "dm_pvalue": np.nan, "dm_n": n}
    correction = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    stat = float(d.mean() / np.sqrt(variance / n) * correction)
    return {"dm_hln": stat, "dm_pvalue": float(2 * student_t.sf(abs(stat), n - 1)), "dm_n": n}


def error_scores(e, benchmark, seed=20261007, draws=499, block=12):
    e, b = np.asarray(e), np.asarray(benchmark)
    valid = np.isfinite(e) & np.isfinite(b)
    e, b = e[valid], b[valid]
    if len(e) < 8:
        raise ValueError("Insufficient comparable errors")
    rmse = float(np.sqrt(np.mean(e * e)))
    mae = float(np.mean(abs(e)))
    ratio = rmse / np.sqrt(np.mean(b * b))
    maer = mae / np.mean(abs(b))
    rng = np.random.default_rng(seed)
    values = []
    rmse_values = []
    for _ in range(draws):
        starts = rng.integers(0, len(e), size=(len(e) + block - 1) // block)
        ix = np.concatenate([(s + np.arange(block)) % len(e) for s in starts])[: len(e)]
        values.append(np.sqrt(np.mean(e[ix] ** 2) / np.mean(b[ix] ** 2)))
        rmse_values.append(np.sqrt(np.mean(e[ix] ** 2)))
    lo, hi = np.quantile(values, [0.05, 0.95])
    return dict(
        n=len(e),
        rmse=rmse,
        mae=mae,
        relative_rmse=float(ratio),
        relative_mae=float(maer),
        lo90=float(lo),
        hi90=float(hi),
        rmse_lo90=float(np.quantile(rmse_values, 0.05)),
        rmse_hi90=float(np.quantile(rmse_values, 0.95)),
    )


def ragged(monthly, gdp, origin, quarter):
    m = monthly.loc[:origin].copy()
    for name in m:
        delay = 0 if name == "esi" else 2
        m.loc[m.index > origin - delay, name] = np.nan
    # Quarter's GDP always withheld; only previously released GDP may train.
    q = gdp.copy()
    for period in q.index:
        if period >= quarter or period.asfreq("M", "end") + 2 > origin:
            q.loc[period] = np.nan
    return m, q


def bridge_predict(monthly, gdp, origin, quarter, unrestricted=False):
    m, q = ragged(monthly, gdp, origin, quarter)
    rows = []
    targets = []
    position = (origin - quarter.asfreq("M", "start")).n

    def reg(period):
        start = period.asfreq("M", "start")
        cutoff = min(start + position, period.asfreq("M", "end"))
        # Apply the identical information pattern to every training quarter.
        local = m.loc[start:cutoff].copy()
        for name in local:
            delay = 0 if name == "esi" else 2
            local.loc[local.index > start + position - delay, name] = np.nan
        if unrestricted:
            # Three observed month slots; missing slots replaced by training design means.
            return local.reindex([start, start + 1, start + 2]).to_numpy().ravel()
        return local.mean().to_numpy()

    for period, value in q.dropna().items():
        if period < quarter:
            rows.append(reg(period))
            targets.append(value)
    x = np.asarray(rows)
    now = reg(quarter)
    count = np.isfinite(x).sum(axis=0)
    mean = np.divide(np.nansum(x, axis=0), count, out=np.zeros(x.shape[1]), where=count > 0)
    mean[~np.isfinite(mean)] = 0
    x = np.where(np.isfinite(x), x, mean)
    now = np.where(np.isfinite(now), now, mean)
    xx = np.column_stack([np.ones(len(x)), x])
    pen = np.eye(xx.shape[1]) * 0.01
    pen[0, 0] = 0
    b = np.linalg.solve(xx.T @ xx + pen, xx.T @ np.asarray(targets))
    return float(np.r_[1, now] @ b)
