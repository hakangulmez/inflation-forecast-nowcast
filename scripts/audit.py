"""Audit public aggregate results without data acquisition or model fitting."""

import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

root = Path.cwd()
checks = []


def check(name, passed):
    checks.append({"check": name, "passed": bool(passed)})


contract = json.loads((root / "results/technical_model_contract.json").read_text())
for row in contract["source"]:
    check(
        row["path"], hashlib.sha256((root / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    )
scores = pd.read_csv(root / "results/inflation_scores_yoy.csv")
check("benchmarks", set(scores.benchmark) == {"RW", "AO"})
check("horizons", set(scores.horizon) == {1, 3, 6, 12})
check("common count", scores.n.eq(140).all())
check("seasonal mean", "SeasonalMean" in set(scores.model))
check("policy pages", len(PdfReader(root / "report/policy_note.pdf").pages) == 2)
check("technical page limit", len(PdfReader(root / "report/technical_report.pdf").pages) <= 15)
for filename in ["manifest.json", "yoy_manifest.json", "v3_inflation_manifest.json"]:
    record = json.loads((root / "results" / filename).read_text())
    check(filename + " zero paid calls", record["paid_calls"] == 0)
files = subprocess.check_output(["git", "ls-files"], cwd=root, text=True).splitlines()
check("allowlist", set(files) == set((root / "docs/PUBLIC_FILES.txt").read_text().splitlines()))
check(
    "no raw/env/private paths",
    not any(p.startswith(("data/", "runs/", ".venv/", ".cache/")) or p == ".env" for p in files),
)
remotes = subprocess.check_output(["git", "remote", "-v"], cwd=root, text=True)
check(
    "authorized remote only",
    all(
        "https://github.com/hakangulmez/inflation-forecast-nowcast.git" in line
        for line in remotes.splitlines()
    ),
)
result = {"checks": checks, "all_pass": all(c["passed"] for c in checks), "estimation": False}
folder = root / ".cache"
folder.mkdir(exist_ok=True)
(folder / "publication_audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
if not result["all_pass"]:
    raise SystemExit(1)
