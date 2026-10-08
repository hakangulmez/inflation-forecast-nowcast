"""Run official-source research or a fully isolated offline synthetic quick run."""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import argparse
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from inflation_forecast_nowcast.pipeline import run
from inflation_forecast_nowcast.yoy import run as run_yoy


def synthetic():
    rng = np.random.default_rng(20261007)
    index = pd.period_range("1999-01", "2026-09", freq="M")
    x = rng.normal(size=(len(index), 6))
    for i in range(1, len(x)):
        x[i] += 0.4 * x[i - 1]
    values = {
        name: pd.Series(100 * np.exp(np.cumsum(0.002 + 0.003 * x[:, j])), index=index)
        for j, name in enumerate(["ea_headline", "ea_core", "tr_headline", "ip", "retail"])
    }
    values["ea_unemployment"] = pd.Series(7 + x[:, 5], index=index)
    values["tr_unemployment"] = pd.Series(10 + x[:, 5], index=index)
    values["unemployment"] = pd.Series(5 + x[:, 5], index=index)
    values["esi"] = pd.Series(100 + 10 * x[:, 0], index=index)
    q = pd.period_range("1999Q1", "2026Q2", freq="Q")
    values["de_gdp"] = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.004, 0.01, len(q)))), index=q)
    return values


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    if args.quick:
        (root / ".cache").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="offline-", dir=root / ".cache") as d:
            result = run(Path(d), quick=True, series=synthetic())
            run_yoy(Path(d), raw=synthetic(), quick=True)
            print(
                json.dumps(
                    {
                        "synthetic": True,
                        "network_calls": 0,
                        "paid_calls": 0,
                        "seconds": result["elapsed_seconds"],
                    }
                )
            )
    else:
        print(json.dumps(run(root)))
