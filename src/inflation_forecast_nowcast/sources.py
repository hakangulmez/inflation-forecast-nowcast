"""Ten verified official series, strict selection, private response checksums."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from inflation_forecast_nowcast.access import Client, read_keys

SPECS = {
    "ea_headline": ("prc_hicp_minr", dict(freq="M", unit="I25", coicop18="TOTAL", geo="EA21")),
    "ea_core": ("prc_hicp_minr", dict(freq="M", unit="I25", coicop18="TOT_X_NRG_FOOD", geo="EA21")),
    "ea_unemployment": (
        "une_rt_m",
        dict(freq="M", s_adj="SA", age="TOTAL", unit="PC_ACT", sex="T", geo="EA21"),
    ),
    "de_gdp": (
        "namq_10_gdp",
        dict(freq="Q", unit="CLV_I20", s_adj="SCA", na_item="B1GQ", geo="DE"),
    ),
    "ip": (
        "sts_inpr_m",
        dict(freq="M", indic_bt="PRD", nace_r2="B-D", s_adj="SCA", unit="I21", geo="DE"),
    ),
    "retail": (
        "sts_trtu_m",
        dict(freq="M", indic_bt="VOL_SLS", nace_r2="G47", s_adj="SCA", unit="I21", geo="DE"),
    ),
    "unemployment": (
        "une_rt_m",
        dict(freq="M", s_adj="SA", age="TOTAL", unit="PC_ACT", sex="T", geo="DE"),
    ),
    "esi": ("ei_bssi_m_r2", dict(freq="M", s_adj="SA", indic="BS-ESI-I", geo="DE")),
}


def eurostat(payload, selectors):
    d = json.loads(payload)
    for name in d["id"]:
        if name != "time" and set(d["dimension"][name]["category"]["index"]) != {selectors[name]}:
            raise ValueError("Selector mismatch")
    if d["id"][-1] != "time":
        raise ValueError("Unsupported layout")
    dates = d["dimension"]["time"]["category"]["index"]
    values = d["value"]
    index = pd.PeriodIndex(dates.keys(), freq=selectors["freq"])
    return pd.Series(
        [values.get(str(i)) if isinstance(values, dict) else values[i] for i in dates.values()],
        index=index,
        dtype=float,
    ).sort_index()


def evds(payload, name):
    d = json.loads(payload)
    rows = d["items"]
    if int(d.get("totalCount", len(rows))) != len(rows):
        raise ValueError("Truncated EVDS response")
    col = name.replace(".", "_")
    return (
        pd.Series(
            [r[col] for r in rows], index=pd.PeriodIndex([r["Tarih"] for r in rows], freq="M")
        )
        .apply(pd.to_numeric, errors="coerce")
        .sort_index()
    )


def acquire(root: Path):
    client = Client(root)
    series = {}
    for name, (dataset, selectors) in SPECS.items():
        payload = client.get(
            name,
            "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/" + dataset,
            dict(
                lang="en",
                **selectors,
                sinceTimePeriod="1999-Q1" if selectors["freq"] == "Q" else "1999-01",
                untilTimePeriod="2026-Q2" if selectors["freq"] == "Q" else "2026-09",
            ),
        )
        series[name] = eurostat(payload, selectors)
    keys = read_keys(root / ".env")
    if "EVDS_API_KEY" not in keys:
        raise ValueError("Missing EVDS_API_KEY; values not printed")
    for name, identifier in [
        ("tr_headline", "TP.TUKFIY2025.GENEL"),
        ("tr_unemployment", "TP.TIG08"),
    ]:
        url = (
            "https://evds3.tcmb.gov.tr/igmevdsms-dis/series="
            + identifier
            + "&startDate=01-01-1999&endDate=30-09-2026&type=json"
        )
        series[name] = evds(
            client.get(name, url, headers={"key": keys["EVDS_API_KEY"]}), identifier
        )
    target = root / "data/processed"
    target.mkdir(parents=True, exist_ok=True)
    for name, s in series.items():
        s.to_csv(target / (name + ".csv"), header=[name])
    summary: dict = {
        k: dict(
            first=str(v.first_valid_index()),
            last=str(v.last_valid_index()),
            n=int(v.count()),
            missing=[str(i) for i in v.index[v.isna()]],
        )
        for k, v in series.items()
    }
    summary["sources"] = client.records
    (root / "results").mkdir(exist_ok=True)
    (root / "results/data_inventory.json").write_text(json.dumps(summary, indent=2))
    return series


def load(root):
    target = root / "data/processed"
    if not all(
        (target / (n + ".csv")).exists() for n in list(SPECS) + ["tr_headline", "tr_unemployment"]
    ):
        return acquire(root)
    values = {}
    for p in target.glob("*.csv"):
        s = pd.read_csv(p, index_col=0).iloc[:, 0]
        s.index = pd.PeriodIndex(s.index, freq="Q" if p.stem == "de_gdp" else "M")
        values[p.stem] = s
    return values


def transform(series):
    result = {}
    for name, s in series.items():
        s = s.reindex(pd.period_range(s.index.min(), s.index.max(), freq=s.index.freqstr))
        result[name] = (
            100 * np.log(s).diff()
            if name in ["ea_headline", "ea_core", "tr_headline", "de_gdp", "ip", "retail"]
            else (s.diff() if name == "unemployment" else s)
        )
    return result
